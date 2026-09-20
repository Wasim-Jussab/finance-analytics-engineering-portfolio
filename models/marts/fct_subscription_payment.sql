{{
    config(
        materialized='incremental',
        unique_key='subscription_payment_id',
        incremental_strategy='merge'
    )
}}

with current_source as (
    select
        payment.subscription_payment_id,
        payment.subscription_id,
        payment.billing_date,
        calendar.month_start_date as billing_month,
        payment.amount,
        payment.payment_status,
        payment.payment_status = 'Completed' as is_collected,
        payment.loaded_at as source_loaded_at,
        true as is_source_present,
        cast(null as timestamp) as source_missing_since
    from {{ source('raw', 'subscription_payments') }} as payment
    left join {{ ref('dim_date') }} as calendar
        on payment.billing_date = calendar.calendar_date
)

select *
from current_source

{% if is_incremental() %}

union all

select
    existing.subscription_payment_id,
    existing.subscription_id,
    existing.billing_date,
    existing.billing_month,
    existing.amount,
    existing.payment_status,
    existing.is_collected,
    existing.source_loaded_at,
    false as is_source_present,
    case
        when existing.is_source_present
            then cast('{{ run_started_at.strftime("%Y-%m-%d %H:%M:%S.%f") }}' as timestamp)
        else existing.source_missing_since
    end as source_missing_since
from {{ this }} as existing
left join current_source as source
    on existing.subscription_payment_id = source.subscription_payment_id
where source.subscription_payment_id is null

{% endif %}
