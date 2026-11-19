with account_month as (
    select
        snapshot.account_id,
        snapshot.product_code,
        snapshot.snapshot_date,
        snapshot.original_balance,
        snapshot.cumulative_completed_payment_amount,
        coalesce(sum(
            case when schedule.due_date <= snapshot.snapshot_date
                then schedule.scheduled_principal_amount else 0.00 end
        ), 0.00) as scheduled_principal_due_amount
    from {{ ref('fct_loan_monthly_snapshot') }} as snapshot
    left join {{ ref('fct_loan_repayment_schedule') }} as schedule
        on snapshot.account_id = schedule.account_id
    group by snapshot.account_id, snapshot.product_code, snapshot.snapshot_date,
        snapshot.original_balance, snapshot.cumulative_completed_payment_amount
)
select
    *,
    least(cumulative_completed_payment_amount, scheduled_principal_due_amount)
        as assumed_allocated_completed_payment_amount,
    scheduled_principal_due_amount
        - least(cumulative_completed_payment_amount, scheduled_principal_due_amount)
        as scheduled_principal_shortfall_amount,
    original_balance - scheduled_principal_due_amount as future_scheduled_principal_amount,
    greatest(cumulative_completed_payment_amount - scheduled_principal_due_amount, 0.00)
        as unallocated_completed_payment_amount
from account_month
