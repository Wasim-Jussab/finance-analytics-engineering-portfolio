# Day 82 — trace shortfall changes to account contributions

16 November 2026

I compared current and prior calendar-month positions using the union of
both account sets. That keeps an account which was only in the prior month
visible rather than dropping its negative contribution. Current-only
accounts contribute their current shortfall, but only when the prior month
was actually observed. Missing comparator months still produce null changes.

I labelled membership Entered, Exited or Continuing without calling it a
closure, default or recovery. The isolated fixture has a continuing +5,
an exit -20 and an entry +30, reconciling to a +15 portfolio change.
These are principal-only position differences, not collections flows.

The full local gate passed: 651 dbt results, 125 Python tests, controlled
scenarios, Ruff, docs and lock cleanup. A read-only query found 355
contribution rows; December's 25 continuing accounts sum to a 2,754.15
shortfall increase, matching the portfolio report. The exit path is tested
in the controlled fixture, not claimed as an observed exit in that month.
