# Day 23 — deriving changes without inventing history

Today I built the first reporting model that consumes the agreement snapshot.

`fct_subscription_status_change` compares consecutive versions of each agreement and keeps a row only when the status changes. Its grain is one observed transition, identified by the dbt version ID on the new side of that transition.

The clean seed-42 build has no status-change rows. That is intentional. The first snapshot tells me the state that the pipeline saw, but there is no earlier version to compare it with. Adding fabricated previous states would make the output easier to demonstrate while weakening the meaning of the model.

The controlled cancellation scenario now does three things:

1. changes one active agreement to Cancelled in a temporary database;
2. reruns the snapshots;
3. rebuilds and tests the status-change fact.

GitHub Actions produced exactly one transition from Active to Cancelled, and the selected model build passed all eleven attached tests. The model keeps both the synthetic cancellation event date and the snapshot observation timestamp, plus the number of days between them. A positive delay means the pipeline observed the event after its stated business date; a negative delay could represent a future-dated event known in advance.

I added reconciliation back to the complete snapshot history rather than checking only the one demonstration row. I also test that cancellation transitions have an event date and that the stored delay agrees with the two dates.

This still is not a full event-sourcing system. A source correction can look like a change, and snapshots only capture states seen by successful runs. Those limitations need to stay visible when this model is used.
