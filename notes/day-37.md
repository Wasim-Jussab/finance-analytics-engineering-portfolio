# Day 37 — prevent overlapping pipeline runs

Yesterday's runner made the stage order and failure path visible, but it still
allowed two commands to start at the same time. That matters more with DuckDB than
it would with a server database because both processes can target the same local
file. The recovery-file problem seen during earlier builds made this the next
useful control to add.

I added one atomic lock around the whole pipeline rather than separate locks for
each stage. Generation replaces the shared CSV files and ingestion replaces the
raw tables, so protecting only the dbt step would still allow the inputs to change
under a running build.

The lock stores a run ID, UTC start time and process ID. A second invocation exits
with code 2 before generation starts, reports the recorded owner and keeps the
previous completed run report. The owner releases the lock after success or a
handled failure, and checks its run ID before deleting anything.

## What I checked

- A second invocation cannot reach its first stage while the lock is held.
- The previous successful report is not overwritten by a rejected invocation.
- Normal completion and exceptions release the owner's lock.
- A process does not delete a lock whose ownership metadata has changed.
- The real command-line entry point exits with code 2 before touching DuckDB.
- The complete project gate still passes through the locked runner.

I deliberately did not delete locks automatically after a fixed age. A long dbt
run could be valid, and treating it as stale would allow exactly the overlap this
control is meant to prevent. An interrupted process can therefore leave a lock
that needs to be inspected. The next useful step is a clear timeout and recovery
policy based on an observed process state, not just elapsed time.
