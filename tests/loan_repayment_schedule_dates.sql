select
    schedule.schedule_id,
    schedule.account_id,
    schedule.instalment_number,
    schedule.due_date,
    loan.origination_date
from {{ ref('fct_loan_repayment_schedule') }} as schedule
inner join {{ ref('dim_loan') }} as loan using (account_id)
where schedule.due_date <> cast(
    loan.origination_date + schedule.instalment_number * interval '1 month'
    as date
)
