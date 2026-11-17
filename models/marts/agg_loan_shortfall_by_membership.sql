select
    snapshot_date,
    previous_snapshot_date,
    has_previous_month,
    position_state,
    count(*) as contribution_account_count,
    sum(scheduled_principal_shortfall_amount) as scheduled_principal_shortfall_amount,
    sum(previous_scheduled_principal_shortfall_amount)
        as previous_scheduled_principal_shortfall_amount,
    sum(scheduled_principal_shortfall_change) as scheduled_principal_shortfall_change,
    case when has_previous_month then sum(
        case when scheduled_principal_shortfall_change > 0
            then scheduled_principal_shortfall_change else 0.00 end
    ) end as gross_shortfall_increase_amount,
    case when has_previous_month then sum(
        case when scheduled_principal_shortfall_change < 0
            then -scheduled_principal_shortfall_change else 0.00 end
    ) end as gross_shortfall_decrease_amount
from {{ ref('rpt_loan_monthly_shortfall_contribution') }}
group by snapshot_date, previous_snapshot_date, has_previous_month, position_state
