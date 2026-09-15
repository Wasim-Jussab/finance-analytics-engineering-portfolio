select
    subscription_id,
    status,
    start_date,
    cancellation_date
from {{ ref('subscription_agreement_history') }}
where
    (status = 'Active' and cancellation_date is not null)
    or (status = 'Cancelled' and cancellation_date is null)
    or cancellation_date < start_date
