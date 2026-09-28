select
    schedule.schedule_id,
    schedule.account_id,
    schedule.instalment_number,
    schedule.due_date,
    cast(date_trunc('month', schedule.due_date) as date) as due_month,
    schedule.scheduled_principal_amount,
    schedule.loaded_at as source_loaded_at
from {{ source('raw', 'loan_repayment_schedule') }} as schedule
