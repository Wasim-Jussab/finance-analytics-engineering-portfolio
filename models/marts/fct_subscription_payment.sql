{{
    config(
        materialized='incremental',
        unique_key='subscription_payment_id',
        incremental_strategy='merge'
    )
}}

select
    payment.subscription_payment_id,
    payment.subscription_id,
    payment.billing_date,
    calendar.month_start_date as billing_month,
    payment.amount,
    payment.payment_status,
    payment.payment_status = 'Completed' as is_collected,
    payment.loaded_at as source_loaded_at
from {{ source('raw', 'subscription_payments') }} as payment
left join {{ ref('dim_date') }} as calendar
    on payment.billing_date = calendar.calendar_date
