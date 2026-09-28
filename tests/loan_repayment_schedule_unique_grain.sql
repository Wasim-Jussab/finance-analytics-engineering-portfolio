select account_id, instalment_number, count(*) as row_count
from {{ ref('fct_loan_repayment_schedule') }}
group by account_id, instalment_number
having count(*) <> 1
