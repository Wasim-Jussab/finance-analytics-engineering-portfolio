with ordered_dates as (
    select
        calendar_date,
        lag(calendar_date) over (order by calendar_date) as previous_date
    from {{ ref('dim_date') }}
)
select
    previous_date,
    calendar_date
from ordered_dates
where previous_date is not null
    and date_diff('day', previous_date, calendar_date) <> 1
