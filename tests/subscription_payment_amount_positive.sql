select
    subscription_payment_id,
    amount
from {{ ref('fct_subscription_payment') }}
where amount <= 0
