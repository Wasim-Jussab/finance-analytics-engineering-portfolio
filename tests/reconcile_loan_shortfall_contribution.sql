with contributions as (
    select snapshot_date,
        sum(scheduled_principal_shortfall_amount) as current_shortfall,
        sum(previous_scheduled_principal_shortfall_amount) as previous_shortfall,
        sum(scheduled_principal_shortfall_change) as change_amount
    from {{ ref('rpt_loan_monthly_shortfall_contribution') }}
    group by snapshot_date
)
select coalesce(c.snapshot_date, r.snapshot_date) as snapshot_date
from contributions as c
full outer join {{ ref('rpt_loan_portfolio_monthly_change') }} as r
    on c.snapshot_date = r.snapshot_date
left join {{ ref('agg_loan_portfolio_total_monthly') }} as previous
    on r.previous_snapshot_date = previous.snapshot_date
where c.snapshot_date is null or r.snapshot_date is null
    or c.current_shortfall is distinct from r.scheduled_principal_shortfall_amount
    or c.previous_shortfall is distinct from previous.scheduled_principal_shortfall_amount
    or c.change_amount is distinct from r.scheduled_principal_shortfall_change
