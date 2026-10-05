# Day 1 — make the delivery metric inspectable

I started with the reporting screen and its denominator. A rate calculated only
from completed shipments would hide overdue open work, which is exactly what an
operations user needs to see.

The first view uses promised-date cohorts. An overdue shipment remains in the due
population even if it has not been delivered. Cancellations are reported separately.
The API and dashboard call the same metric service rather than keeping a second
definition in browser code.

The fixture contains an invented regional deterioration so there is something to
investigate. It is labelled synthetic, and I have not written a causal explanation
for a scenario whose cause is simply a generator setting.

I checked exact deadline equality, exclusive date boundaries, cancellation
exclusion, empty populations and regional reconciliation. Invalid replacement
snapshots leave the preceding database intact.

The first custom-fixture tests exposed a metadata assumption: every snapshot was
being labelled seed 42. After changing custom fixtures to carry no seed, the
database constraint also needed to allow that null. The clean tests now pass.

The package includes a localhost dashboard and a read-only API. AI answers are the
next layer, not something simulated by hard-coded prose in this first increment.
