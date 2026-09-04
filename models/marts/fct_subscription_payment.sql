select
    subscription_payment_id,
    subscription_id,
    billing_date,
    cast(date_trunc('month', billing_date) as date) as billing_month,
    amount,
    payment_status,
    payment_status = 'Completed' as is_collected
from {{ source('raw', 'subscription_payments') }}
