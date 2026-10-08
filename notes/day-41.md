# Day 41 — summarise completed pipeline health

The retained run reports were useful one at a time, but they did not answer the first operational questions: how many completed runs passed, which stage failed and whether stage duration changed.

I added a small summary command over the archived JSON evidence. It validates each report before calculating run outcomes and stage timings, and writes the result atomically. A malformed archive now fails the refresh rather than disappearing from the denominator.

I deliberately did not call the success rate uptime. The evidence only covers processes that reached report writing, so a killed process can still be absent. There is also no alerting, scheduler or service-level objective in this local project. Those limits are more important than a decorative monitoring dashboard.
