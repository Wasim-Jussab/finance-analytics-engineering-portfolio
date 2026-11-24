# Day 55 — exercise the release command boundary

24 November 2026

I added subprocess tests of the actual release CLI, not just its Python
function. Valid evidence must publish an approved decision; missing audit
or coherently edited overlap flags/totals must exit nonzero and leave a
fresh output path absent. These invalid inputs are controlled fixtures,
not corruption observed in the generated report.

A failed run does not delete an older decision file, so the review now
states that consumers must check successful exit before consuming output.
This closes Days 51–55: window/denominator prose guards plus an honest,
validated reference-training overlap audit. It does not create an
independent holdout or add generative inference.

The initial test command ran before setup finished and could not import
pytest. I waited for installation before retrying; this was not a model
or data-test failure. All three focused CLI cases and full `make verify`
passed: 244 tests, 18/18 fixed routing, 27/27 adversarial, 6/6 grounding,
13/13 question cases, readiness, 18/18 proposal cases and saved-report
replay. Ruff passed. Only local intent-classifier inference ran; the
release verifier is deterministic. The existing TestClient dependency
warning remains non-failing.
