{{
    config(
        materialized='incremental',
        incremental_strategy='append',
        schema='audit'
    )
}}

with raw_metrics as (
    select
        count(*) as raw_payment_count,
        count(*) filter (where payment_status = 'Completed') as raw_collected_count,
        coalesce(
            sum(amount) filter (where payment_status = 'Completed'),
            0
        ) as raw_collected_amount,
        max(loaded_at) as latest_source_loaded_at
    from {{ source('raw', 'subscription_payments') }}
),

fact_metrics as (
    select
        count(*) as physical_fact_count,
        count(*) filter (where is_source_present) as current_fact_count,
        count(*) filter (where not is_source_present) as retained_absent_count,
        count(*) filter (
            where is_collected and is_source_present
        ) as current_fact_collected_count,
        coalesce(
            sum(amount) filter (where is_collected and is_source_present),
            0
        ) as current_fact_collected_amount,
        count(*) filter (
            where
                (is_source_present and source_missing_since is not null)
                or (not is_source_present and source_missing_since is null)
        ) as invalid_presence_metadata_count,
        max(source_missing_since) as latest_missing_since
    from {{ ref('fct_subscription_payment') }}
),

duplicate_metrics as (
    select count(*) as duplicate_fact_key_count
    from (
        select subscription_payment_id
        from {{ ref('fct_subscription_payment') }}
        group by subscription_payment_id
        having count(*) > 1
    ) as duplicate_keys
)

select
    '{{ invocation_id }}' as model_run_id,
    cast('{{ run_started_at.strftime("%Y-%m-%d %H:%M:%S.%f") }}' as timestamp)
        as observed_at,
    raw.raw_payment_count,
    fact.physical_fact_count,
    fact.current_fact_count,
    fact.retained_absent_count,
    duplicates.duplicate_fact_key_count,
    fact.invalid_presence_metadata_count,
    raw.raw_collected_count,
    fact.current_fact_collected_count,
    raw.raw_collected_amount,
    fact.current_fact_collected_amount,
    raw.latest_source_loaded_at,
    fact.latest_missing_since,
    (
        raw.raw_payment_count = fact.current_fact_count
        and fact.physical_fact_count
            = fact.current_fact_count + fact.retained_absent_count
        and duplicates.duplicate_fact_key_count = 0
        and fact.invalid_presence_metadata_count = 0
        and raw.raw_collected_count = fact.current_fact_collected_count
        and raw.raw_collected_amount = fact.current_fact_collected_amount
    ) as is_reconciled
from raw_metrics as raw
cross join fact_metrics as fact
cross join duplicate_metrics as duplicates
