select snapshot_date, account_id
from {{ ref('rpt_loan_monthly_shortfall_contribution') }}
group by snapshot_date, account_id
having count(*) <> 1
