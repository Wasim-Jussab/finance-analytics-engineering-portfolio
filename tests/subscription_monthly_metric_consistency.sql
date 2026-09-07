select
    billing_month,
    product_code,
    billing_frequency,
    active_agreement_count,
    payment_attempt_count,
    completed_payment_count,
    failed_payment_count,
    attempted_amount,
    collected_amount,
    collection_rate
from {{ ref('agg_subscription_monthly') }}
where payment_attempt_count <> completed_payment_count + failed_payment_count
    or active_agreement_count <= 0
    or payment_attempt_count < 0
    or attempted_amount < 0
    or collected_amount < 0
    or collected_amount > attempted_amount
    or collection_rate < 0
    or collection_rate > 1
    or (
        payment_attempt_count = 0
        and (
            completed_payment_count <> 0
            or failed_payment_count <> 0
            or attempted_amount <> 0
            or collected_amount <> 0
            or collection_rate <> 0
        )
    )
    or (payment_attempt_count > 0 and attempted_amount <= 0)
    or (
        payment_attempt_count > 0
        and collection_rate <> round(
            completed_payment_count * 1.0 / payment_attempt_count,
            4
        )
    )
