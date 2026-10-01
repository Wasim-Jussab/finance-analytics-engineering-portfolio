# Day 38 — keep verification inside the run lock

Reviewing the runner exposed a gap in the previous increment. The pipeline held
its lock through the dbt build, but Make then ran the historical scenarios, tests
and documentation outside that lock. Another invocation could therefore replace
the shared inputs while verification was still reading the database.

I moved the complete finance gate into the same runner behind a `--verify`
option. The additional stages remain explicit in the run report and stop after
the first failure. The shorter `make pipeline` command still runs four stages.

The new overlap test attempts a second invocation during the incremental scenario,
after the main build. It must fail before reaching any stage and cannot write a
second run report. GitHub Actions also checks that a successful verification
releases its lock.

The separate operations application starts alongside this work. Its metric
definition and learning log live with that package, rather than expanding the
finance README again.
