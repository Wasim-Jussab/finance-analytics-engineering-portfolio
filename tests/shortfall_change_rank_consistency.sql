with ranked as (
    select * from {{ ref('rpt_loan_shortfall_change_ranked') }}
), source as (
    select * from {{ ref('rpt_loan_monthly_shortfall_contribution') }}
)
select r.snapshot_date, r.account_id
from ranked r full outer join source s
    on r.snapshot_date = s.snapshot_date and r.account_id = s.account_id
where r.account_id is null or s.account_id is null
    or r.scheduled_principal_shortfall_change is distinct from s.scheduled_principal_shortfall_change
    or r.change_direction is distinct from case
        when not s.has_previous_month then 'No comparator'
        when s.scheduled_principal_shortfall_change > 0 then 'Increase'
        when s.scheduled_principal_shortfall_change < 0 then 'Decrease'
        else 'Unchanged' end
    or r.direction_rank is distinct from case
        when s.has_previous_month and s.scheduled_principal_shortfall_change <> 0 then (
            select count(*) + 1 from source c
            where c.snapshot_date = s.snapshot_date
                and sign(c.scheduled_principal_shortfall_change)
                    = sign(s.scheduled_principal_shortfall_change)
                and (abs(c.scheduled_principal_shortfall_change)
                    > abs(s.scheduled_principal_shortfall_change)
                    or (abs(c.scheduled_principal_shortfall_change)
                        = abs(s.scheduled_principal_shortfall_change) and c.account_id < s.account_id))
        ) end
union all
select snapshot_date, account_id from ranked
group by snapshot_date, account_id having count(*) <> 1
