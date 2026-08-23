select
    payment_id,
    account_id,
    payment_date,
    strftime(payment_date, '%Y-%m') as payment_month,
    amount,
    payment_status,
    payment_method,
    payment_status = 'Completed' as is_successful
from {{ source('raw', 'payments') }}
