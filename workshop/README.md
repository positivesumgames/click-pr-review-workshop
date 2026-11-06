# Prepare PRs with evidence

A 60-minute, 200-level workshop inspired by Kiro Crew's prepare-PR loop, plus a
30-minute, 300-level adversarial-review lab. Learners implement a gate, diagnose
false readiness, test a Click fix, reconcile independent reviews, and add their own policy.

Start with [prework](PREWORK.md), then [the core workshop](WORKSHOP.md).
The [advanced lab](ADVANCED.md) works without paid API calls.
[Facilitator notes](FACILITATOR.md) include timing assumptions and scoring.

The reference implementation is runnable, but is not the learner's completed assignment:

```bash
python3.12 -m venv .venv
mkdir -p .work/tmp .work/pip
TMPDIR="$PWD/.work/tmp" PIP_CACHE_DIR="$PWD/.work/pip" .venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
.venv/bin/python -m pr_review_workshop evaluate --fixture tests/fixtures/ready.json
```

In the published Click-based template, these files live under `workshop/`.
Enter that directory before using the commands. This authoring workspace needs
an independent pinned Click checkout at `.work/click-source`; see prework.

Review-ready is not merge permission. Unknown, missing, stale or unanswered
evidence cannot produce readiness. No auto-merge, global Crew installation,
account-wide budget control, or paid verification is included.

Click's report is reproduced at the pinned source. The partial/repaired
candidates and review replay are explicitly authored teaching data, not measured
model outputs or a production-ready upstream patch.

See [attribution and source pins](ATTRIBUTION.md) and the
[manual refresh command and monthly reminder](MAINTAINER.md).
