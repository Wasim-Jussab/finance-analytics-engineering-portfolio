select * from {{ ref('rpt_loan_current_assignment_action') }}
where minutes_to_first_observed_action < 0
    or assignment_action_state is distinct from case
        when current_assignment_id is null then 'Unassigned'
        when first_action_after_assignment_at is null then 'No action since current assignment'
        else 'Action observed since current assignment' end
    or minutes_to_first_observed_action is distinct from
        date_diff('minute', assigned_at, first_action_after_assignment_at)
    or (current_assignment_id is null and (
        assigned_at is not null or first_action_after_assignment_at is not null
    ))
