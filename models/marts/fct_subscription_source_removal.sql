with ranked_versions as (
    select
        dbt_scd_id as removal_id,
        subscription_id,
        customer_id,
        subscription_plan_id,
        status as last_observed_status,
        cancellation_date as last_observed_cancellation_date,
        dbt_valid_from as last_observed_at,
        dbt_valid_to as removed_at,
        row_number() over (
            partition by subscription_id
            order by dbt_valid_from desc
        ) as version_rank
    from {{ ref('subscription_agreement_history') }}
)

select
    removal_id,
    subscription_id,
    customer_id,
    subscription_plan_id,
    last_observed_status,
    last_observed_cancellation_date,
    last_observed_at,
    removed_at,
    last_observed_status = 'Cancelled' as was_cancelled_before_removal
from ranked_versions
where
    version_rank = 1
    and removed_at is not null
