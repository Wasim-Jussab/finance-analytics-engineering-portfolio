select
    loan.account_id,
    loan.original_balance,
    coalesce(sum(schedule.scheduled_principal_amount), 0.00) as scheduled_principal
from {{ ref('dim_loan') }} as loan
left join {{ ref('fct_loan_repayment_schedule') }} as schedule using (account_id)
group by loan.account_id, loan.original_balance
having loan.original_balance <> coalesce(
    sum(schedule.scheduled_principal_amount), 0.00
)
