# Day 2 — give the assistant a narrow tool interface

I added two approved tools: delivery_summary and compare_delivery_periods. Both call the same metric service as the dashboard. The request schema rejects unknown tools, extra arguments and unrecognised regions; no SQL input is accepted.

A comparison requires equally long, non-overlapping calendar periods. That is only a calendar comparability rule, not proof that the cohorts have the same customer mix. Rates are recomputed from counts, and changes are reported in percentage points. An empty denominator produces a null rate change.

The synthetic weekly comparison reconciles 213 versus 218 due shipments, 176 versus 153 on time, and a 12.45 percentage-point decline. Midlands accounts for 22 of the 23 fewer on-time completions. That observation does not establish why deliveries deteriorated.

I checked that tool results equal the underlying service results, regional count differences reconcile and the database fingerprint is unchanged. The API rejects arbitrary SQL arguments, bad dates and overlapping or unequal periods. Eight tests pass, with an upstream TestClient deprecation warning still visible.

This is a deterministic tool interface. No model inference or natural-language planning has been implemented yet.

An actual localhost HTTP request also passed for the tool catalogue and comparison endpoint. Browser rendering was not rechecked in this increment.
