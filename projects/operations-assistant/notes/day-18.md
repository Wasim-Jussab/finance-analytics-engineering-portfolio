# Day 18 — verify the ledger against an independently retained head

The hash chain detects changed records and missing middle rows, but yesterday's
status endpoint could still accept a complete replacement with a shorter,
internally valid ledger. I added optional expected-head and expected-count
parameters to the read-only status endpoint.

The service verifies the chain first, then compares the caller's independently
retained values. A matching expectation returns only integrity metadata; a
mismatch returns HTTP 409. Tests cover a matching anchor, malformed input and a
real truncation that remains internally valid without the external expectation.

I deliberately did not write the expected head beside the audit file. A local user
able to replace the ledger could replace that file too. The caller must retain the
anchor in a separate control plane for the check to add value. This is deterministic
integrity verification and adds no model inference.
