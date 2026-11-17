# Day 83 — show gross changes before they offset

17 November 2026

I grouped account contributions by their observed membership state. I
kept gross increases and decreases alongside the net, so a +5 and -3
within continuing accounts remain visible rather than just showing +2.
Both gross figures use positive magnitudes; net is increase minus decrease.

Counts refer to contribution accounts, including prior-only accounts.
They are not current active-loan counts. No-comparator rows keep unknown
changes null, and unobserved membership states stay absent. The fixture
also includes an entry and exit; these are observed labels, not evidence
of origination, closure, default or recovery.

I wrapped a fixture line flagged by Ruff before rerunning checks. The
full gate passed: 658 dbt results, 126 Python tests, controlled scenarios,
Ruff, docs and lock cleanup. A read-only query showed December's 25
continuing contribution accounts with gross increase 2,754.15, gross
decrease 0.00 and net increase 2,754.15. The offset case is demonstrated
in the controlled fixture, not claimed for that observed month.
