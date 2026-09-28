with schedule_summary as (
    select
        account_id,
        count(*) as instalment_count,
        min(instalment_number) as first_instalment,
        max(instalment_number) as last_instalment,
        count(distinct instalment_number) as distinct_instalments
    from {{ ref('fct_loan_repayment_schedule') }}
    group by account_id
)
select
    loan.account_id,
    loan.term_months,
    schedule.instalment_count,
    schedule.first_instalment,
    schedule.last_instalment,
    schedule.distinct_instalments
from {{ ref('dim_loan') }} as loan
left join schedule_summary as schedule using (account_id)
where schedule.account_id is null
    or schedule.instalment_count <> loan.term_months
    or schedule.first_instalment <> 1
    or schedule.last_instalment <> loan.term_months
    or schedule.distinct_instalments <> loan.term_months
