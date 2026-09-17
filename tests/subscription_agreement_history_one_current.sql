with source_agreements as (
    select subscription_id
    from {{ source('raw', 'subscriptions') }}
),

current_history as (
    select subscription_id
    from {{ ref('subscription_agreement_history') }}
    where dbt_valid_to is null
)

select
    source.subscription_id
from source_agreements as source
left join current_history as history
    on source.subscription_id = history.subscription_id
group by source.subscription_id
having count(history.subscription_id) != 1
