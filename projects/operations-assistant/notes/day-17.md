# Day 17 — expose audit health without exposing audit records

Yesterday's hash-linked ledger could be verified in Python, but an operator could
not inspect its integrity through the running service. I added a read-only status
endpoint that verifies every record and returns the record count, head fingerprint
and format version. It does not return traces, the configured path or raw questions.

I made the disabled state explicit: `not_run` is different from a configured empty
ledger that has passed verification. A changed record returns HTTP 409 rather than
presenting stale metadata as healthy.

This improves local operability, not storage trust. The ledger is still writable
by a local administrator, has no external timestamp or independently retained head,
and has no multi-process writer lock. The endpoint performs deterministic integrity
checking; it adds no new model inference.
