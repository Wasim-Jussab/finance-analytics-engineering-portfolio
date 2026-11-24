# Day 52 — keep the denominator explanation intact

21 November 2026

The summary guard previously matched the cancellation count and "excluded"
but not the rest of that sentence. I required the full canonical statement
that cancelled rows are excluded from the denominator. Saying numerator
or another period's denominator can mislead even with correct numbers.

The mutations preserve claims/evidence and exercise both a positive-due
period and an empty/null-rate period. All 12 focused cases passed, with
healthy responses checked before refusal on both answer paths. This is
deterministic template checking, not a general language holdout or a new
generative model. Only the local intent classifier performs inference.

Full `make verify` passed: 227 tests, 6/6 grounding, 18/18 intent,
27/27 adversarial, 13/13 question cases, release/readiness checks,
18/18 proposal cases and saved-report replay. Ruff passed. Separate
HTTP checks returned four healthy summaries and refused four numerator
substitutions across both periods and endpoints; the server stopped.
The existing TestClient dependency warning remains non-failing.
