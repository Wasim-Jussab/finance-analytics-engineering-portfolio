select
    action.action_id,
    action.account_id,
    'Synthetic collection action is outside the governed queue reporting window'
        as failure_reason
from {{ ref('fct_loan_collection_action') }} as action
left join {{ ref('rpt_loan_delinquency_exception_queue') }} as queue
    using (account_id)
where queue.account_id is null
    or cast(action.action_at as date) > queue.as_of_date
