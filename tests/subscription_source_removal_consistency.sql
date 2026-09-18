select
    removal.removal_id,
    removal.subscription_id,
    removal.last_observed_status,
    removal.last_observed_at,
    removal.removed_at,
    removal.was_cancelled_before_removal
from {{ ref('fct_subscription_source_removal') }} as removal
left join {{ ref('subscription_agreement_history') }} as current_history
    on removal.subscription_id = current_history.subscription_id
    and current_history.dbt_valid_to is null
left join {{ source('raw', 'subscriptions') }} as source
    on removal.subscription_id = source.subscription_id
where
    current_history.subscription_id is not null
    or source.subscription_id is not null
    or removal.removed_at < removal.last_observed_at
    or removal.was_cancelled_before_removal
        is distinct from (removal.last_observed_status = 'Cancelled')
