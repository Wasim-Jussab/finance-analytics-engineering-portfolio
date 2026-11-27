# Day 93 — check what the ranked prefix actually contains

27 November 2026

Yesterday's count and contiguous-rank checks could still accept a reversed
ranking. I now recompute full-direction order by absolute movement descending
and account ID ascending, in the same read-only transaction, before the cap.
This mirrors the current mart contract rather than inventing another ranking.

Controlled fixtures reverse two otherwise valid ranks for both directions,
with unequal amounts and ties. All four are refused without changing the
database fingerprint. Two healthy tie cases verify account order and full
denominator coverage. All 22 focused cases passed; Ruff and diff checks passed.
The extra window calculation is acceptable for this small synthetic dataset;
I have not benchmarked it at scale or replaced the upstream dbt contracts.

Full `make verify` passed: 673 dbt results, 153 Python tests, freshness,
history/incremental and degraded-path scenarios, Ruff and docs. Additional
health/evidence verifiers passed; the pipeline lock was removed. The real
CLI still returned the top three of eleven December increasing accounts:
1,354.19 selected from the full 2,754.15 gross denominator. No inference
is used in this reader.
