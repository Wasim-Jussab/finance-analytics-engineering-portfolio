with totals as (
    select
        (select coalesce(sum(amount), 0) from {{ source('raw', 'payments') }}
         where payment_status = 'Completed') as raw_total,
        (select coalesce(sum(amount), 0) from {{ ref('fct_payment') }}
         where is_successful) as fact_total,
        (select coalesce(sum(completed_payment_amount), 0) from {{ ref('dim_loan') }})
            as loan_total
)
select *
from totals
where raw_total <> fact_total
   or raw_total <> loan_total
