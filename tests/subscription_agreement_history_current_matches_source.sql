with current_history as (
    select
        subscription_id,
        customer_id,
        product_code,
        subscription_plan_id,
        start_date,
        cancellation_date,
        billing_frequency,
        status
    from {{ ref('subscription_agreement_history') }}
    where dbt_valid_to is null
),

current_source as (
    select
        subscription_id,
        customer_id,
        product_code,
        subscription_plan_id,
        start_date,
        cancellation_date,
        billing_frequency,
        status
    from {{ source('raw', 'subscriptions') }}
)

select
    coalesce(history.subscription_id, source.subscription_id) as subscription_id
from current_history as history
full outer join current_source as source
    on history.subscription_id = source.subscription_id
where
    history.subscription_id is null
    or source.subscription_id is null
    or history.customer_id is distinct from source.customer_id
    or history.product_code is distinct from source.product_code
    or history.subscription_plan_id is distinct from source.subscription_plan_id
    or history.start_date is distinct from source.start_date
    or history.cancellation_date is distinct from source.cancellation_date
    or history.billing_frequency is distinct from source.billing_frequency
    or history.status is distinct from source.status
