select
    subscription_payment_id,
    subscription_id,
    billing_date,
    strftime(billing_date, '%Y-%m') as billing_month,
    amount,
    payment_status,
    payment_status = 'Completed' as is_collected
from {{ source('raw', 'subscription_payments') }}
