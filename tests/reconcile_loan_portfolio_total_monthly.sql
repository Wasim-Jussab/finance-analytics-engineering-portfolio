with expected_accounts as (
    select snapshot_date, count(distinct account_id) as account_count
    from {{ ref('fct_loan_monthly_snapshot') }}
    group by snapshot_date
),
product_positions as (
    select
        snapshot_date,
        sum(scheduled_principal_due_amount) as due,
        sum(assumed_allocated_completed_payment_amount) as allocated,
        sum(scheduled_principal_shortfall_amount) as shortfall
    from {{ ref('agg_loan_portfolio_monthly') }}
    group by snapshot_date
)
select coalesce(t.snapshot_date, a.snapshot_date, p.snapshot_date) as snapshot_date
from {{ ref('agg_loan_portfolio_total_monthly') }} as t
full outer join expected_accounts as a on t.snapshot_date = a.snapshot_date
full outer join product_positions as p on coalesce(t.snapshot_date, a.snapshot_date) = p.snapshot_date
where t.snapshot_date is null or a.snapshot_date is null or p.snapshot_date is null
    or t.loan_account_count is distinct from a.account_count
    or t.scheduled_principal_due_amount is distinct from p.due
    or t.assumed_allocated_completed_payment_amount is distinct from p.allocated
    or t.scheduled_principal_shortfall_amount is distinct from p.shortfall
    or p.due <> p.allocated + p.shortfall
    or t.due_principal_coverage_ratio is distinct from
        round(p.allocated / nullif(p.due, 0), 4)
