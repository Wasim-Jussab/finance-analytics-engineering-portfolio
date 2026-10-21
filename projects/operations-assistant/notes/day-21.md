# Day 21 — expose bounded exception detail before adding model routing

The summary already contained exception rows, but an operator could not request a
small, explicitly bounded worklist through the approved-tool interface. I added a
third read-only tool for that narrower business question.

The tool selects non-cancelled late-delivered and overdue-open shipments by promised
date, keeps one row per shipment and returns total and returned counts. I capped the
caller limit at 100 and used deterministic ordering so repeated requests against the
same snapshot return the same worklist. Inputs remain bound parameters; arbitrary SQL
and comparison-only fields are rejected.

I deliberately did not add natural-language routing or answer prose today. The local
classifier has not been trained or evaluated for an exception-detail intent, and the
grounding suite does not yet cover row-level claims. Calling the deterministic tool
AI would be misleading. The existing TF-IDF/logistic classifier remains the only
model inference.

## Validation

Local execution was unavailable in this run. The branch is published for exact-head
GitHub Actions validation; I will only report executable checks as passed after that
workflow completes.
