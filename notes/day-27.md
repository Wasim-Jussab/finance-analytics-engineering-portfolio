# Day 27 — retaining source-absent payments safely

Day 26 proved that the payment fact could insert a late key and update an existing
one. It left another important question unanswered: if the next full source snapshot
does not contain a payment, should the fact delete it or keep counting it forever?
Neither choice felt defensible without making the state visible.

I kept the previously observed fact row and added `is_source_present` plus
`source_missing_since`. An absent key remains available as evidence, but current
collection reconciliations and the monthly aggregate only use rows still present in
the latest raw snapshot. If the key reappears, the merge restores it to current
reporting and clears the absence timestamp.

The controlled scenario removed one completed payment after the existing insert and
correction checks. The fact stayed at 151 distinct keys, while the current population
and monthly attempt total fell to 150. Exactly one row was marked absent with a
timestamp. Restoring the source row returned all 151 keys to current reporting, and
one more rerun made no further change. All six selected builds passed 38 results.

The first attempt did not reach the scenario because the known DuckDB recovery file
could not be replayed. I retained that file separately and reran from the checkpointed
database; I have not counted the failed setup attempt as evidence for this logic.

The wording matters here. I am recording source absence, not a confirmed deletion.
This extract has no deletion event or reason code, so it cannot tell me whether a row
was genuinely removed or accidentally omitted. In a production design I would want
an upstream tombstone, extract identifier and agreed retention policy before treating
absence as a business event.
