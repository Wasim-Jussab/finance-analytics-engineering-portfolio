# Operations Day 23 — explicit exception outcome

## What I changed

I added one typed outcome filter to the governed exception tool and question path. A caller can select either `late_delivered` or `overdue_open`; unsupported values are rejected. The filter is applied before the total, returned-row count and truncation flag, and it is captured in the evidence request and deterministic answer claims.

I extended the grounding suite with an overdue-open case and the end-to-end question suite with a sixth answered case. The fixed second-week fixture gives me a useful reconciliation: 44 late-delivered plus 21 overdue-open rows equals all 65 exceptions.

## Decision and boundary

I kept outcome as an explicit typed parameter rather than trying to extract it from question wording. The local classifier still decides only which approved tool to call. That makes the contract less conversational, but it keeps a business-critical filter reviewable and avoids claiming parameter inference I have not built or evaluated.

This increment does not add a generative model, retrieval model or new classifier label. Tool execution, filtering, evidence and answer rendering remain deterministic. Actual AI inference is still limited to the previously evaluated local TF-IDF/logistic-regression intent classifier.

## Validation target

The full package gate must pass 76 unit tests, six grounding cases, 18 held-out routing cases, 27 adversarial cases and ten end-to-end question cases. I will only describe the new path as verified after the exact branch head passes GitHub Actions.
