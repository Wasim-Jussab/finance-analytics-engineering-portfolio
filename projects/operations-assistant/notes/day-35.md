# Operations Day 35 — prove the artifact-to-report handoff before closing the milestone

4 November 2026

I added a real subprocess regression for the persisted proposal-evaluation path.
It exports a trusted local classifier, executes evaluation and checks the report's
artifact hash and scope flags. Then it corrupts that local fixture and verifies
that evaluation fails without replacing the previous report. A stale report is
not a fresh pass; the CLI exit status remains essential.

I consolidated the five-session review and combined current main before validation.
The shared root README and workflow are preserved. The delivered scope is bounded
proposal integration and honest evaluation, not generative inference. There is
still no LLM implementation or new public endpoint.

## Local verification

The package gate passed: 151 tests, grounding 6/6, held-out routing 18/18,
adversarial 27/27, end-to-end questions 10/10, both release gates, runtime readiness
and 18/18 reused proposal-planning cases. Ruff passed. The targeted CLI handoff
regression passed separately, including corrupted-artifact rejection without
report replacement. The existing TestClient dependency warning remains.

After combining current main, the root `make verify` gate also passed: 613 dbt
results, 574 data tests, 116 finance Python tests, controlled scenarios, Ruff and
docs. This validates compatibility with published finance code, not the separate
unpublished stricter-copy proposal, whose WAL blocker remains unresolved.
Root README is unchanged at 486 words; the package overview is 441 words.
