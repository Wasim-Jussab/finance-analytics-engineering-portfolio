# Day 68 — locate reader failures in the actual lifecycle

31 October 2026

I added an opt-in diagnostic runner around the existing locked pipeline. It reads
the original raw loan population after each executed stage from loading onwards,
keeping the first failed read even if later reads recover. This separates failure
timing from build success without changing the standard quality gate.

I chose raw loans because later case marts do not exist immediately after loading.
The check is not a replacement for account/date readiness. It makes no repair,
deletes no recovery evidence and does not attribute causality from stage timing.
The previous scratch database was no longer available, so today's run uses a
fresh checkout rather than claiming to have repaired yesterday's failing file.

## Local validation and remaining blocker

`make verify` completed successfully: 613 dbt results, 574 data tests, 100 Python
tests, all controlled scenarios, Ruff and documentation. The original database
probe then returned ready: all four populations 25 and all account checks zero,
with no WAL present. That is one observation, not a permanent reliability fix.

The actual lifecycle invocation was blocked by a retained `reports/pipeline.lock`
after the standard run. I did not remove it or select another lock to bypass it.
Consequently no actual first-failing-stage result is claimed. I added a graceful
exit-2 CLI path and a regression that proves an existing lock is preserved without
writing diagnostic output. The six final targeted lifecycle tests passed; the
whole Python suite was rerun after this addition: 101 passed, with Ruff clean.
The full build gate above preceded this final CLI handling change; it was not
rerun past the retained lock. The lock ownership/retention
needs investigation before rerunning the live diagnostic in this checkout.
