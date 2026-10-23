with case_status as (
    select
        as_of_date,
        coalesce(current_assigned_team, 'Unassigned') as workload_bucket,
        current_assigned_team is not null as is_currently_assigned,
        has_recorded_action,
        scheduled_principal_shortfall_amount,
        portfolio_exception_rank
    from {{ ref('rpt_loan_delinquency_case_status') }}
),
bucketed as (
    select
        as_of_date,
        workload_bucket,
        count(*) as case_count,
        sum(case when is_currently_assigned then 1 else 0 end) as assigned_case_count,
        sum(case when not is_currently_assigned then 1 else 0 end) as unassigned_case_count,
        sum(case when has_recorded_action then 1 else 0 end) as actioned_case_count,
        sum(case when not has_recorded_action then 1 else 0 end) as no_action_case_count,
        round(sum(scheduled_principal_shortfall_amount), 2) as scheduled_principal_shortfall_amount,
        min(portfolio_exception_rank) as highest_portfolio_priority_rank,
        max(portfolio_exception_rank) as lowest_portfolio_priority_rank
    from case_status
    group by as_of_date, workload_bucket
),
with_denominators as (
    select
        *,
        sum(case_count) over (partition by as_of_date) as portfolio_case_count,
        round(
            sum(scheduled_principal_shortfall_amount) over (partition by as_of_date),
            2
        ) as portfolio_scheduled_principal_shortfall_amount
    from bucketed
)
select
    as_of_date,
    workload_bucket,
    case_count,
    assigned_case_count,
    unassigned_case_count,
    actioned_case_count,
    no_action_case_count,
    scheduled_principal_shortfall_amount,
    highest_portfolio_priority_rank,
    lowest_portfolio_priority_rank,
    portfolio_case_count,
    portfolio_scheduled_principal_shortfall_amount,
    round(case_count / portfolio_case_count, 4) as portfolio_case_share,
    round(
        scheduled_principal_shortfall_amount
        / portfolio_scheduled_principal_shortfall_amount,
        4
    ) as portfolio_shortfall_share
from with_denominators
