with account_position as (
    select * from {{ ref('fct_loan_monthly_schedule_position') }}
)
select
    snapshot_date,
    product_code,
    count(*) as loan_account_count,
    sum(original_balance) as original_balance_amount,
    sum(cumulative_completed_payment_amount)
        as completed_payment_amount_as_of_month_end,
    sum(scheduled_principal_due_amount) as scheduled_principal_due_amount,
    sum(assumed_allocated_completed_payment_amount)
        as assumed_allocated_completed_payment_amount,
    sum(scheduled_principal_shortfall_amount)
        as scheduled_principal_shortfall_amount,
    sum(future_scheduled_principal_amount) as future_scheduled_principal_amount,
    sum(unallocated_completed_payment_amount)
        as unallocated_completed_payment_amount,
    count(*) filter (
        where scheduled_principal_due_amount = 0.00
    ) as not_yet_due_account_count,
    count(*) filter (
        where scheduled_principal_due_amount > 0.00
            and scheduled_principal_shortfall_amount = 0.00
    ) as on_schedule_account_count,
    count(*) filter (
        where scheduled_principal_shortfall_amount > 0.00
    ) as behind_schedule_account_count,
    case
        when sum(scheduled_principal_due_amount) = 0.00 then null
        else round(
            sum(assumed_allocated_completed_payment_amount)
            / sum(scheduled_principal_due_amount),
            4
        )
    end as due_principal_coverage_ratio
from account_position
group by snapshot_date, product_code
