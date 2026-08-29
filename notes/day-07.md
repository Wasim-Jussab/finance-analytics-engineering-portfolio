# Day 7 — making the dbt checks more useful

**Date:** 29 August 2026

Today I added more specific checks to the dbt project instead of treating not-null and unique tests as enough.

The new checks cover:

- accepted loan statuses
- accepted payment statuses
- accepted payment methods
- required fields on the reporting models
- payment dates not occurring before the loan origination date

The date check is a singular test because it compares two models rather than checking one column in isolation. It returns the offending payment and loan dates, which should make a failure easier to investigate.

I considered adding source freshness today. I did not add it because the raw tables currently have no ingestion timestamp. The generated `run_parameters.as_of_date` is a reporting date, not a load timestamp, so using it as freshness metadata would give a false sense of control. A future ingestion step should add a real loaded-at value before source freshness is enabled.

This leaves the checks split between:

- structural checks such as keys and relationships
- domain checks such as accepted statuses
- reconciliation checks for completed payment totals
- cross-table checks for impossible dates

The next step is to see whether the new checks catch deliberately invalid rows without changing the model output.
