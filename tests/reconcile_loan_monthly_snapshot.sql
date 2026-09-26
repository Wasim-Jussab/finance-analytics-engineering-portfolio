with latest_snapshot as (
    select * exclude (snapshot_rank)
    from (
        select
            *,
            row_number() over (
                partition by account_id order by snapshot_date desc
            ) as snapshot_rank
        from {{ ref('fct_loan_monthly_snapshot') }}
    )
    where snapshot_rank = 1
)
select
    loan.account_id,
    loan.completed_payment_count as loan_payment_count,
    snapshot.cumulative_completed_payment_count as snapshot_payment_count,
    loan.completed_payment_amount as loan_payment_amount,
    snapshot.cumulative_completed_payment_amount as snapshot_payment_amount
from {{ ref('dim_loan') }} as loan
left join latest_snapshot as snapshot using (account_id)
where snapshot.account_id is null
    or loan.completed_payment_count <> snapshot.cumulative_completed_payment_count
    or loan.completed_payment_amount <> snapshot.cumulative_completed_payment_amount
