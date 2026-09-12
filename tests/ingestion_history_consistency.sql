with source_summary as (
    select
        load_id,
        count(*) as source_count,
        sum(source_row_count) as total_source_row_count,
        count(distinct loaded_at) as loaded_at_count,
        min(loaded_at) as loaded_at
    from {{ source('audit', 'ingestion_sources') }}
    group by load_id
)
select
    runs.load_id,
    runs.source_count as recorded_source_count,
    summary.source_count as actual_source_count,
    runs.total_source_row_count as recorded_row_count,
    summary.total_source_row_count as actual_row_count
from {{ source('audit', 'ingestion_runs') }} as runs
left join source_summary as summary using (load_id)
where (
        runs.run_status = 'Success'
        and (
            summary.load_id is null
            or runs.source_count <> summary.source_count
            or runs.total_source_row_count <> summary.total_source_row_count
            or summary.loaded_at_count <> 1
            or runs.loaded_at <> summary.loaded_at
            or runs.source_count <> 7
        )
    )
    or (
        runs.run_status = 'Failed'
        and (
            summary.load_id is not null
            or runs.source_count <> 0
            or runs.total_source_row_count <> 0
        )
    )
