# Operations Day 29 — anchor the report, not just its snapshot label

29 October 2026

Yesterday's verifier could establish internal consistency but could not distinguish
a fully rewritten, rehashed report from the original. I added a canonical whole-
report digest and an optional independently retained expected digest. New reports
use v2; legacy v1 structural verification remains supported with explicit flags.

The crucial regression deliberately produces an internally valid rewritten report.
It still passes without an external expectation, and fails against the retained
original digest. This is the honest boundary: hashing is not signing, immutable
storage or proof of business truth. A compromised expectation is not a trusted anchor.

Existing page digests are unchanged. The collector/verifier invoke no model;
the package gate still executes the local intent classifier separately. I added no
generative inference or credential requirement.

## Local verification

The package gate passed: 114 tests, grounding 6/6, held-out routing 18/18,
adversarial routing 27/27, end-to-end questions 10/10, both release gates and
runtime readiness. Ruff passed. The 21 targeted verifier/anchor cases passed.
The real CLI produced a v2 report containing 21 rows over three pages; a retained
digest supplied to the offline CLI passed with the external-anchor flag true and
no database opened. The existing TestClient dependency warning remains.
