# Day 16 — retain runtime decisions without retaining raw questions

The API already returned a deterministic decision trace, but the trace disappeared
with the response. I added an optional local JSONL audit ledger that records both
answered and blocked question decisions. Each row is hash-linked to the previous
row, and the ledger is verified before a new row is appended.

I also added the active adapter, inference location and exact model-artifact
fingerprint to each trace. This closes a runtime evidence gap: release readiness
identified the approved artifact, but an individual decision did not previously
carry that identity.

The raw question remains excluded. I deliberately did not call this immutable or
production audit storage: a local administrator can replace or truncate the whole
file, and this first version has no multi-process writer lock or external head
anchor. The business-data tools remain read-only; only the explicitly configured
audit path is written.
