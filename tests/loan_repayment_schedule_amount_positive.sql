select schedule_id, scheduled_principal_amount
from {{ ref('fct_loan_repayment_schedule') }}
where scheduled_principal_amount <= 0
