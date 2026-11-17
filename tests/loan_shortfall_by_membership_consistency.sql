with duplicate_grain as (
    select snapshot_date, position_state
    from {{ ref('agg_loan_shortfall_by_membership') }}
    group by snapshot_date, position_state having count(*) <> 1
),
monthly as (
    select snapshot_date, sum(contribution_account_count) as accounts,
        sum(scheduled_principal_shortfall_amount) as current_shortfall,
        sum(previous_scheduled_principal_shortfall_amount) as previous_shortfall,
        sum(scheduled_principal_shortfall_change) as change_amount
    from {{ ref('agg_loan_shortfall_by_membership') }}
    group by snapshot_date
),
account_counts as (
    select snapshot_date, count(*) as accounts
    from {{ ref('rpt_loan_monthly_shortfall_contribution') }} group by snapshot_date
),
invalid_month as (
    select coalesce(m.snapshot_date, r.snapshot_date) as snapshot_date
    from monthly as m
    full outer join {{ ref('rpt_loan_portfolio_monthly_change') }} as r
        on m.snapshot_date = r.snapshot_date
    left join account_counts as a on m.snapshot_date = a.snapshot_date
    left join {{ ref('agg_loan_portfolio_total_monthly') }} as p
        on r.previous_snapshot_date = p.snapshot_date
    where m.snapshot_date is null or r.snapshot_date is null
        or m.accounts is distinct from a.accounts
        or m.current_shortfall is distinct from r.scheduled_principal_shortfall_amount
        or m.previous_shortfall is distinct from p.scheduled_principal_shortfall_amount
        or m.change_amount is distinct from r.scheduled_principal_shortfall_change
)
select snapshot_date from duplicate_grain
union all
select snapshot_date from invalid_month
union all
select snapshot_date from {{ ref('agg_loan_shortfall_by_membership') }}
where contribution_account_count <= 0
    or (has_previous_month and (
        gross_shortfall_increase_amount is null or gross_shortfall_decrease_amount is null
        or scheduled_principal_shortfall_change is null
        or gross_shortfall_increase_amount < 0 or gross_shortfall_decrease_amount < 0
        or scheduled_principal_shortfall_change <>
            gross_shortfall_increase_amount - gross_shortfall_decrease_amount
    ))
    or (not has_previous_month and (
        gross_shortfall_increase_amount is not null or gross_shortfall_decrease_amount is not null
        or scheduled_principal_shortfall_change is not null
        or previous_scheduled_principal_shortfall_amount is not null
    ))
