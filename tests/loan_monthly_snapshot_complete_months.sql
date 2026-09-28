with expected as (
    select
        loan.account_id,
        calendar.calendar_date as snapshot_date
    from {{ ref('dim_loan') }} as loan
    cross join {{ ref('dim_date') }} as calendar
    where calendar.is_month_end
        and loan.origination_date <= calendar.calendar_date
),
actual as (
    select account_id, snapshot_date
    from {{ ref('fct_loan_monthly_snapshot') }}
)
select
    coalesce(expected.account_id, actual.account_id) as account_id,
    coalesce(expected.snapshot_date, actual.snapshot_date) as snapshot_date,
    case
        when expected.account_id is null then 'Unexpected snapshot'
        when actual.account_id is null then 'Missing snapshot'
    end as exception_reason
from expected
full outer join actual using (account_id, snapshot_date)
where expected.account_id is null
    or actual.account_id is null
