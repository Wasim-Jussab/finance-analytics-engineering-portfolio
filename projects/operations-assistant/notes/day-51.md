# Day 51 — bind the summary's displayed reporting window

20 November 2026

The summary already checked counts, rate, region and snapshot time, but
could display a different reporting window while retaining correct claims.
I bound its header to the approved inclusive start and exclusive end,
including the exclusive-end label.

Three mutations keep claims/evidence unchanged while altering start,
end or inclusivity. Both answer API paths must refuse each alteration.
All nine focused cases passed. This is canonical-template validation,
not a new language holdout or general free-text fact checking. The
existing local intent classifier remains the only inference; the answer
renderer and new guard are deterministic.

Full `make verify` passed: 215 tests, 6/6 grounding, 18/18 intent,
27/27 adversarial, 13/13 question cases, release/readiness checks,
18/18 proposal cases and saved-report replay. Ruff passed. A separate
local HTTP check returned two healthy summaries and refused six altered
windows; the server stopped. The existing TestClient deprecation warning
remains non-failing.
