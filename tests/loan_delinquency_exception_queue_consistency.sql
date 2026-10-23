with checked as (
    select
        *,
        count(*) over (
            partition by as_of_date
        ) as recalculated_portfolio_exception_count,
        count(*) over (
            partition by as_of_date, product_code
        ) as recalculated_product_exception_count,
        sum(scheduled_principal_shortfall_amount) over (
            partition by as_of_date
        ) as recalculated_portfolio_shortfall_amount,
        sum(scheduled_principal_shortfall_amount) over (
            partition by as_of_date, product_code
        ) as recalculated_product_shortfall_amount,
        max(portfolio_exception_rank) over (
            partition by as_of_date
        ) as maximum_portfolio_rank,
        max(product_exception_rank) over (
            partition by as_of_date, product_code
        ) as maximum_product_rank
    from {{ ref('rpt_loan_delinquency_exception_queue') }}
)
select
    account_id,
    as_of_date,
    'Delinquency exception queue is internally inconsistent' as failure_reason
from checked
where scheduled_principal_shortfall_amount <= 0.00
    or delinquency_band_proxy = 'Current'
    or oldest_uncovered_due_date is null
    or days_past_due_proxy <= 0
    or scheduled_principal_due_amount
        <> assumed_allocated_completed_payment_amount
            + scheduled_principal_shortfall_amount
    or band_priority <> case delinquency_band_proxy
        when '90+ days' then 3
        when '30-89 days' then 2
        when '1-29 days' then 1
        else 0
    end
    or portfolio_exception_rank <= 0
    or product_exception_rank <= 0
    or portfolio_exception_count <> recalculated_portfolio_exception_count
    or product_exception_count <> recalculated_product_exception_count
    or portfolio_shortfall_amount <> recalculated_portfolio_shortfall_amount
    or product_shortfall_amount <> recalculated_product_shortfall_amount
    or maximum_portfolio_rank <> portfolio_exception_count
    or maximum_product_rank <> product_exception_count
    or portfolio_shortfall_share <> round(
        scheduled_principal_shortfall_amount / portfolio_shortfall_amount,
        4
    )
    or product_shortfall_share <> round(
        scheduled_principal_shortfall_amount / product_shortfall_amount,
        4
    )
