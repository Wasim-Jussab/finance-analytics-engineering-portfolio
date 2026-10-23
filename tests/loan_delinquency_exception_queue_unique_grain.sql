select
    account_id,
    as_of_date,
    count(*) as row_count
from {{ ref('rpt_loan_delinquency_exception_queue') }}
group by account_id, as_of_date
having count(*) <> 1
