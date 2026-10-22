select
    as_of_date,
    workload_bucket,
    count(*) as row_count
from {{ ref('agg_loan_delinquency_team_workload') }}
group by as_of_date, workload_bucket
having count(*) <> 1
