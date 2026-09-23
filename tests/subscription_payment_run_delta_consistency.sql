with expected as (
    select
        model_run_id,
        observed_at,
        lag(model_run_id) over run_order as previous_run_id,
        raw_payment_count - lag(raw_payment_count) over run_order
            as raw_payment_delta,
        physical_fact_count - lag(physical_fact_count) over run_order
            as physical_fact_delta,
        current_fact_count - lag(current_fact_count) over run_order
            as current_fact_delta,
        retained_absent_count - lag(retained_absent_count) over run_order
            as retained_absent_delta,
        current_fact_collected_count - lag(current_fact_collected_count) over run_order
            as collected_count_delta,
        current_fact_collected_amount - lag(current_fact_collected_amount) over run_order
            as collected_amount_delta
    from {{ ref('audit_subscription_payment_run') }}
    window run_order as (order by observed_at, model_run_id)
)

select coalesce(e.model_run_id, d.model_run_id) as model_run_id
from expected as e
full outer join {{ ref('subscription_payment_run_delta') }} as d
    on e.model_run_id = d.model_run_id
where
    e.model_run_id is null
    or d.model_run_id is null
    or e.observed_at is distinct from d.observed_at
    or e.previous_run_id is distinct from d.previous_run_id
    or e.raw_payment_delta is distinct from d.raw_payment_delta
    or e.physical_fact_delta is distinct from d.physical_fact_delta
    or e.current_fact_delta is distinct from d.current_fact_delta
    or e.retained_absent_delta is distinct from d.retained_absent_delta
    or e.collected_count_delta is distinct from d.collected_count_delta
    or e.collected_amount_delta is distinct from d.collected_amount_delta
