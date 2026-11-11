select
    current_position.snapshot_date,
    previous_position.snapshot_date as previous_snapshot_date,
    previous_position.snapshot_date is not null as has_previous_month,
    current_position.loan_account_count,
    current_position.loan_account_count - previous_position.loan_account_count
        as loan_account_count_change,
    current_position.scheduled_principal_due_amount,
    current_position.scheduled_principal_due_amount
        - previous_position.scheduled_principal_due_amount as scheduled_principal_due_change,
    current_position.assumed_allocated_completed_payment_amount,
    current_position.assumed_allocated_completed_payment_amount
        - previous_position.assumed_allocated_completed_payment_amount
        as assumed_allocated_completed_payment_change,
    current_position.scheduled_principal_shortfall_amount,
    current_position.scheduled_principal_shortfall_amount
        - previous_position.scheduled_principal_shortfall_amount as scheduled_principal_shortfall_change
from {{ ref('agg_loan_portfolio_total_monthly') }} as current_position
left join {{ ref('agg_loan_portfolio_total_monthly') }} as previous_position
    on previous_position.snapshot_date
        = date_trunc('month', current_position.snapshot_date) - interval '1 day'
