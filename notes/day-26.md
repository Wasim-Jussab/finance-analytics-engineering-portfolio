# Day 26 — incremental payment merges and safe reruns

I have avoided adding incremental logic just to put the word in the project. The
dataset is small and the raw loader still replaces its tables in full, so converting
one fact does not make this pipeline faster in any meaningful way. The useful thing
to prove was whether I could rerun a model safely when a payment arrives late or an
existing source record is corrected.

I changed `fct_subscription_payment` to a dbt incremental model using
`subscription_payment_id` as the merge key. That key already defines the fact's
grain and has uniqueness tests, which makes it a more defensible choice than a date
watermark. I also carried the source `loaded_at` timestamp into the fact so a merged
row can still be tied to the accepted raw batch.

The check runs against a disposable copy of the built database. An unchanged rerun
stayed at 150 rows. I then changed one failed attempt to Completed and inserted one
late retry with a new key. The merge updated the existing row, inserted the new row
once and finished with 151 distinct keys. Running the same build again left the
result unchanged.

Two things needed separating during validation. The first attempt hit the existing
DuckDB recovery-file conflict before the scenario reached an assertion, so I did not
count it as incremental evidence. The merge then worked on a clean copy, but my
initial dbt selector refreshed only the fact while an eagerly selected monthly
reconciliation test read the old aggregate. Selecting the fact and its descendants
together fixed the real dependency problem; each final selected build passed all 36
results.

The remaining limitation is important: because `raw.subscription_payments` is still
a full-refresh table, dbt considers all 150 source rows before merging. This is safe
upsert behaviour, not yet a production CDC or watermark design. I would need a
reliable upstream change field and a late-arrival policy before filtering the source
scan.
