select
    payment.payment_id,
    payment.account_id,
    payment.payment_date,
    loan.origination_date
from {{ ref('fct_payment') }} as payment
inner join {{ ref('dim_loan') }} as loan using (account_id)
where payment.payment_date < loan.origination_date
