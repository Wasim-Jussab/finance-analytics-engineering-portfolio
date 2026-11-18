# Day 49 — ground signed comparison volumes

18 November 2026

I checked the remaining comparison volume sentence against the approved
tool result: due-volume, late-delivery and overdue-open changes must all
retain their signed values. Correct structured claims do not make an
incorrect sentence safe to show.

Three mutations keep claims and evidence unchanged while changing one
volume number. Both API answer paths must reject each mutation. All nine
focused tests passed; Ruff sorted the new test's imports. A separate
local HTTP check returned healthy comparisons on both paths and refused
all six altered answers with the generic 500 response.

The observed synthetic comparison has due volume +5, late deliveries
+17 and overdue-open shipments +11. These are count changes, not causes.
The regional-decrease narrative is still outside these numeric prose
checks. This is template-specific validation, not free-text factuality
or a generative-model evaluation. Only the local intent classifier runs
inference; metrics and answers remain deterministic.

Full `make verify` passed: 201 Python tests, 6/6 grounding cases,
18/18 intent cases, 27/27 adversarial cases, 13/13 question cases,
release/readiness checks, 18/18 proposal cases and saved-report replay.
Ruff passed. The existing TestClient dependency deprecation warning
remains; it did not fail the gate.
