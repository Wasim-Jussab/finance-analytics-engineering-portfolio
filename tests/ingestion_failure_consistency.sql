select
    coalesce(runs.load_id, failures.load_id) as load_id,
    runs.run_status,
    failures.error_type,
    failures.error_message
from {{ source('audit', 'ingestion_runs') }} as runs
full outer join {{ source('audit', 'ingestion_failures') }} as failures using (load_id)
where runs.load_id is null
    or (runs.run_status = 'Failed' and failures.load_id is null)
    or (runs.run_status = 'Success' and failures.load_id is not null)
    or (failures.failed_at < runs.loaded_at)
    or trim(failures.error_type) = ''
    or trim(failures.error_message) = ''
