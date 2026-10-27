select * from {{ ref('agg_loan_assignment_action_coverage') }}
where queue_account_count <= 0
    or queue_account_count <> assigned_account_count + unassigned_account_count
    or assigned_account_count <> assigned_accounts_with_action + assigned_accounts_without_action
    or assigned_accounts_with_action < 0 or assigned_accounts_without_action < 0
    or unassigned_account_count < 0
    or assigned_action_coverage_rate is distinct from
        assigned_accounts_with_action * 1.0 / nullif(assigned_account_count, 0)
union all
select * from {{ ref('agg_loan_assignment_action_coverage') }}
qualify count(*) over (partition by as_of_date, current_assigned_team) > 1
