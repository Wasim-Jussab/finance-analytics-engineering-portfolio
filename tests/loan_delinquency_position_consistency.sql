select
    account_id,
    'Delinquency proxy does not match the tested schedule position' as failure_reason
from {{ ref('fct_loan_delinquency_position') }}
where delinquency_band_proxy <> case
        when days_past_due_proxy = 0 then 'Current'
        when days_past_due_proxy between 1 and 29 then '1-29 days'
        when days_past_due_proxy between 30 and 89 then '30-89 days'
        else '90+ days'
    end
    or (delinquency_band_proxy = 'Current')
        <> (scheduled_principal_shortfall_amount = 0.00)
    or (oldest_uncovered_due_date is null)
        <> (scheduled_principal_shortfall_amount = 0.00)
