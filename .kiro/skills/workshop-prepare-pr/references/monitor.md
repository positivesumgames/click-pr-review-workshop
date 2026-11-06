# Bounded observation

Inside a separately provisioned disposable Crew container, discover its
`monitor_start` schema before arming anything. The pinned upstream interface uses
`message`, `interval_secs`, `max_cycles`, `max_runtime_secs`, `judge`, and `banner`.
Do not assume an unverified installed version has the same interface.

Use a 60-second cadence, at most 12 cycles and 900 seconds, `judge=False`.
The message must include the exact learner repository, PR number, publisher,
package directory, and `.work/watch.json` state path. Each tick runs:

```bash
python -m pr_review_workshop watch --repo OWNER/NAME --allowed-repo OWNER/NAME --pr N --publisher LOGIN
```

The helper does one read and exits. The scheduler performs the wait outside the
agent turn. Dispatch only when `dispatch` is true. Report and call the runtime's
stop mechanism when `stop_reason` is non-null. An unchanged tick is silent.
Never push, rebase, reset bounds, publish paid requests or merge during observation.
A repair is a new, explicitly authorized task with fresh reviews.

The helper enforces cycle/time/stall bounds even if the scheduler wakes late.
Fixture mode verifies the same state machine without a running Crew gateway.
Live Crew behavior is unverified until exercised in an isolated container.
