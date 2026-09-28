select *
from {{ ref('agg_loan_portfolio_monthly') }}
where loan_account_count <= 0
    or original_balance_amount <= 0.00
    or completed_payment_amount_as_of_month_end < 0.00
    or scheduled_principal_due_amount < 0.00
    or assumed_allocated_completed_payment_amount < 0.00
    or scheduled_principal_shortfall_amount < 0.00
    or future_scheduled_principal_amount < 0.00
    or unallocated_completed_payment_amount < 0.00
    or not_yet_due_account_count < 0
    or on_schedule_account_count < 0
    or behind_schedule_account_count < 0
    or loan_account_count
        <> not_yet_due_account_count
            + on_schedule_account_count
            + behind_schedule_account_count
    or scheduled_principal_due_amount
        <> assumed_allocated_completed_payment_amount
            + scheduled_principal_shortfall_amount
    or original_balance_amount
        <> scheduled_principal_due_amount + future_scheduled_principal_amount
    or completed_payment_amount_as_of_month_end
        <> assumed_allocated_completed_payment_amount
            + unallocated_completed_payment_amount
    or due_principal_coverage_ratio is distinct from case
        when scheduled_principal_due_amount = 0.00 then null
        else round(
            assumed_allocated_completed_payment_amount
            / scheduled_principal_due_amount,
            4
        )
    end
