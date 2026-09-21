select
    model_run_id,
    raw_payment_count,
    physical_fact_count,
    current_fact_count,
    retained_absent_count,
    duplicate_fact_key_count,
    invalid_presence_metadata_count,
    raw_collected_count,
    current_fact_collected_count,
    raw_collected_amount,
    current_fact_collected_amount,
    is_reconciled
from {{ ref('audit_subscription_payment_run') }}
where
    raw_payment_count < 0
    or physical_fact_count < 0
    or current_fact_count < 0
    or retained_absent_count < 0
    or physical_fact_count <> current_fact_count + retained_absent_count
    or raw_payment_count <> current_fact_count
    or duplicate_fact_key_count <> 0
    or invalid_presence_metadata_count <> 0
    or raw_collected_count <> current_fact_collected_count
    or raw_collected_amount <> current_fact_collected_amount
    or not is_reconciled
