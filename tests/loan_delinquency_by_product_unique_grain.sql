select
    as_of_date,
    product_code,
    delinquency_band_proxy,
    count(*) as row_count
from {{ ref('agg_loan_delinquency_by_product') }}
group by as_of_date, product_code, delinquency_band_proxy
having count(*) > 1
