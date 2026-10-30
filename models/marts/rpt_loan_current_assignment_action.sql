-- Observed sequence only: action need not be performed by the assigned team.
with assignment_action as (
    select
        status.account_id,
        status.as_of_date,
        status.current_assignment_id,
        status.current_assigned_team,
        assignment.assigned_at,
        min(action.action_at) as first_action_after_assignment_at
    from {{ ref('rpt_loan_delinquency_case_status') }} as status
    left join {{ ref('fct_loan_case_assignment') }} as assignment
        on status.current_assignment_id = assignment.assignment_id
    left join {{ ref('fct_loan_collection_action') }} as action
        on status.account_id = action.account_id
        and action.action_at >= assignment.assigned_at
        and cast(action.action_at as date) <= status.as_of_date
    group by all
)
select
    *,
    case when first_action_after_assignment_at is not null
        then date_diff('minute', assigned_at, first_action_after_assignment_at)
    end as minutes_to_first_observed_action,
    case
        when current_assignment_id is null then 'Unassigned'
        when first_action_after_assignment_at is null then 'No action since current assignment'
        else 'Action observed since current assignment'
    end as assignment_action_state
from assignment_action
