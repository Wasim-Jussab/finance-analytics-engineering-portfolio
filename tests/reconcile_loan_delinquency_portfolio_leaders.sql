with ranked as (
    select
        *,
        row_number() over (
            partition by as_of_date
            order by loan_account_count desc, product_code
        ) as account_rank,
        row_number() over (
            partition by as_of_date
            order by scheduled_principal_shortfall_amount desc, product_code
        ) as shortfall_rank
    from {{ ref('agg_loan_delinquency_product_risk') }}
),
expected as (
    select
        as_of_date,
        max(case when account_rank = 1 then product_code end)
            as largest_account_product_code,
        max(case when account_rank = 1 then loan_account_count end)
            as largest_account_product_count,
        max(case when shortfall_rank = 1 then product_code end)
            as largest_shortfall_product_code,
        max(case when shortfall_rank = 1 then scheduled_principal_shortfall_amount end)
            as largest_product_shortfall_amount
    from ranked
    group by as_of_date
)
select
    actual.as_of_date,
    'Portfolio concentration leader does not reconcile to product risk' as failure_reason
from {{ ref('agg_loan_delinquency_portfolio_concentration') }} as actual
inner join expected using (as_of_date)
where expected.largest_account_product_code
        <> actual.largest_account_product_code
    or expected.largest_account_product_count
        <> actual.largest_account_product_count
    or expected.largest_shortfall_product_code
        <> actual.largest_shortfall_product_code
    or expected.largest_product_shortfall_amount
        <> actual.largest_product_shortfall_amount
