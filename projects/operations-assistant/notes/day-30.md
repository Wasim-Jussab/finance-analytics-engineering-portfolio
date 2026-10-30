# Operations Day 30 — test the handoff, then close the milestone

30 October 2026

I added subprocess-level tests for the complete collection and verification
handoff rather than treating successful helper calls as proof the command-line
workflow works. The tests check all exceptions and both outcome subsets, source
file immutability, separate offline verification with the source unavailable,
wrong-anchor rejection and a cap failure that emits no partial report.

I consolidated the project overview around current behaviour and linked the
milestone review instead of retaining a growing sequence of day-labelled feature
sections. The independent package remains in the same repository. I combined the
branch with current main before validation so this milestone does not discard
the completed finance changes or overwrite the concise root README.

The deterministic investigation does not add AI inference. The existing local
classifier is still the only executed model; an independently retained hash is
not a signature or proof that business rules are correct.

## Local verification

The package gate passed: 118 tests, grounding 6/6, held-out routing 18/18,
adversarial 27/27, end-to-end 10/10, both release gates and runtime readiness.
All four new CLI handoff cases also passed separately. The fixture reconciled
65/44/21 rows across ten/seven/three pages. Ruff passed; the existing TestClient
dependency deprecation warning remains.

The combined branch also passed the root finance `make verify`: 613 dbt results,
574 data tests, 82 Python tests, all controlled scenarios, Ruff and dbt docs.
The root README remains 488 words, the operations overview is 399 words and all
relative links in both resolve. Shared Makefile/workflow/root README match main.
