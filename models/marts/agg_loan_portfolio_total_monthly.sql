with monthly_totals as (
    select
        snapshot_date,
        sum(loan_account_count) as loan_account_count,
        sum(scheduled_principal_due_amount) as scheduled_principal_due_amount,
        sum(assumed_allocated_completed_payment_amount)
            as assumed_allocated_completed_payment_amount,
        sum(scheduled_principal_shortfall_amount) as scheduled_principal_shortfall_amount
    from {{ ref('agg_loan_portfolio_monthly') }}
    group by snapshot_date
)
select
    *,
    round(
        assumed_allocated_completed_payment_amount / nullif(scheduled_principal_due_amount, 0),
        4
    ) as due_principal_coverage_ratio
from monthly_totals
