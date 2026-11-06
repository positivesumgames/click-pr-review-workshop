# Build a prepare-PR loop — 60 minutes

By the end you should be able to implement a fail-closed gate, explain its trust
boundary, reproduce a defect before accepting a review, and adapt a policy.
The complete reference is available for comparison, not as the assignment to paste.
Use an AI coding agent for narrow changes and tests. You own the decisions and evidence.

All commands run from the package directory with `.venv/bin/python`.
Exit 0 means success; 10 running; 20 blocked; 2 unreadable. Expected failures
below are intentional. Do not weaken a test to make the demonstration green.

## Lab 1 — Draw the evidence boundary (8 minutes)

### Decision

Inspect `config/review-policy.json`, `tests/fixtures/ready.json` and the workflow
files. Mark which input can be changed by the PR author and which code the
status-writing workflow is allowed to execute.

The loop is preflight → review → reconcile → publish → evaluate → monitor.
A review says “I inspected this input”; a passing test says “this check passed”;
neither is human merge approval. Why do we need all three concepts?

### Build

Make `.work/learning.json` with your prediction for the ready, stale-review and
pending-check fixtures. State the expected exit code and the reason, before running:

```bash
.venv/bin/python -m pr_review_workshop evaluate --fixture tests/fixtures/ready.json
.venv/bin/python -m pr_review_workshop evaluate --fixture tests/fixtures/stale-review.json
.venv/bin/python -m pr_review_workshop evaluate --fixture tests/fixtures/pending-check.json
```

### Checkpoint

Compare 0, 20 and 10 with your predictions. Find the exact reviewer SHA that makes
the second fixture unsafe. The upstream provenance SHA is not the live PR head.

### Comprehension

