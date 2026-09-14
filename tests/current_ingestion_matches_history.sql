with current_load as (
    select distinct load_id
    from {{ source('raw', 'ingestion_audit') }}
),
current_history as (
    select history.*
    from {{ source('audit', 'ingestion_sources') }} as history
    inner join current_load using (load_id)
)
select
    coalesce(current_batch.source_name, history.source_name) as source_name,
    current_batch.load_id as current_load_id,
    history.load_id as history_load_id
from {{ source('raw', 'ingestion_audit') }} as current_batch
full outer join current_history as history
    on current_batch.load_id = history.load_id
    and current_batch.source_name = history.source_name
where current_batch.source_name is null
    or history.source_name is null
    or current_batch.source_file is distinct from history.source_file
    or current_batch.source_row_count <> history.source_row_count
    or current_batch.source_file_size_bytes is distinct from history.source_file_size_bytes
    or current_batch.source_file_sha256 is distinct from history.source_file_sha256
    or current_batch.load_status <> history.load_status
    or current_batch.loaded_at <> history.loaded_at
