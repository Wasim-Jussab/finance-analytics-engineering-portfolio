# Metric edge cases — Days 41–45

I tightened the existing classifier-backed route rather than adding a second
model. Dates, region, outcome and pagination remain typed inputs; the model
selects an approved tool, not SQL.

The question release gate now requires 13 executed cases, nine answered and
four blocked. These reuse known question wording to isolate metric behaviour,
not to measure new language generalisation:

- Empty baseline: the change in counts is available but rate change is null.
- Beyond-last page: 21 overdue-open exceptions remain 21 even when zero rows
  are returned at offset 25.
- North-only comparison: baseline 46/53 and current 47/54 on-time shipments;
  both numerator and denominator stay within the region.

Run `make verify` from this package. It runs tests, builds the persisted
local classifier, evaluates routing and answers, checks exact-artifact release
readiness, and generates/replays the fixed weekly comparison.

Canonical summary grounding checks counts and rate in prose as well as
structured claims and evidence. Six mutation tests change numbers while
preserving claims. The question and direct-answer APIs now enforce that
evaluator before returning an answer. A failed check returns HTTP 500 with
no answer; it is an internal output failure, not bad client input.
The raw tool endpoint still returns deterministic tool data.

Runtime regressions verify the healthy 200 response and rejection of a changed
rate on both answer routes. These checks are template-specific. They are not
a general prose fact checker; the new numeric checks do not cover comparison
or exception prose. Routing still uses TF-IDF/logistic classification, not
a generative model. No LLM inference or LLM evaluation has been executed.
