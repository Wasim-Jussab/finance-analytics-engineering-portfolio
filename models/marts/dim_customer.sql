select
    customer_id,
    concat_ws(' ', first_name, last_name) as full_name,
    date_of_birth,
    postcode
from {{ source('raw', 'customers') }}
