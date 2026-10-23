select
    assignment.assignment_id,
    assignment.account_id,
    assignment.assigned_at,
    queue.as_of_date,
    'Assignment must belong to the queue and be observed by the reporting date' as failure_reason
from {{ ref('fct_loan_case_assignment') }} as assignment
left join {{ ref('rpt_loan_delinquency_exception_queue') }} as queue
    using (account_id)
where queue.account_id is null
    or assignment.assigned_at > cast(queue.as_of_date as timestamp) + interval 1 day
