with billing_attempts as (
    select
        payment.billing_month,
        subscription.product_code,
        subscription.billing_frequency,
        payment.amount,
        payment.is_collected
    from {{ ref('fct_subscription_payment') }} as payment
    inner join {{ ref('dim_subscription') }} as subscription using (subscription_id)
),
monthly_metrics as (
    select
        billing_month,
        product_code,
        billing_frequency,
        count(*) as payment_attempt_count,
        count(*) filter (where is_collected) as completed_payment_count,
        count(*) filter (where not is_collected) as failed_payment_count,
        sum(amount) as attempted_amount,
        sum(case when is_collected then amount else 0 end) as collected_amount
    from billing_attempts
    group by billing_month, product_code, billing_frequency
)
select
    billing_month,
    product_code,
    billing_frequency,
    payment_attempt_count,
    completed_payment_count,
    failed_payment_count,
    attempted_amount,
    collected_amount,
    round(
        completed_payment_count * 1.0 / nullif(payment_attempt_count, 0),
        4
    ) as collection_rate
from monthly_metrics
