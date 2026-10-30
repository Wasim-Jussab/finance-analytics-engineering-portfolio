# Complete, pinned exception investigation

From this package after installation and `make data`:

```bash
python -m operations_assistant.investigation \
  --start 2026-09-21 --end 2026-09-28 --limit 7 --max-rows 100 \
  --outcome overdue_open
```

The collector calls only the existing approved `delivery_exceptions` tool. It starts
at offset zero, pins subsequent pages to the first snapshot ID and returns all rows
with page-level evidence. It checks full counts, advancing offsets and unique shipment
IDs; empty populations are valid. If the snapshot changes or any page fails, no
partial result is returned. A row cap from 1 to 1,000 limits a complete investigation;
an oversized population is rejected, not silently truncated.

The fixed fixture's overdue-open investigation contains 21 shipments over three
seven-row pages. Counts reconcile to a separate full-tool call in tests. Replacement
between pages, cap breaches and malformed pagination contracts are also tested.

This is deterministic orchestration, not an autonomous agent, model planning or
generative answering. Existing local intent-classifier evaluations still execute
separately. The collector neither retains old snapshots nor promises correctness
of the synthetic business rules merely because hashes agree. Its console output
contains synthetic shipment detail and should not be confused with a production
privacy or access-control design.
