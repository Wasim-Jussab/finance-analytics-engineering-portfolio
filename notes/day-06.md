# Day 6 — running the dbt project

**Date:** 27 August 2026

Today I ran the dbt project against a newly built DuckDB database instead of treating the presence of the files as proof that the setup worked.

The first run failed even though `dbt debug` could connect. The loader had created `data/day6_finance.duckdb`, while the dbt profile was still using its default `data/finance.duckdb`. dbt was therefore connecting to a different, empty database and could not find the `raw` schema. I fixed this by using the same `FINANCE_DUCKDB_PATH` environment variable for the dbt command and documenting it as part of the run sequence.

The next build completed successfully:

- 3 table models built
- 11 data tests passed
- 14 total dbt resources passed
- 0 warnings, 0 errors and 0 skipped resources after the test configuration was updated

I also generated the local dbt documentation output and checked the manifest. It contains the three models and five declared raw sources. The generated `target/` files are not committed because they are reproducible build output rather than source code.

One small change was needed for the dbt version installed locally. The relationship-test arguments were initially written in the older top-level format, which produced a deprecation warning. I moved `to` and `field` under `arguments`, then reran the build without the warning.

The main lesson was that a successful connection test does not prove that the correct database is being used. The path is part of the data pipeline contract, so it needs to be explicit and shared by the loader and transformation step.

## Next question

The current models rebuild as tables on every run. The next useful step is to decide which model, if any, should become incremental and what key or date column would make that safe. I do not want to add incremental logic before there is a real reason and a test for reruns.
