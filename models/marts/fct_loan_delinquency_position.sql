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
    case
        when days_past_due_proxy = 0 then 'Current'
        when days_past_due_proxy between 1 and 29 then '1-29 days'
        when days_past_due_proxy between 30 and 89 then '30-89 days'
        else '90+ days'
    end as delinquency_band_proxy
from {{ ref('fct_loan_schedule_position') }}
