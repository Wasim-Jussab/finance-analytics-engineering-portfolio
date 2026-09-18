select
    subscription_plan_id
from {{ ref('subscription_plan_history') }}
group by subscription_plan_id
having sum(case when dbt_valid_to is null then 1 else 0 end) != 1
