select source_name, source_file, source_file_size_bytes, source_file_sha256
from {{ source('raw', 'ingestion_audit') }}
where (
        source_name = 'run_parameters'
        and (
            source_file is not null
            or source_file_size_bytes is not null
            or source_file_sha256 is not null
        )
    )
    or (
        source_name <> 'run_parameters'
        and (
            source_file is null
            or source_file_size_bytes is null
            or source_file_size_bytes <= 0
            or source_file_sha256 is null
            or not regexp_full_match(source_file_sha256, '[0-9a-f]{64}')
        )
    )
