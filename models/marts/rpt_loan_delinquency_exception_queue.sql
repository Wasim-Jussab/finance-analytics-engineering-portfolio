with exceptions as (
    select
        *,
        case delinquency_band_proxy
            when '90+ days' then 3
            when '30-89 days' then 2
            when '1-29 days' then 1
            else 0
        end as band_priority
    from {{ ref('fct_loan_delinquency_position') }}
    where scheduled_principal_shortfall_amount > 0.00
),
ranked as (
    select
        *,
        row_number() over (
            partition by as_of_date
            order by
                band_priority desc,
                scheduled_principal_shortfall_amount desc,
                account_id
        ) as portfolio_exception_rank,
        row_number() over (
            partition by as_of_date, product_code
            order by
                band_priority desc,
                scheduled_principal_shortfall_amount desc,
                account_id
        ) as product_exception_rank,
        count(*) over (
            partition by as_of_date
        ) as portfolio_exception_count,
        count(*) over (
            partition by as_of_date, product_code
        ) as product_exception_count,
        sum(scheduled_principal_shortfall_amount) over (
            partition by as_of_date
        ) as portfolio_shortfall_amount,
        sum(scheduled_principal_shortfall_amount) over (
            partition by as_of_date, product_code
        ) as product_shortfall_amount
    from exceptions
)
select
    account_id,
    customer_id,
    product_code,
    source_loan_status,
    as_of_date,
    scheduled_principal_due_amount,
    assumed_allocated_completed_payment_amount,
    scheduled_principal_shortfall_amount,
    oldest_uncovered_due_date,
    days_past_due_proxy,
    schedule_position_status,
    delinquency_band_proxy,
    band_priority,
    portfolio_exception_rank,
    product_exception_rank,
    portfolio_exception_count,
    product_exception_count,
    portfolio_shortfall_amount,
    product_shortfall_amount,
    round(
        scheduled_principal_shortfall_amount / portfolio_shortfall_amount,
        4
    ) as portfolio_shortfall_share,
    round(
        scheduled_principal_shortfall_amount / product_shortfall_amount,
        4
    ) as product_shortfall_share
from ranked
