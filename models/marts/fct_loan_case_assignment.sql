select
    assignment_id,
    account_id,
    cast(assigned_at as timestamp) as assigned_at,
    assigned_team,
    assignment_reason
from {{ ref('loan_case_assignments') }}
