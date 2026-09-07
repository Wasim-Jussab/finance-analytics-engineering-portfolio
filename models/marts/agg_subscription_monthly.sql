with reporting_months as (
    select
        calendar_date as billing_month,
        month_end_date
    from {{ ref('dim_date') }}
    where calendar_date = month_start_date
),
eligible_plan_months as (
    select
        month.billing_month,
        subscription.subscription_plan_id,
        count(distinct subscription.subscription_id) as active_agreement_count
    from reporting_months as month
    inner join {{ ref('dim_subscription') }} as subscription
        on month.month_end_date >= subscription.start_date
        and month.billing_month <= date_trunc(
            'month',
            coalesce(
                subscription.cancellation_date,
                (select max(calendar_date) from {{ ref('dim_date') }})
            )
        )
    group by month.billing_month, subscription.subscription_plan_id
),
monthly_metrics as (
    select
        payment.billing_month,
        subscription.subscription_plan_id,
        count(*) as payment_attempt_count,
        count(*) filter (where payment.is_collected) as completed_payment_count,
        count(*) filter (where not payment.is_collected) as failed_payment_count,
        sum(payment.amount) as attempted_amount,
        sum(case when payment.is_collected then payment.amount else 0 end) as collected_amount
    from {{ ref('fct_subscription_payment') }} as payment
    inner join {{ ref('dim_subscription') }} as subscription using (subscription_id)
    group by payment.billing_month, subscription.subscription_plan_id
),
zero_filled as (
    select
        eligible.billing_month,
        eligible.subscription_plan_id,
        eligible.active_agreement_count,
        coalesce(metrics.payment_attempt_count, 0) as payment_attempt_count,
        coalesce(metrics.completed_payment_count, 0) as completed_payment_count,
        coalesce(metrics.failed_payment_count, 0) as failed_payment_count,
        coalesce(metrics.attempted_amount, 0) as attempted_amount,
        coalesce(metrics.collected_amount, 0) as collected_amount
    from eligible_plan_months as eligible
    left join monthly_metrics as metrics
        on eligible.billing_month = metrics.billing_month
        and eligible.subscription_plan_id = metrics.subscription_plan_id
)
select
    zero_filled.billing_month,
    plan.product_code,
    plan.billing_frequency,
    zero_filled.active_agreement_count,
    zero_filled.payment_attempt_count,
    zero_filled.completed_payment_count,
    zero_filled.failed_payment_count,
    zero_filled.attempted_amount,
    zero_filled.collected_amount,
    case
        when zero_filled.payment_attempt_count = 0 then 0.0
        else round(
            zero_filled.completed_payment_count * 1.0
                / zero_filled.payment_attempt_count,
            4
        )
    end as collection_rate
from zero_filled
inner join {{ ref('dim_subscription_plan') }} as plan using (subscription_plan_id)
