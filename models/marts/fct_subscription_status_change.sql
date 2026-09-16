with agreement_versions as (
    select
        dbt_scd_id as status_change_id,
        subscription_id,
        customer_id,
        subscription_plan_id,
        start_date,
        cancellation_date,
        status as new_status,
        dbt_valid_from as observed_at,
        lag(status) over (
            partition by subscription_id
            order by dbt_valid_from
        ) as previous_status
    from {{ ref('subscription_agreement_history') }}
),

status_changes as (
    select
        status_change_id,
        subscription_id,
        customer_id,
        subscription_plan_id,
        start_date,
        previous_status,
        new_status,
        cancellation_date as business_event_date,
        observed_at,
        case
            when cancellation_date is not null
                then date_diff('day', cancellation_date, cast(observed_at as date))
        end as observation_delay_days
    from agreement_versions
    where
        previous_status is not null
        and previous_status is distinct from new_status
)

select *
from status_changes
