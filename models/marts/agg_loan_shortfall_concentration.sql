select snapshot_date, change_direction,
    count(*) as contributing_account_count,
    max(direction_gross_change_amount) as direction_gross_change_amount,
    0.80 as review_share_threshold,
    min(case when cumulative_gross_change_share >= 0.80 then direction_rank end)
        as accounts_to_review_threshold
from {{ ref('rpt_loan_shortfall_change_ranked') }}
where direction_rank is not null
group by snapshot_date, change_direction
