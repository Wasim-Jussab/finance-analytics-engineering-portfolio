with expected as (
    select
        as_of_date,
        current_assigned_team,
        count(*) as account_count,
        sum(case when has_recorded_activity then 1 else 0 end) as accounts_with_activity,
        sum(case when not has_recorded_activity then 1 else 0 end) as accounts_without_activity,
        sum(total_activity_count) as total_activity_count,
        sum(scheduled_principal_shortfall_amount) as scheduled_principal_shortfall_amount,
        sum(case when not has_recorded_activity
            then scheduled_principal_shortfall_amount else 0 end
        ) as shortfall_without_activity_amount,
        sum(case when has_recorded_activity then 1 else 0 end) * 1.0 / count(*)
            as activity_coverage_rate
    from {{ ref('rpt_loan_case_activity_summary') }}
    group by as_of_date, current_assigned_team
),
differences as (
    (select * from expected except all select * from {{ ref('agg_loan_case_team_coverage') }})
    union all
    (select * from {{ ref('agg_loan_case_team_coverage') }} except all select * from expected)
)
select * from differences
