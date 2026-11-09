# Day 38 — verify the answer paired with a decision trace

7 November 2026

I could verify a trace's own digest without noticing that someone had attached
different claims or evidence to it. The weekly demo now also checks the
structured claims, evidence ID, contract version and executed tool request
against that trace before it prints.

I used the same synthetic comparison and API response to test the valid
pairing, then changed the claims, evidence ID, contract and region separately.
The unchanged trace still verifies by itself; each edited pairing must fail.
This checks internal consistency, not source replay, prose accuracy or
authenticity. The classifier still routes locally and the answer is rendered
deterministically.

The first lint run flagged a long line in the regression; I wrapped the
fixture. The final package gate passed: 154 tests, the live CLI, API parity,
all evaluation and readiness checks, and Ruff.
