# Day 57 — validate decision diagnostics before release

26 November 2026

I made the new decision diagnostics mandatory for release and recomputed
their match/reason counts from case rows. Raw labels must be approved;
acceptance, guardrail, observed outcome and primary reason must agree.
Counters must be integer values with exactly the expected reason keys.
The controlled mutations preserve all 18 passing routing results, so a
passing headline score cannot hide inconsistent diagnostic evidence.

Release evaluator version is 1.3.0; old reports need regeneration. I do not
re-derive acceptance from rounded confidence, claim proof of inference,
or turn this reused fixed suite into a holdout. Training, model and router
thresholds are unchanged. All 13 focused diagnostic/CLI cases and full
`make verify` passed: 256 tests, 18/18 fixed routing, 27/27 adversarial,
6/6 grounding, 13/13 questions, readiness, 18/18 proposal cases and replay.
Ruff passed. An executed demo approved the actual reports and refused a
copied report with an altered raw-label match count while its routing
results remained unchanged. Real diagnostics remain 15 raw matches and
18 governed matches. Classifier inference ran in evaluation, not in the
deterministic verifier; no generative model ran. The existing TestClient
dependency warning remains non-failing.
