with expected as (
    select
        cast('{{ var("calendar_start_date") }}' as date) as first_date,
        as_of_date as last_date
    from {{ source('raw', 'run_parameters') }}
),
actual as (
    select
        min(calendar_date) as first_date,
        max(calendar_date) as last_date,
        count(*) as date_count
    from {{ ref('dim_date') }}
)
select
    actual.first_date,
    actual.last_date,
    actual.date_count,
    expected.first_date as expected_first_date,
    expected.last_date as expected_last_date
from actual
cross join expected
where actual.first_date <> expected.first_date
    or actual.last_date <> expected.last_date
    or actual.date_count <> date_diff('day', expected.first_date, expected.last_date) + 1
