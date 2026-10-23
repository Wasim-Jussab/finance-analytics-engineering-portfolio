select
    action_id,
    account_id,
    cast(action_at as timestamp) as action_at,
    action_type,
    action_outcome,
    agent_team
from {{ ref('loan_collection_actions') }}
