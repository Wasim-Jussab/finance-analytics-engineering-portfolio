with expected as (
    select
        as_of_date,
        coalesce(current_assigned_team, 'Unassigned') as workload_bucket,
        count(*) as case_count,
        sum(case when current_assigned_team is not null then 1 else 0 end) as assigned_case_count,
        sum(case when current_assigned_team is null then 1 else 0 end) as unassigned_case_count,
        sum(case when has_recorded_action then 1 else 0 end) as actioned_case_count,
        sum(case when not has_recorded_action then 1 else 0 end) as no_action_case_count,
        round(sum(scheduled_principal_shortfall_amount), 2) as scheduled_principal_shortfall_amount,
        min(portfolio_exception_rank) as highest_portfolio_priority_rank,
        max(portfolio_exception_rank) as lowest_portfolio_priority_rank
    from {{ ref('rpt_loan_delinquency_case_status') }}
    group by as_of_date, workload_bucket
),
expected_with_denominators as (
    select
        *,
        sum(case_count) over (partition by as_of_date) as portfolio_case_count,
        round(
            sum(scheduled_principal_shortfall_amount) over (partition by as_of_date),
            2
        ) as portfolio_scheduled_principal_shortfall_amount
    from expected
)
select
    coalesce(expected.as_of_date, actual.as_of_date) as as_of_date,
    coalesce(expected.workload_bucket, actual.workload_bucket) as workload_bucket,
    'Team workload does not reconcile to case status' as failure_reason
from expected_with_denominators as expected
full outer join {{ ref('agg_loan_delinquency_team_workload') }} as actual
    using (as_of_date, workload_bucket)
where expected.as_of_date is null
    or actual.as_of_date is null
    or expected.case_count <> actual.case_count
    or expected.assigned_case_count <> actual.assigned_case_count
    or expected.unassigned_case_count <> actual.unassigned_case_count
    or expected.actioned_case_count <> actual.actioned_case_count
    or expected.no_action_case_count <> actual.no_action_case_count
    or expected.scheduled_principal_shortfall_amount
        <> actual.scheduled_principal_shortfall_amount
    or expected.highest_portfolio_priority_rank
        <> actual.highest_portfolio_priority_rank
    or expected.lowest_portfolio_priority_rank
        <> actual.lowest_portfolio_priority_rank
    or expected.portfolio_case_count <> actual.portfolio_case_count
    or expected.portfolio_scheduled_principal_shortfall_amount
        <> actual.portfolio_scheduled_principal_shortfall_amount
    or round(expected.case_count / expected.portfolio_case_count, 4)
        <> actual.portfolio_case_share
    or round(
        expected.scheduled_principal_shortfall_amount
        / expected.portfolio_scheduled_principal_shortfall_amount,
        4
    ) <> actual.portfolio_shortfall_share
