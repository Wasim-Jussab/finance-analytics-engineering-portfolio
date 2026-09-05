with fact_totals as (
    select
        count(*) as payment_attempt_count,
        count(*) filter (where is_collected) as completed_payment_count,
        count(*) filter (where not is_collected) as failed_payment_count,
        sum(amount) as attempted_amount,
        sum(case when is_collected then amount else 0 end) as collected_amount
    from {{ ref('fct_subscription_payment') }}
),
monthly_totals as (
    select
        sum(payment_attempt_count) as payment_attempt_count,
        sum(completed_payment_count) as completed_payment_count,
        sum(failed_payment_count) as failed_payment_count,
        sum(attempted_amount) as attempted_amount,
        sum(collected_amount) as collected_amount
    from {{ ref('agg_subscription_monthly') }}
)
select
    fact.payment_attempt_count as fact_payment_attempt_count,
    monthly.payment_attempt_count as monthly_payment_attempt_count,
    fact.completed_payment_count as fact_completed_payment_count,
    monthly.completed_payment_count as monthly_completed_payment_count,
    fact.failed_payment_count as fact_failed_payment_count,
    monthly.failed_payment_count as monthly_failed_payment_count,
    fact.attempted_amount as fact_attempted_amount,
    monthly.attempted_amount as monthly_attempted_amount,
    fact.collected_amount as fact_collected_amount,
    monthly.collected_amount as monthly_collected_amount
from fact_totals as fact
cross join monthly_totals as monthly
where fact.payment_attempt_count <> monthly.payment_attempt_count
    or fact.completed_payment_count <> monthly.completed_payment_count
    or fact.failed_payment_count <> monthly.failed_payment_count
    or fact.attempted_amount <> monthly.attempted_amount
    or fact.collected_amount <> monthly.collected_amount
