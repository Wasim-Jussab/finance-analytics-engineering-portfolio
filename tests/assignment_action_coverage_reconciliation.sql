with expected as (
    select
        as_of_date,
        current_assigned_team,
        count(*) as queue_account_count,
        sum(case when current_assignment_id is not null then 1 else 0 end)
            as assigned_account_count,
        sum(case when current_assignment_id is null then 1 else 0 end)
            as unassigned_account_count,
        sum(case when assignment_action_state = 'Action observed since current assignment'
            then 1 else 0 end) as assigned_accounts_with_action,
        sum(case when assignment_action_state = 'No action since current assignment'
            then 1 else 0 end) as assigned_accounts_without_action,
        sum(case when assignment_action_state = 'Action observed since current assignment'
            then 1 else 0 end) * 1.0
            / nullif(sum(case when current_assignment_id is not null then 1 else 0 end), 0)
            as assigned_action_coverage_rate
    from {{ ref('rpt_loan_current_assignment_action') }}
    group by as_of_date, current_assigned_team
)
(select * from expected except all select * from {{ ref('agg_loan_assignment_action_coverage') }})
union all
(select * from {{ ref('agg_loan_assignment_action_coverage') }} except all select * from expected)
