select
    subscription_id
from {{ ref('subscription_agreement_history') }}
group by subscription_id
having sum(case when dbt_valid_to is null then 1 else 0 end) > 1
