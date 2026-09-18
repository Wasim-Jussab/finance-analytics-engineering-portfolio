with expected_removals as (
    select subscription_id
    from {{ ref('subscription_agreement_history') }}
    group by subscription_id
    having sum(case when dbt_valid_to is null then 1 else 0 end) = 0
),

actual_removals as (
    select subscription_id
    from {{ ref('fct_subscription_source_removal') }}
)

select
    coalesce(expected.subscription_id, actual.subscription_id) as subscription_id
from expected_removals as expected
full outer join actual_removals as actual
    on expected.subscription_id = actual.subscription_id
where
    expected.subscription_id is null
    or actual.subscription_id is null
