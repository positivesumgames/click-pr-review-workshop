# Two-provider adversarial review — optional 30 minutes

Learning goal: preserve independent first passes, challenge claims without
conflating agreement with evidence, and explain what the runner budget controls.
This is an example-specific experiment, not a general model-quality ranking.
Authored teaching replay is the default; its tokens and “provider results”
are fictional, not measured outputs.

## Estimate and choose a run (5 minutes)

Decision: identify the approved providers, exact models, rate date and runner limit.
Prework owns keys and container setup. Do not spend on a whim during this lab.

Build/inspect:

```bash
.venv/bin/python -m pr_review_workshop estimate
.venv/bin/python -m pytest -q tests/test_budget.py
```

Rates checked 2026-11-06: GPT-5.4 mini snapshot input/output $0.75/$4.50 per million,
Claude Haiku 4.5 snapshot $1/$5 per million. The configured input allowance is
64,000 tokens and output cap 4,096, no tools, caching, premium/regional modifiers
or automatic retries. Four calls reserve at most $0.301824; the eight-attempt
ceiling is $0.603648 at those recorded rates. The default runner limit is $5,
not the estimate and not an account-wide cap. Recheck current rates before live use.
Reservations are conservative allowances, not a guarantee that a provider
reports or bills exactly as expected; unexpected usage stops the run.

Checkpoint: explain estimates versus reservations versus reported usage.
Comprehension: why can other apps still spend on the same account? [Answer](ANSWERS.md#advanced).

## Independently review, then cross-critique (8 minutes)

Decision: what information may each first-pass reviewer receive? What changes
when the second round begins?

Build:

```bash
.venv/bin/python -m pr_review_workshop review --packet .work/packet.json --mode replay
.venv/bin/python scripts/export_reviews.py
```

Inspect `.work/review-run.json`. Both first passes receive the same immutable
packet, but different lenses. Only after both finish does each receive its peer's
review for cross-critique. The two arrays stay separate; challenge findings do
not silently rewrite the first-pass record or clear a finding.

If prework explicitly approved a live run, execute **inside the disposable
container**, with a new output path, selected keys/models and validated rates:

```bash
python -m pr_review_workshop review --packet .work/packet.json --mode live --budget 5 --approve-paid-run --out .work/live-run-1.json
```

This performs four calls, not an endless retry loop. Each request reserves cost
before sending. A failed/unreadable response stops and retains unresolved cost.
Inspect the saved ledger before any separately approved retry; do not delete
or overwrite it. Attempts count toward eight, and no more than two rounds.
A new output path does not grant permission to reset a budget or repeat paid work.

Checkpoint: verify first-pass inputs lack peer evidence, all results bind the same
SHA/digest, and cross-critique remains separate. Run the provider-contract tests.
Comprehension: is pinning a requested model proof of the model served? [Answer](ANSWERS.md#advanced).

## Adjudicate with tests (12 minutes)

Decision: list each first-pass claim before looking at peer criticism.
Deduplicate the two long-token reports for comparison, but retain both original
finding IDs for dispositions. The short-token claim is a plausible false positive.

Build: reproduce on the partial candidate. Repair in a new revision or explain
a rebuttal/accepted deferral at the unchanged revision. Never declare an unchanged
defective packet fixed. Use the case checkpoint for the hyphen case and long token;
write one extra boundary test the replay does not already supply.

Checkpoint: create the disposition ledger, showing each claim, reachable input,
test result, outcome, current SHA and evidence. Reconcile with the CLI only when
the claims genuinely have complete outcomes; needs-a-decision is an honest stop.
Comprehension: can two identical model findings replace one reproduction?
[Answer](ANSWERS.md#advanced).

## Compare and defend the result (5 minutes)

Decision: choose measures that this single experiment can actually support.

Build: record unique validated mechanisms per reviewer, overlap, false positives,
unresolved claims, and cost. Count a shared mechanism once for overlap, not twice
as “two unique bugs.” On replay, label cost and usage fictional. On live runs,
distinguish conservative reservations and provider-reported token cost from
the provider's final invoice. Do not claim universal model strengths.

Checkpoint: defend the ledger to a partner using tests rather than consensus.
Comprehension: what extra examples/control of lens assignments would be needed
before attributing a difference to the model rather than the prompt?
[Answer and rubric](ANSWERS.md#advanced).
