# Day 56 — separate the model label from the governed result

25 November 2026

The fixed suite's observed label includes abstention and guardrails. I
retained the raw model label, acceptance flag, guardrail and primary
decision reason per case, and counted raw matches separately from governed
matches. A blocked request must not quietly become evidence that the
classifier itself predicted unsupported correctly.

Decision counts partition accepted, guardrail, model-unsupported and
below-threshold outcomes. The small controlled fixture demonstrates raw
and governed counts differing; it is not an observed model failure.
The executed-case test reconciles every diagnostic to the result rows.
Both focused tests passed. Training, thresholds and release requirements
are unchanged. The 18 cases remain fixed regressions with known overlap,
not an independent holdout or calibration study. No generative model ran.
Full `make verify` passed: 246 tests, 18/18 fixed routing, 27/27
adversarial, 6/6 grounding, 13/13 question cases, readiness, 18/18
proposal cases and saved-report replay. Ruff passed. The executed report
has 15 raw-label matches and 18 governed matches; decision counts are
13 accepted, 4 guardrail, 0 model-unsupported and 1 below-threshold.
Reference-training overlap remains 5/13. These are regression diagnostics,
not an independent accuracy estimate. The existing TestClient dependency
warning remains non-failing.
