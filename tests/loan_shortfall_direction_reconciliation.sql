select a.snapshot_date, a.position_state
from {{ ref('agg_loan_shortfall_by_membership') }} as a
where a.has_previous_month and (
    a.increasing_account_count is distinct from (
        select count(*) from {{ ref('rpt_loan_monthly_shortfall_contribution') }} as c
        where c.snapshot_date = a.snapshot_date and c.position_state = a.position_state
            and c.scheduled_principal_shortfall_change > 0
    )
    or a.decreasing_account_count is distinct from (
        select count(*) from {{ ref('rpt_loan_monthly_shortfall_contribution') }} as c
        where c.snapshot_date = a.snapshot_date and c.position_state = a.position_state
            and c.scheduled_principal_shortfall_change < 0
    )
    or a.unchanged_account_count is distinct from (
        select count(*) from {{ ref('rpt_loan_monthly_shortfall_contribution') }} as c
        where c.snapshot_date = a.snapshot_date and c.position_state = a.position_state
            and c.scheduled_principal_shortfall_change = 0
    )
)
