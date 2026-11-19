with positions as (
    select * from {{ ref('fct_loan_monthly_schedule_position') }}
),
months as (
    select distinct snapshot_date from positions
),
pairs as (
    select current_month.snapshot_date, previous_month.snapshot_date as previous_snapshot_date
    from months as current_month
    left join months as previous_month on previous_month.snapshot_date
        = date_trunc('month', current_month.snapshot_date) - interval '1 day'
),
account_keys as (
    select pairs.snapshot_date, positions.account_id
    from pairs join positions on pairs.snapshot_date = positions.snapshot_date
    union
    select pairs.snapshot_date, positions.account_id
    from pairs join positions on pairs.previous_snapshot_date = positions.snapshot_date
)
select
    pairs.snapshot_date,
    pairs.previous_snapshot_date,
    keys.account_id,
    pairs.previous_snapshot_date is not null as has_previous_month,
    current_position.product_code as current_product_code,
    previous_position.product_code as previous_product_code,
    case
        when pairs.previous_snapshot_date is null then 'No comparator'
        when previous_position.account_id is null then 'Entered'
        when current_position.account_id is null then 'Exited'
        else 'Continuing'
    end as position_state,
    coalesce(current_position.scheduled_principal_shortfall_amount, 0.00)
        as scheduled_principal_shortfall_amount,
    case when pairs.previous_snapshot_date is not null
        then coalesce(previous_position.scheduled_principal_shortfall_amount, 0.00)
    end as previous_scheduled_principal_shortfall_amount,
    case when pairs.previous_snapshot_date is not null then
        coalesce(current_position.scheduled_principal_shortfall_amount, 0.00)
        - coalesce(previous_position.scheduled_principal_shortfall_amount, 0.00)
    end as scheduled_principal_shortfall_change
from account_keys as keys
join pairs on keys.snapshot_date = pairs.snapshot_date
left join positions as current_position on keys.account_id = current_position.account_id
    and pairs.snapshot_date = current_position.snapshot_date
left join positions as previous_position on keys.account_id = previous_position.account_id
    and pairs.previous_snapshot_date = previous_position.snapshot_date
