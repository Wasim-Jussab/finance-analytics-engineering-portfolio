# Pipeline health summary

`make pipeline-health` reads every completed JSON report in `reports/runs/`, validates the evidence and writes `reports/pipeline-health.json` atomically.

The summary reconciles successful and failed runs, identifies the latest completed run, counts failed stages and reports median and maximum attempted duration by stage. Blocked stages are counted separately and excluded from timing statistics.

This is intentionally a completed-run view. It cannot detect a process that was killed before writing a report, and its success rate is not uptime or an availability SLO. The local lock and runbook remain the controls for interrupted work. GitHub retains the generated summary with the other pipeline evidence for seven days.

Run it after at least one completed pipeline invocation:

```bash
make verify
make pipeline-health
```

Any malformed archive stops the refresh. The previous summary is left intact so corrupt evidence is not silently omitted.

## Policy gate

`config/pipeline-health-policy.json` contains the minimum completed-run count, maximum failure rate, latest-run requirement and selected stage-duration budgets. The command records every breach in the output and exits non-zero when the result is degraded, so local runs and GitHub Actions use the same decision.

Threshold comparisons are inclusive: a failure rate or stage duration exactly at its limit passes. Missing stages are not treated as fast or healthy; they remain outside duration evaluation and the completed-run count stays visible. These repository thresholds are quality controls, not operational uptime targets.
