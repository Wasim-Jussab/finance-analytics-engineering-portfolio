select
    schedule.schedule_id,
    schedule.account_id as schedule_account_id,
    allocation.account_id as allocation_account_id,
    schedule.instalment_number as schedule_instalment_number,
    allocation.instalment_number as allocation_instalment_number,
    schedule.due_date as schedule_due_date,
    allocation.due_date as allocation_due_date,
    schedule.scheduled_principal_amount as schedule_amount,
    allocation.scheduled_principal_amount as allocation_amount
from {{ ref('fct_loan_repayment_schedule') }} as schedule
full outer join {{ ref('fct_loan_schedule_allocation') }} as allocation
    using (schedule_id)
where schedule.schedule_id is null
    or allocation.schedule_id is null
    or schedule.account_id <> allocation.account_id
    or schedule.instalment_number <> allocation.instalment_number
    or schedule.due_date <> allocation.due_date
    or schedule.scheduled_principal_amount
        <> allocation.scheduled_principal_amount
