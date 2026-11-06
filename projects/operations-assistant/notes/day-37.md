# Day 37 — match the demo's decision to the API

6 November 2026

I wanted to tell whether the weekly comparison shown in the terminal was the
same decision a reviewer would see through the API. I reused the question
API's trace builder so the demo now records the same typed scope, classifier
identity, evidence ID and claims digest without copying the question text.

The regression executes both routes with the same local classifier and
synthetic snapshot. It checks the claims, verifies the digest and requires the
full core traces to match. I left proposal and release metadata separate:
parity is about the decision and evidence, not proof that both routes took
the same path. A digest isn't a signature. The answer stays deterministic;
the only inference in this test is local intent classification.

Local `make verify` passed: 154 tests, the API parity check, the live CLI
demo and all evaluation and readiness gates. Ruff passed too.
