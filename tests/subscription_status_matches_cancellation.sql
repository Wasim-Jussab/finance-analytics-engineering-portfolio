select
    subscription_id,
    status,
    cancellation_date
from {{ ref('dim_subscription') }}
where (status = 'Cancelled' and cancellation_date is null)
    or (status = 'Active' and cancellation_date is not null)
