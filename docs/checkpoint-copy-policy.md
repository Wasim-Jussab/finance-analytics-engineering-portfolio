# Fail closed before copying a completed database

Scenario checks and dbt documentation use isolated database copies. They now
require the original database to open and checkpoint successfully before copying
its database file. Any recovery/checkpoint failure propagates; no scenario or
documentation command may silently continue using a file-only copy without its WAL.

Previously the helper recognised one WAL replay error and assumed that the main
database file was sufficient. That assumption was not proved by successful reads
of the copied file: unreplayed source changes could be absent. Day 71 removes that
exception rather than claiming to repair the underlying DuckDB/dbt failure.

The original database and recovery file are never discarded by this helper. On
the known failure, the new regression proves copying never begins and both files
remain byte-for-byte unchanged. A healthy checkpoint still permits an isolated
copy, preserving its filename/catalogue identity and data. Unrelated errors also
continue to propagate.

This intentionally strengthens `make verify`: if the original cannot checkpoint,
dependent scenarios/docs fail rather than contribute a misleading green result.
Do not restore the old fallback or remove recovery evidence to make the gate pass.
Use the [reader controls](reader-controls-review.md) and capture the actual failure.

Even when checkpoint returns successfully, a nonempty WAL visible after the
connection closes blocks a database-only copy. This is a conservative check,
not a determination that the WAL contains unapplied changes. The caller still
needs a quiescent source: a file-size check is not a writer lock and cannot rule
out changes after the check. The verification pipeline holds its own lock;
standalone callers must not run alongside a writer.
