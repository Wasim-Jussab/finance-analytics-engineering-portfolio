# Operations Day 28 — make saved evidence verifiable

28 October 2026

The collector previously returned page evidence references but not complete page
results. I now retain those bounded results and added an offline verifier that can
recompute every tool digest and reconcile scope, page pinning and complete rows.
The digest helper preserves the existing tool hash contract.

I deliberately kept the claim narrow: this establishes internal consistency, not
authenticity or correctness of the source business rules. A malicious writer can
recalculate an unanchored report. A separately retained snapshot expectation adds
an identity check, not a signature or immutable evidence store.

The regression cases exercise JSON persistence, empty results, tampering, incomplete
reports and a removed pin even after its digest is recalculated. Verification must
work with DuckDB connections blocked. Neither this verifier nor the collector adds
model inference; the package gate still executes the existing local classifier.

## Local verification

The final package gate passed: 105 tests, grounding 6/6, held-out routing 18/18,
adversarial routing 27/27, end-to-end questions 10/10 and runtime readiness.
Both release gates and Ruff passed. All 12 new verifier tests passed separately.
The real collector CLI saved a 21-row, three-page overdue-open investigation;
the offline CLI verified it with `database_opened: false`. The existing TestClient
dependency deprecation warning remains. No generative inference is claimed.
