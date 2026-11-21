with classified as (
    select *, case
        when not has_previous_month then 'No comparator'
        when scheduled_principal_shortfall_change > 0 then 'Increase'
        when scheduled_principal_shortfall_change < 0 then 'Decrease'
        else 'Unchanged'
    end as change_direction
    from {{ ref('rpt_loan_monthly_shortfall_contribution') }}
), ranked as (
select *, case when change_direction in ('Increase', 'Decrease') then
    row_number() over (
        partition by snapshot_date, change_direction
        order by abs(scheduled_principal_shortfall_change) desc, account_id
    )
end as direction_rank
from classified
), amounts as (
    select *, case when direction_rank is not null then
        sum(abs(scheduled_principal_shortfall_change)) over (
            partition by snapshot_date, change_direction
        ) end as direction_gross_change_amount,
    case when direction_rank is not null then
        sum(abs(scheduled_principal_shortfall_change)) over (
            partition by snapshot_date, change_direction
            order by direction_rank rows between unbounded preceding and current row
        ) end as cumulative_gross_change_amount
    from ranked
)
select *, cumulative_gross_change_amount
    / nullif(direction_gross_change_amount, 0) as cumulative_gross_change_share
from amounts
