with loans as (
    select account_id
    from {{ ref('dim_loan') }}
),
positions as (
    select account_id
    from {{ ref('fct_loan_schedule_position') }}
)
select
    coalesce(loans.account_id, positions.account_id) as account_id,
    case
        when loans.account_id is null then 'Position without loan'
        when positions.account_id is null then 'Loan without position'
    end as failure_reason
from loans
full outer join positions using (account_id)
where loans.account_id is null
    or positions.account_id is null
