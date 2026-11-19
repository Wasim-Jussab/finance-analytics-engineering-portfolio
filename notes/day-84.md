# Day 84 — count accounts behind the movement

18 November 2026

I added increasing, decreasing and unchanged account counts to the
membership summary. A small net amount can hide opposite movements;
amounts alone also do not say how many accounts contributed. These are
sign buckets for synthetic principal shortfall, not defaults, recoveries,
payment events or active-loan counts.

The three counts partition contribution accounts only when the prior
calendar month exists. Without a comparator they stay null, not zero.
The controlled continuing-account fixture now has +5, -3 and zero: three
accounts, one in each bucket, gross 5/3 and net +2. Entry and exit remain
observed membership labels, not business-event explanations.

The focused fixture passed. I extended the dbt consistency check to
require nonnegative counts and a complete partition, and documented the
null semantics. Full `make verify` passed: 126 Python tests, dbt build,
freshness, controlled history/incremental scenarios, degraded-path checks,
Ruff and documentation generation. The pipeline lock was removed.
A read-only query for 31 December 2025 showed 25 continuing contribution
accounts: 11 increasing, zero decreasing and 14 unchanged. The separate
controlled fixture, not this month, demonstrates opposite movements.
