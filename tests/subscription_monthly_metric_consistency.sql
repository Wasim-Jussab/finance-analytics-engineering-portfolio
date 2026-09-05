select
    billing_month,
    product_code,
    billing_frequency,
    payment_attempt_count,
    completed_payment_count,
    failed_payment_count,
    attempted_amount,
    collected_amount,
    collection_rate
from {{ ref('agg_subscription_monthly') }}
where payment_attempt_count <> completed_payment_count + failed_payment_count
    or payment_attempt_count <= 0
    or attempted_amount <= 0
    or collected_amount < 0
    or collected_amount > attempted_amount
    or collection_rate < 0
    or collection_rate > 1
