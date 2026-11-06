# Facilitator guide

## Before the session

Run prework yourself from a fresh default-branch template copy. Use the pinned
version/source manifest, not a moving Click main. Check Python, gh permissions,
publisher variable and the no-cost replay. Provision live Crew only in a new
container; keys/login belong in prework. Never borrow an existing gateway.

Core time boxes total 60 minutes: 8, 12, 14, 12 and 14. Advanced: 5, 8, 12 and 5.
These are designed estimates, not human-tested completion measurements.
Pilot with one prepared 200-level developer before advertising a guaranteed
duration; measure setup friction and time spent explaining dispositions.

## During labs

Ask learners to predict outcomes before commands. Recommend agents for narrow
test-writing and minimal repairs, not for choosing a tradeoff or producing an
unread answer key. Ask “what observation could prove this claim wrong?”
Pair participants for reviewer/adjudicator roles if access fails.

Lab 2's starter and capstone intentionally fail. The full reference tests stay
green because they are not grading completed learner submissions. A learner
must show repaired checkpoint output, one new negative case and an explanation.
Do not “fix” the workshop by replacing the learner's assignment with the reference.

At lab 4, a legitimate blocked result is preferable to false readiness.
Rebutted requires evidence; deferred requires a real accepted task. Repairs
require new reviews, not manually patched SHAs. Discuss how educational publisher
attestations differ from production reviewer-service provenance.

## Troubleshooting

- Missing container/backend: use replay or manual schema; label live path unverified.
- Missing publisher permission: check gh account and repository variable; do not trust PR text.
- No `PR Readiness` after publication: inspect Actions permissions/events; manually dispatch
  `pr-readiness.yml` on main for the exact PR. Never target upstream.
- Resolved thread still red: thread resolution has no Actions trigger here; explicitly dispatch.
- “Unknown model” or rate expiry: stop; check official access/rates, do not guess another model.
- Unresolved provider usage: preserve ledger and stop. Never retry automatically.
- Upstream case no longer reproduces: freeze this cohort; repair the next release's curriculum.

## Score and debrief

Use [the answer key](ANSWERS.md) only after attempts. Apply the 8/10 capstone
rubric with mandatory integration/trust-boundary scores. Advanced must include
test-backed dispositions, cost distinctions and narrow conclusions.

Record timing, unclear instructions, support needed and failed comprehension
checks in the facilitator's own notes. Do not report automated command checks
as a human learning study.
