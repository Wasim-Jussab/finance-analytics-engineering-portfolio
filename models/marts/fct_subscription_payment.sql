select
    payment.subscription_payment_id,
    payment.subscription_id,
    payment.billing_date,
    calendar.month_start_date as billing_month,
    payment.amount,
    payment.payment_status,
    payment.payment_status = 'Completed' as is_collected
from {{ source('raw', 'subscription_payments') }} as payment
left join {{ ref('dim_date') }} as calendar
    on payment.billing_date = calendar.calendar_date
