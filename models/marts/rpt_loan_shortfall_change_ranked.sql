with classified as (
    select *, case
        when not has_previous_month then 'No comparator'
        when scheduled_principal_shortfall_change > 0 then 'Increase'
        when scheduled_principal_shortfall_change < 0 then 'Decrease'
        else 'Unchanged'
    end as change_direction
    from {{ ref('rpt_loan_monthly_shortfall_contribution') }}
)
select *, case when change_direction in ('Increase', 'Decrease') then
    row_number() over (
        partition by snapshot_date, change_direction
        order by abs(scheduled_principal_shortfall_change) desc, account_id
    )
end as direction_rank
from classified
