with thresholds as (
select snapshot_date, change_direction,
    count(*) as contributing_account_count,
    max(direction_gross_change_amount) as direction_gross_change_amount,
    0.80 as review_share_threshold,
    min(case when cumulative_gross_change_share >= 0.80 then direction_rank end)
        as accounts_to_review_threshold
from {{ ref('rpt_loan_shortfall_change_ranked') }}
where direction_rank is not null
group by snapshot_date, change_direction
)
select t.*, r.cumulative_gross_change_amount as covered_gross_change_amount,
    r.cumulative_gross_change_share as covered_gross_change_share,
    p.cumulative_gross_change_share as previous_rank_gross_change_share
from thresholds t
left join {{ ref('rpt_loan_shortfall_change_ranked') }} r
    on t.snapshot_date = r.snapshot_date and t.change_direction = r.change_direction
    and t.accounts_to_review_threshold = r.direction_rank
left join {{ ref('rpt_loan_shortfall_change_ranked') }} p
    on t.snapshot_date = p.snapshot_date and t.change_direction = p.change_direction
    and t.accounts_to_review_threshold - 1 = p.direction_rank
