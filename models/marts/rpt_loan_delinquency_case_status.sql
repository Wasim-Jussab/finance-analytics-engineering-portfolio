with action_summary as (
    select
        account_id,
        count(*) as recorded_action_count,
        min(action_at) as first_action_at,
        max(action_at) as latest_action_at
    from {{ ref('fct_loan_collection_action') }}
    group by account_id
),
latest_action as (
    select
        account_id,
        action_id as latest_action_id,
        action_at,
        action_type as latest_action_type,
        action_outcome as latest_action_outcome,
        agent_team as latest_agent_team
    from {{ ref('fct_loan_collection_action') }}
    qualify row_number() over (
        partition by account_id
        order by action_at desc, action_id desc
    ) = 1
)
select
    queue.account_id,
    queue.customer_id,
    queue.product_code,
    queue.as_of_date,
    queue.delinquency_band_proxy,
    queue.scheduled_principal_shortfall_amount,
    queue.portfolio_exception_rank,
    coalesce(action_summary.recorded_action_count, 0) as recorded_action_count,
    action_summary.recorded_action_count is not null as has_recorded_action,
    action_summary.first_action_at,
    action_summary.latest_action_at,
    latest_action.latest_action_id,
    latest_action.latest_action_type,
    latest_action.latest_action_outcome,
    latest_action.latest_agent_team
from {{ ref('rpt_loan_delinquency_exception_queue') }} as queue
left join action_summary using (account_id)
left join latest_action using (account_id)
