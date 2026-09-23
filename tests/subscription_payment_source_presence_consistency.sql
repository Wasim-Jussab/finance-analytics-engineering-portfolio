with current_source as (
    select
        subscription_payment_id,
        subscription_id,
        billing_date,
        amount,
        payment_status,
        loaded_at
    from {{ source('raw', 'subscription_payments') }}
),

current_fact as (
    select
        subscription_payment_id,
        subscription_id,
        billing_date,
        amount,
        payment_status,
        source_loaded_at
    from {{ ref('fct_subscription_payment') }}
    where is_source_present
),

source_disagreement as (
    select
        coalesce(source.subscription_payment_id, fact.subscription_payment_id)
            as subscription_payment_id
    from current_source as source
    full outer join current_fact as fact using (subscription_payment_id)
    where
        source.subscription_payment_id is null
        or fact.subscription_payment_id is null
        or source.subscription_id is distinct from fact.subscription_id
        or source.billing_date is distinct from fact.billing_date
        or source.amount is distinct from fact.amount
        or source.payment_status is distinct from fact.payment_status
        or source.loaded_at is distinct from fact.source_loaded_at
),

invalid_presence_metadata as (
    select subscription_payment_id
    from {{ ref('fct_subscription_payment') }}
    where
        (is_source_present and source_missing_since is not null)
        or (not is_source_present and source_missing_since is null)
)

select subscription_payment_id from source_disagreement
union all
select subscription_payment_id from invalid_presence_metadata
