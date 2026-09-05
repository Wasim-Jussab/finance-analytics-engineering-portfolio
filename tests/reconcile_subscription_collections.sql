with collection_totals as (
    select
        (
            select coalesce(sum(amount), 0)
            from {{ source('raw', 'subscription_payments') }}
            where payment_status = 'Completed'
        ) as raw_total,
        (
            select coalesce(sum(amount), 0)
            from {{ ref('fct_subscription_payment') }}
            where is_collected
        ) as fact_total
)
select
    raw_total,
    fact_total
from collection_totals
where raw_total <> fact_total
