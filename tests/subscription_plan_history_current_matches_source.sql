with current_history as (
    select
        subscription_plan_id,
        product_code,
        billing_frequency,
        billing_amount
    from {{ ref('subscription_plan_history') }}
    where dbt_valid_to is null
),

current_source as (
    select
        subscription_plan_id,
        product_code,
        billing_frequency,
        billing_amount
    from {{ source('raw', 'subscription_plans') }}
)

select
    coalesce(history.subscription_plan_id, source.subscription_plan_id) as subscription_plan_id
from current_history as history
full outer join current_source as source
    on history.subscription_plan_id = source.subscription_plan_id
where
    history.subscription_plan_id is null
    or source.subscription_plan_id is null
    or history.product_code is distinct from source.product_code
    or history.billing_frequency is distinct from source.billing_frequency
    or history.billing_amount is distinct from source.billing_amount
