# Operations Day 32 — valid arguments are not sufficient authority

1 November 2026

I connected proposal validation to the existing classifier and policy boundary.
A structurally valid request can still choose the wrong tool, or follow a question
the existing policy refuses. The new helper rejects both before returning any
authorised request. It does not execute tools or bypass release/readiness checks.

The tests execute the actual local classifier, including a synthetic read-only
service query. My first positive assertion used an assumed response shape and
failed; I corrected it to the existing result/totals/due contract. No production
metric code or training data was changed to make the test pass.

This remains narrow intent inference, not generative AI. Baseline agreement is a
restriction, not proof the baseline understands every question correctly.

## Local verification

The package gate passed: 141 tests, grounding 6/6, held-out routing 18/18,
adversarial 27/27, end-to-end 10/10, both release gates and runtime readiness.
Ruff passed; the existing TestClient dependency warning remains. The positive
authorisation case executed the local classifier and reconciled 218 due synthetic
shipments through the existing tool, preserving database bytes. No generative
inference was implemented or evaluated.
