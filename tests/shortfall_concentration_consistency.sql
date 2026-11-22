with source_totals as (
    select snapshot_date, case when scheduled_principal_shortfall_change > 0
        then 'Increase' else 'Decrease' end as change_direction,
        count(*) as accounts, sum(abs(scheduled_principal_shortfall_change)) as gross
    from {{ ref('rpt_loan_monthly_shortfall_contribution') }}
    where has_previous_month and scheduled_principal_shortfall_change <> 0
    group by snapshot_date, change_direction
), invalid_source as (
    select coalesce(a.snapshot_date, s.snapshot_date) as snapshot_date,
        coalesce(a.change_direction, s.change_direction) as change_direction
    from {{ ref('agg_loan_shortfall_concentration') }} a full outer join source_totals s
        on a.snapshot_date = s.snapshot_date and a.change_direction = s.change_direction
    where a.snapshot_date is null or s.snapshot_date is null
        or a.contributing_account_count is distinct from s.accounts
        or a.direction_gross_change_amount is distinct from s.gross
), checked as (
    select a.*, r.cumulative_gross_change_share as crossing_share,
        p.cumulative_gross_change_share as preceding_share
    from {{ ref('agg_loan_shortfall_concentration') }} a
    left join {{ ref('rpt_loan_shortfall_change_ranked') }} r
        on a.snapshot_date = r.snapshot_date and a.change_direction = r.change_direction
        and a.accounts_to_review_threshold = r.direction_rank
    left join {{ ref('rpt_loan_shortfall_change_ranked') }} p
        on a.snapshot_date = p.snapshot_date and a.change_direction = p.change_direction
        and a.accounts_to_review_threshold - 1 = p.direction_rank
)
select snapshot_date, change_direction from checked
where contributing_account_count <= 0 or direction_gross_change_amount <= 0
    or review_share_threshold <> 0.80
    or accounts_to_review_threshold < 1
    or accounts_to_review_threshold > contributing_account_count
    or crossing_share is null or crossing_share < review_share_threshold
    or (accounts_to_review_threshold > 1 and
        (preceding_share is null or preceding_share >= review_share_threshold))
union all
select snapshot_date, change_direction from {{ ref('agg_loan_shortfall_concentration') }}
group by snapshot_date, change_direction having count(*) <> 1
union all
select snapshot_date, change_direction from invalid_source
