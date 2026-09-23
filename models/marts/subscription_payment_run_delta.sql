{{ config(materialized='view', schema='audit') }}

with ordered as (
    select
        model_run_id,
        observed_at,
        raw_payment_count,
        physical_fact_count,
        current_fact_count,
        retained_absent_count,
        current_fact_collected_count,
        current_fact_collected_amount,
        is_reconciled,
        lag(model_run_id) over run_order as previous_run_id,
        lag(raw_payment_count) over run_order as previous_raw_payment_count,
        lag(physical_fact_count) over run_order as previous_physical_fact_count,
        lag(current_fact_count) over run_order as previous_current_fact_count,
        lag(retained_absent_count) over run_order as previous_retained_absent_count,
        lag(current_fact_collected_count) over run_order
            as previous_collected_count,
        lag(current_fact_collected_amount) over run_order
            as previous_collected_amount
    from {{ ref('audit_subscription_payment_run') }}
    window run_order as (order by observed_at, model_run_id)
)

select
    model_run_id,
    observed_at,
    previous_run_id,
    raw_payment_count,
    physical_fact_count,
    current_fact_count,
    retained_absent_count,
    current_fact_collected_count,
    current_fact_collected_amount,
    is_reconciled,
    raw_payment_count - previous_raw_payment_count as raw_payment_delta,
    physical_fact_count - previous_physical_fact_count as physical_fact_delta,
    current_fact_count - previous_current_fact_count as current_fact_delta,
    retained_absent_count - previous_retained_absent_count as retained_absent_delta,
    current_fact_collected_count - previous_collected_count as collected_count_delta,
    current_fact_collected_amount - previous_collected_amount
        as collected_amount_delta
from ordered