Why can a successful old-head check not clear a new PR head? Why does the workflow
with status-write permission check out main, while the test workflow checks out
the PR head? [Answers after your attempt](ANSWERS.md#lab-1).

## Lab 2 — Repair a false-green gate (12 minutes)

### Decision

Read `exercises/unsafe_gate.py`. It reports ready when all listed checks succeeded.
Predict what it does with an empty list and with green tests but stale reviews.
Name the missing invariant rather than asking an agent to “make it safer.”

### Build

Run the learner checkpoint; exit 1 is expected for the starter:

```bash
.venv/bin/python exercises/check_gate.py
```

Implement your own `ready(snapshot) -> bool` in that file. You may use
`contracts.parse_evidence` to read the comment envelope, but do not call the
reference evaluator. Require positive evidence, a complete current-head test,
both named independent lenses and current packet/review head binding.
Unknown input must return false, not throw or silently pass.

Suggested agent request: “Help me write tests for the invariant I chose. Do not
implement the gate yet. Include a stale-review counterexample and an empty-list case.”
Inspect the tests, then ask for the smallest implementation and explain each condition.

### Checkpoint

Rerun the learner checkpoint and the reference suite. Add one negative fixture
of your own, such as an unknown conclusion or absent boundaries reviewer.

```bash
.venv/bin/python exercises/check_gate.py
.venv/bin/python -m pytest -q
```

The first must now exit 0. Reference tests must stay green. A passing small
checkpoint is not production certification; compare your gate's omissions with
`src/pr_review_workshop/readiness.py`.

### Comprehension

What does `all([])` return? Why is “no evidence of failure” different from
“positive evidence of completion”? [Answers after your attempt](ANSWERS.md#lab-2).

## Lab 3 — Review a fix, not just the happy example (14 minutes)

### Decision

The pinned Click source reproduces report #3362 by Melebius: a hyphenated option
splits on the usage line. The testable workshop intent is narrower than a full
upstream policy change: keep option/metavar tokens intact while ordinary prose wraps.
Click may need additional design choices before accepting such a global change.

Run the baseline and partial candidate. Both intentionally exit 1:

```bash
.venv/bin/python scripts/case_checkpoint.py baseline --require-intact
.venv/bin/python scripts/case_checkpoint.py partial --require-intact
```

The partial candidate stops hyphen breaks. Why does the reported example look
fixed while a 90-character unhyphenated token still splits?

### Build

Inspect Click's `src/click/formatting.py` at the repository root and its
`TextWrapper` constructor. In your own exercise branch, write a regression test
in `tests/test_workshop_regression.py` for the sibling case before proposing a minimal repair.
Explain the tradeoff:
keeping an indivisible token intact can exceed the nominal line width.

Recommended agent request: “Given this intent, suggest two falsifiable boundary
tests and identify the owning code. Do not edit until I choose the tradeoff.”
Avoid broadly rewriting the formatter or claiming this workshop's hypothesis is
a production-approved Click fix.

### Checkpoint

Run your test against the baseline, partial repair and your proposed repair.
Use the supplied in-memory repaired hypothesis only after recording a prediction:

```bash
.venv/bin/python scripts/case_checkpoint.py repaired --require-intact
.venv/bin/python -m pytest -q tests/test_click_cases.py
```

Both now exit 0. The helper does not modify Click files; your authored candidate
and regression test are the learner deliverable. `baseline`, `partial` and
`repaired` explicitly reenact the three wrapper settings so the scenario suite
remains stable after learner edits. To test the actual current Click source
without that override, run:

```bash
.venv/bin/python scripts/case_checkpoint.py native --require-intact
```

Expect exit 1 before your repair and 0 afterward. On a real PR that changes
`src/click/formatting.py`, the read-only CI also checks this native behavior and
executes your `tests/test_workshop_regression.py`; reenactments alone cannot clear it.

### Comprehension

Which test disproves “the reported example passes, therefore the fix is complete”?
Is an over-width indivisible token a bug or an explicit tradeoff under this intent?
[Answers after your attempt](ANSWERS.md#lab-3).

## Lab 4 — Independently review and reconcile (12 minutes)

### Decision

Choose the two questions you want reviewers to answer. Use the trusted
correctness and boundaries lenses first. Do not let a PR edit its own reviewer
requirement to remove a disagreeing reviewer.

Generate a packet for the offline teaching PR:

```bash
.venv/bin/python -m pr_review_workshop packet --fixture tests/fixtures/ready.json
```

For a real PR, use `packet --repo OWNER/NAME --allowed-repo OWNER/NAME --pr N
--publisher LOGIN`. Every practice PR must target your own repository. Use
`gh pr create --repo "$WORKSHOP_REPO" --base main --head YOUR-EXERCISE-BRANCH`
only after committing/pushing your chosen exercise change to that repository.
Do not run this live path against the offline `aaaaaaaa…` packet.

### Build

Recommend two fresh read-only AI contexts in your disposable Crew environment,
one per lens. Give both the identical packet and trusted lens text; neither
first pass sees the other. Reviewers return JSON with these fields:

```json
{
  "schema_version": 1,
  "head_sha": "full packet head SHA",
  "base_sha": "full packet base SHA",
  "input_digest": "packet digest",
  "lens": "correctness",
  "phase": "independent",
  "status": "completed",
  "run_id": "unique context/run identity",
  "reviewer": "actual reviewer or manual name; do not invent a served model",
  "read_only": true,
  "findings": []
}
```

Each finding needs `id`, `severity`, `category`, `claim`, `location`,
`reproduction`. See the schema validator for allowed categories/severities.
Manual reviewers use exactly this schema. If runtime access fails, use the
authored replay to practice adjudication, not as claimed agent performance:

```bash
.venv/bin/python -m pr_review_workshop review --packet .work/packet.json --mode replay
.venv/bin/python scripts/export_reviews.py
```

For every finding, test legitimacy and proportionality; assign one outcome.
Write `.work/dispositions.json` yourself as an array. Each item names
`finding` (`lens:ID`), `outcome`, current `head_sha`, `decided_by` (`learner`
for this offline example), and concrete `evidence`.
Fixed/rebutted need test/code evidence; accepted-and-deferred also needs local
issue, owner, due date and explicit acceptance. A security/data-loss deferral
or needs-a-decision stops the loop.

### Checkpoint

Show before/after test evidence for the long-token claims and disproof for the
replay's short-token claim. Then run:

```bash
.venv/bin/python -m pr_review_workshop reconcile --packet .work/packet.json --reviews .work/correctness.json .work/boundaries.json --dispositions .work/dispositions.json --publisher learner
```

Do not mark a claim fixed when reviewing a packet that still contains the defect.
Offline observations may rebut/defer a claim or block for repair. A real fix
requires a new head and entirely fresh reviews; never edit stale SHAs to pass.

On a live PR, use `publish` only after fresh reviews and authorized publication.
The status-writing workflow reads authenticated comment evidence, never executes
it or downloads PR-produced artifacts. Inspect `PR Readiness`. After resolving
an inline thread, explicitly refresh with `gh workflow run pr-readiness.yml
--repo "$WORKSHOP_REPO" --ref main -f pr=N`; thread resolution alone is not a
supported Actions trigger. Human merge authority remains separate.

### Comprehension

Why separate reviewer contexts? What facts must change after a repair? Can JSON
prove a model actually ran or a regression test is true? [Answers](ANSWERS.md#lab-4).

## Lab 5 — Adapt the loop and bound observation (14 minutes)

### Decision

Choose a new gate relevant to your work, not another agreeable model vote.
Examples: require a regression-test reference for a changed public API, or
limit unexplained changes outside the declared owning module. Define one
positive, one negative and one unknown-input case.

### Build

Implement `additional_gate(packet, evidence)` in `exercises/capstone.py`.
Return `(bool, nonempty_reason)`. Create `exercises/test_my_gate.py` with a
`cases()` function returning `(packet, evidence, expected_bool)` triples.
Different learners must choose and justify their own policy; no unchanged
supplied implementation completes this capstone.

Integrate your gate into a small learner wrapper that combines the reference
verdict and your extra gate: both must pass. Show that a base-ready fixture can
still be rejected by your new policy. Do not modify the trusted production
workflow to self-approve that policy; control-code changes need maintainer review.

Inspect `monitor.py`: it runs one tick, not an agent sleeping in a loop.
The host schedules future ticks, with 12 cycles, 900 seconds and three unchanged
cycles as bounds. Ready, terminal, user-stop, blocker, unreadable state, stall
and budget exhaustion all stop. Never reset a stopped loop automatically.

### Checkpoint

```bash
.venv/bin/python exercises/check_capstone.py
.venv/bin/python -m pytest -q tests/test_monitor.py
.venv/bin/python -m pytest -q
```

The capstone command initially fails until you supply code/tests. The facilitator
must also check integration and novelty; a trivial function can game a small
automated check and does not pass the rubric.
For isolated live Crew, use the distinct skill's finite monitor recipe; no
auto-merge, push, rebase, or paid requests belong in observation.

### Comprehension

Why is a stopped monitor not automatically restarted? What evidence would make
you dispatch a new agent turn, and what should remain silent?
[Answers and capstone rubric](ANSWERS.md#lab-5).
