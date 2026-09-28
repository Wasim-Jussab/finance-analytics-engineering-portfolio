select
    snapshot_date,
    product_code,
    count(*) as row_count
from {{ ref('agg_loan_portfolio_monthly') }}
group by snapshot_date, product_code
having count(*) <> 1
