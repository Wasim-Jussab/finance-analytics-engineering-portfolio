select *
from {{ ref('agg_loan_case_team_coverage') }}
where account_count <= 0
   or account_count <> accounts_with_activity + accounts_without_activity
   or accounts_with_activity < 0
   or accounts_without_activity < 0
   or activity_coverage_rate not between 0 and 1
   or total_activity_count < accounts_with_activity
   or shortfall_without_activity_amount < 0
   or shortfall_without_activity_amount > scheduled_principal_shortfall_amount
   or activity_coverage_rate is null
union all
select * from {{ ref('agg_loan_case_team_coverage') }}
qualify count(*) over (partition by as_of_date, current_assigned_team) > 1
