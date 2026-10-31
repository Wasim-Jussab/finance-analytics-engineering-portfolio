# Snapshot-pinned investigations

Read `evidence.snapshot_id` from the first response. Send it as
`expected_snapshot_id` on every subsequent tool, answer or question request.
The optional field accepts exactly 64 lowercase hexadecimal characters.

For example, add that ID to the existing exception request with `offset: 5`.
Matching requests execute normally; a mismatch returns HTTP 422 with a restart
message before the metric function executes. Malformed IDs are schema errors.
The guard applies to all three approved tools, not only pagination.

The snapshot includes metadata and shipment contents, not just filesystem bytes.
It is recomputed on the same read-only connection used for the metric. It is not
an authentication token or proof of correctness. Historical snapshots are not kept
and this increment adds no cursor, retention or cross-process locking protocol.
Unpinned calls remain supported and must not be presented as a pinned investigation.

Tests exercise all three POST paths, including actual local intent inference on
the question path, then replace the synthetic source and assert fail-before-metric
behaviour. Release evaluations continue to test the existing unpinned contract.
