with actual_counts as (
    select
        'subscription_plans' as source_name,
        count(*) as source_row_count,
        count(distinct load_id) as load_id_count,
        min(load_id) as load_id
    from {{ source('raw', 'subscription_plans') }}
    union all
    select 'customers', count(*), count(distinct load_id), min(load_id)
    from {{ source('raw', 'customers') }}
    union all
    select 'loans', count(*), count(distinct load_id), min(load_id)
    from {{ source('raw', 'loans') }}
    union all
    select 'subscriptions', count(*), count(distinct load_id), min(load_id)
    from {{ source('raw', 'subscriptions') }}
    union all
    select 'subscription_payments', count(*), count(distinct load_id), min(load_id)
    from {{ source('raw', 'subscription_payments') }}
    union all
    select 'payments', count(*), count(distinct load_id), min(load_id)
    from {{ source('raw', 'payments') }}
    union all
    select 'run_parameters', count(*), count(distinct load_id), min(load_id)
    from {{ source('raw', 'run_parameters') }}
),
audited_counts as (
    select load_id, source_name, source_row_count, load_status
    from {{ source('raw', 'ingestion_audit') }}
)
select
    coalesce(actual.source_name, audit.source_name) as source_name,
    actual.source_row_count as actual_row_count,
    audit.source_row_count as audited_row_count,
    actual.load_id_count,
    actual.load_id as actual_load_id,
    audit.load_id as audited_load_id,
    audit.load_status
from actual_counts as actual
full outer join audited_counts as audit using (source_name)
where actual.source_name is null
    or audit.source_name is null
    or actual.source_row_count <> audit.source_row_count
    or actual.load_id_count <> 1
    or actual.load_id <> audit.load_id
    or audit.load_status <> 'Loaded'
