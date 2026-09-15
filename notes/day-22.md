# Day 22 — separating status history from event dates

Today I extended the snapshot work from plan definitions to subscription agreements.

The source has one current row per agreement. Without a snapshot, changing an agreement from Active to Cancelled would overwrite the state that the pipeline saw previously. The new snapshot versions changes to the customer, plan, start date, cancellation date, billing frequency and status.

I kept two timelines separate:

- `cancellation_date` is the synthetic business event date;
- `dbt_valid_from` and `dbt_valid_to` show when this pipeline observed each source version.

They are not interchangeable. A late-arriving cancellation could have an earlier event date than the time it was loaded, and this local project still has no upstream change timestamp.

The controlled check selects an active agreement from the generated data instead of assuming a particular key. It changes that agreement to Cancelled in a temporary database, uses the fixed reporting date as the cancellation event date and runs both snapshots again. The expected result is 21 agreement versions: 20 current and one closed.

I also moved the common database-copy and dbt command into a shared helper. The plan and agreement checks now use the same isolated setup rather than carrying two copies of the subprocess and temporary-file logic.

The current reporting dimension still reads the latest raw agreement row. I have not turned the snapshot into a historical status report yet because that would need a clear as-at question and careful handling of event time versus observation time.
