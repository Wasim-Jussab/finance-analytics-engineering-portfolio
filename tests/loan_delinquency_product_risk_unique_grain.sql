select
    as_of_date,
    product_code,
    count(*) as row_count
from {{ ref('agg_loan_delinquency_product_risk') }}
group by as_of_date, product_code
having count(*) <> 1
