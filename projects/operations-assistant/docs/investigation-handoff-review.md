# Days 26–30: a reproducible investigation handoff

The business question is: which shipments missed their promises in an explicit
UTC promised-date period, and can someone verify the saved investigation later
without the source database? This is deterministic evidence collection, not a
new model capability.

## Completed boundary

1. Approved tool requests can name the expected snapshot. A changed source fails
   before metrics execute rather than silently joining pages from different loads.
2. The bounded collector follows stable offsets, pins the first snapshot and
   reconciles the complete filtered population. Oversized results fail, not truncate.
3. Saved reports retain full pages, requests and evidence, not just an evidence ID.
4. Offline verification checks hashes, scope, pins, pagination and row reconciliation.
5. The v2 whole-report digest can be checked against an independently retained
   expectation. An embedded digest alone cannot detect a fully rehashed replacement.

## Run the handoff

From this package directory, after installation:

```bash
make verify
python -m operations_assistant.investigation \
  --database data/operations.duckdb --start 2026-09-21 --end 2026-09-28 \
  --outcome overdue_open --limit 7 > investigation.json
```

Inspect the report and retain its `report_sha256` independently before handoff.
Supply that previously retained value, not a value read from the received file:

```bash
python -m operations_assistant.investigation_verify investigation.json \
  --expected-report-sha256 <independently-retained-digest>
```

For the fixed synthetic snapshot, the unfiltered exception population is 65:
44 late-delivered plus 21 overdue-open shipments. With page size seven, these
require ten, seven and three pages respectively. Cancellation is excluded before
counts; the period is inclusive 21 September, exclusive 28 September 2026 UTC.

The executable CLI handoff tests collect all three populations, check source-file
immutability, make the database unavailable, then launch a separate offline
verification process with retained snapshot and report expectations. Wrong anchors
and an undersized collection cap produce no verified/partial JSON on stdout.
These tests run automatically through the existing package `make verify` gate.

## What this does not prove

Hashes are not signatures, trusted storage or evidence that the business rules are
right. The recipient still needs a trustworthy way to retain the expectation.
Two internally agreeing reports can share a wrong rule. The source snapshot is
small and fixed; this is not a production concurrency or scale benchmark.

Actual inference remains the existing local TF-IDF/logistic intent classifier.
The collector, metric computation, prose templates and verifier invoke no model.
The package gate executes the classifier evaluations separately; no generative
inference, paid service or credential is introduced here.

See [snapshot guard](snapshot-guard.md), [collector](pinned-investigation.md),
[offline verifier](offline-investigation-verification.md) and
[external digest boundary](report-digest-anchor.md) for implementation detail.
