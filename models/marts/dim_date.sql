with bounds as (
    select
        cast('{{ var("calendar_start_date") }}' as date) as calendar_start_date,
        as_of_date as calendar_end_date
    from {{ source('raw', 'run_parameters') }}
),
calendar_dates as (
    select cast(generated_date as date) as calendar_date
    from bounds
    cross join generate_series(
        calendar_start_date,
        calendar_end_date,
        interval 1 day
    ) as generated(generated_date)
)
select
    cast(strftime(calendar_date, '%Y%m%d') as integer) as date_key,
    calendar_date,
    cast(extract(year from calendar_date) as integer) as calendar_year,
    cast(extract(quarter from calendar_date) as integer) as calendar_quarter,
    cast(extract(month from calendar_date) as integer) as month_number,
    strftime(calendar_date, '%B') as month_name,
    cast(date_trunc('month', calendar_date) as date) as month_start_date,
    last_day(calendar_date) as month_end_date,
    calendar_date = last_day(calendar_date) as is_month_end,
    cast(strftime(calendar_date, '%u') as integer) in (6, 7) as is_weekend
from calendar_dates
