with source_totals as (
    select snapshot_date,
        sum(case when scheduled_principal_shortfall_change > 0
            then scheduled_principal_shortfall_change else 0 end) as increases,
        sum(case when scheduled_principal_shortfall_change < 0
            then -scheduled_principal_shortfall_change else 0 end) as decreases
    from {{ ref('rpt_loan_monthly_shortfall_contribution') }}
    group by snapshot_date
), checked as (
    select r.*, case when change_direction = 'Increase' then s.increases
        else s.decreases end as expected_gross,
        (select sum(abs(c.scheduled_principal_shortfall_change))
         from {{ ref('rpt_loan_shortfall_change_ranked') }} c
         where c.snapshot_date = r.snapshot_date and c.change_direction = r.change_direction
            and c.direction_rank <= r.direction_rank) as expected_cumulative
    from {{ ref('rpt_loan_shortfall_change_ranked') }} r
    join source_totals s on r.snapshot_date = s.snapshot_date
)
select snapshot_date, account_id from checked
where (direction_rank is null and (
    direction_gross_change_amount is not null or cumulative_gross_change_amount is not null
    or cumulative_gross_change_share is not null
)) or (direction_rank is not null and (
    direction_gross_change_amount is distinct from expected_gross
    or cumulative_gross_change_amount is distinct from expected_cumulative
    or cumulative_gross_change_share is null
    or cumulative_gross_change_share <= 0 or cumulative_gross_change_share > 1
    or abs(cumulative_gross_change_share - expected_cumulative / nullif(expected_gross, 0)) > 1e-10
))
