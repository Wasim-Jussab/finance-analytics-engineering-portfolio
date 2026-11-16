# Day 47 — keep exception pagination prose tied to its evidence

16 November 2026

I extended the existing runtime grounding gate to the exception header,
total and page counts, offset, ordered shipment IDs and pagination statement.
An answer that says all exceptions were returned when rows remain is
misleading even if its structured claims are correct.

Six tests edit those fields with claims and evidence unchanged. Both API
paths must refuse a wrong next offset, and the existing beyond-last-page
case must still explain its empty page without losing the total population.
The checks are canonical-template comparisons, not general language fact
checking. No generative inference is introduced or evaluated.

I wrapped a long line flagged by Ruff before validation. The eight focused
tests and full package gate passed: 180 tests, 6/6 grounding cases,
13/13 question cases, routing/adversarial checks, readiness, replay and
Ruff. Both API answer paths returned healthy 200s and refused the wrong
next offset with a generic 500 and no answer payload.
