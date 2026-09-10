with actual_counts as (
    select 'subscription_plans' as source_name, count(*) as source_row_count
    from {{ source('raw', 'subscription_plans') }}
    union all
    select 'customers', count(*) from {{ source('raw', 'customers') }}
    union all
    select 'loans', count(*) from {{ source('raw', 'loans') }}
    union all
    select 'subscriptions', count(*) from {{ source('raw', 'subscriptions') }}
    union all
    select 'subscription_payments', count(*)
    from {{ source('raw', 'subscription_payments') }}
    union all
    select 'payments', count(*) from {{ source('raw', 'payments') }}
    union all
    select 'run_parameters', count(*) from {{ source('raw', 'run_parameters') }}
),
audited_counts as (
    select source_name, source_row_count, load_status
    from {{ source('raw', 'ingestion_audit') }}
)
select
    coalesce(actual.source_name, audit.source_name) as source_name,
    actual.source_row_count as actual_row_count,
    audit.source_row_count as audited_row_count,
    audit.load_status
from actual_counts as actual
full outer join audited_counts as audit using (source_name)
where actual.source_name is null
    or audit.source_name is null
    or actual.source_row_count <> audit.source_row_count
    or audit.load_status <> 'Loaded'
