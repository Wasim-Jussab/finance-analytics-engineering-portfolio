# Day 18 — retaining run history and source fingerprints

**Date:** 11 September 2026

Day 17 made one load atomic, but the next full refresh still replaced its audit manifest. That meant I could prove the current batch was complete without being able to compare it with an earlier successful run.

I added two persistent tables in a separate `audit` schema. `ingestion_runs` stores one row per successful load, while `ingestion_sources` stores the seven related source records. The current seven-row manifest remains in the raw schema because it is useful for checking the active batch against the physical tables.

Before loading, Python now records each CSV's byte size and SHA-256 digest. I used a content fingerprint rather than a modified timestamp because file timestamps can change when a file is copied even if its content does not. A test loads the same inputs twice and confirms two batch IDs, fourteen source-history rows and one distinct customer-file digest.

The clean run passed 8 source freshness checks, 9 dbt models, 151 data tests, the checkpoint hook, 17 Python tests and Ruff. I then changed the stored historical payment digest to a different valid 64-character value. The current-to-history control returned exactly one mismatch and dbt exited with code 1 before I restored the clean database.

The history only contains successful commits. The missing-file test still leaves the previous valid raw batch and now also confirms that no false success record is added. This local audit is useful evidence, but it is stored in the same DuckDB file and is not immutable. A production design would normally put operational run logs in a separate controlled store and include upstream extraction identifiers.
