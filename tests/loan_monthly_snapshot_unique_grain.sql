select
    account_id,
    snapshot_date,
    count(*) as row_count
from {{ ref('fct_loan_monthly_snapshot') }}
group by account_id, snapshot_date
having count(*) > 1
