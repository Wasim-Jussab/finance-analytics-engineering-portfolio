with versioned_history as (
    select
        dbt_scd_id as status_change_id,
        status,
        lag(status) over (
            partition by subscription_id
            order by dbt_valid_from
        ) as previous_status
    from {{ ref('subscription_agreement_history') }}
),

expected_changes as (
    select status_change_id
    from versioned_history
    where
        previous_status is not null
        and previous_status is distinct from status
),

actual_changes as (
    select status_change_id
    from {{ ref('fct_subscription_status_change') }}
)

select
    coalesce(expected.status_change_id, actual.status_change_id) as status_change_id
from expected_changes as expected
full outer join actual_changes as actual
    on expected.status_change_id = actual.status_change_id
where
    expected.status_change_id is null
    or actual.status_change_id is null
