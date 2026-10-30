-- A recorded action after assignment is not a contact success or staff KPI.
select
    as_of_date,
    current_assigned_team,
    count(*) as queue_account_count,
    count(current_assignment_id) as assigned_account_count,
    count(*) filter (where current_assignment_id is null) as unassigned_account_count,
    count(first_action_after_assignment_at) as assigned_accounts_with_action,
    count(*) filter (
        where current_assignment_id is not null and first_action_after_assignment_at is null
    ) as assigned_accounts_without_action,
    count(first_action_after_assignment_at) * 1.0
        / nullif(count(current_assignment_id), 0) as assigned_action_coverage_rate
from {{ ref('rpt_loan_current_assignment_action') }}
group by as_of_date, current_assigned_team
