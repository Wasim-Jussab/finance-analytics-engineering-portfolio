with expected as (
    select
        status.account_id,
        status.as_of_date,
        status.current_assignment_id,
        status.current_assigned_team,
        assignment.assigned_at,
        (
            select min(action.action_at)
            from {{ ref('fct_loan_collection_action') }} as action
            where action.account_id = status.account_id
                and action.action_at >= assignment.assigned_at
                and cast(action.action_at as date) <= status.as_of_date
        ) as first_action_after_assignment_at
    from {{ ref('rpt_loan_delinquency_case_status') }} as status
    left join {{ ref('fct_loan_case_assignment') }} as assignment
        on status.current_assignment_id = assignment.assignment_id
), actual as (
    select account_id, as_of_date, current_assignment_id, current_assigned_team,
        assigned_at, first_action_after_assignment_at
    from {{ ref('rpt_loan_current_assignment_action') }}
)
(select * from expected except all select * from actual)
union all
(select * from actual except all select * from expected)
