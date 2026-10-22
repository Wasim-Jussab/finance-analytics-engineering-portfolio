# Day 22 — evaluate exception questions end to end

Day 21 deliberately stopped before natural-language routing. Today I added an
approved `delivery_exceptions` classifier label only after extending the training,
held-out, adversarial, grounding and end-to-end fixtures.

The distinction is intentional: count and rate questions still route to the summary,
while explicit row-level wording such as “list”, “individual”, “IDs” and “worklist”
routes to bounded exception detail. Dates, region and limit remain typed request
fields; the classifier does not extract or invent parameters.

The answer is still deterministic. It reports total and returned counts, truncation,
the bounded shipment rows and the evidence ID. The only model inference remains the
local TF-IDF/logistic-regression intent classification. There is no generative model
and the fixed fixture results are not a production accuracy claim.

## Validation

I locally exercised the revised classifier specification against all 18 held-out
labels before publishing. The complete package needs DuckDB, FastAPI and pytest,
which are unavailable in this execution environment, so exact-head GitHub Actions
remains the executable package gate.
