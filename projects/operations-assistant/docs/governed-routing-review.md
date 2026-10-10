# Governed routing milestone review

Days 6–10 moved the local intent classifier from a passing held-out score to a release process I can explain. Adversarial fixtures now cover safe summaries, comparisons, write requests, causal claims, forecasts and unrelated questions. Routing release policy requires all held-out and adversarial cases to pass with zero unsafe acceptances.

The end-to-end suite then checks the boundary the routing-only scores cannot cover: validated dates and regions, approved read-only tools, grounded claims, evidence IDs, refusals and an unchanged DuckDB snapshot. Decision traces bind each answer or refusal to its model decision and governed parameters without retaining raw question text. The final question-path gate reconciles that evidence under a versioned policy.

The result is deliberately narrow. The model classifies two supported intents or abstains; it does not extract dates, generate prose, explain causes or forecast. Eight question cases and 24 adversarial fixtures are useful regression evidence, not production accuracy or broad safety evidence. A larger, independently labelled evaluation set and monitoring of real distribution shift would be required before widening the boundary.
