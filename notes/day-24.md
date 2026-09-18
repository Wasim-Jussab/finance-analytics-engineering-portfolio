# Day 24 — a missing row is not automatically a cancellation

Today I tested what happens when an agreement disappears from the source.

The snapshots were already configured to invalidate a current version after a hard delete, but one of my tests still required every historical agreement to have exactly one current row. Those two rules contradicted each other. I changed the requirement to one current version for every agreement that still exists in the source, plus a separate control that prevents any key from having more than one current version.

I added `fct_subscription_source_removal` for agreements whose latest observed version has been closed without a replacement. I kept this separate from the status-change fact. Disappearing from an extract could mean source cleanup, retention, migration or an upstream fault; it is not enough evidence to label the agreement Cancelled.

The clean dataset has no removal rows. The controlled scenario copies the database, deletes one active agreement from the temporary raw table, reruns the snapshots and rebuilds the removal fact. GitHub Actions left 20 historical versions, reduced the current population to 19 and created one removal row whose last observed status remained Active. The selected model build passed all ten attached tests.

I deliberately did not add a relationship test from the removal fact to the current subscription dimension. A removed source key is expected to be absent from that current-state model, so such a test would encode the wrong relationship.

The remaining limitation is that a full extract cannot distinguish a genuine upstream deletion from an accidentally omitted record. In production I would want source manifests, deletion indicators or retention rules before assigning business meaning.
