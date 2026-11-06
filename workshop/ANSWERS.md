# Answer key — open after attempting each checkpoint

## Lab 1

The stale fixture's correctness review uses `cccc…`, not the actual `aaaa…` head.
A successful old check says nothing about new code. A privileged workflow runs
trusted main because executing a PR's scripts/package hooks could expose its
write token. Tests run PR code only with read privileges and no secrets.
Readiness is evidence completion, not human approval or a claim that code has no bugs.

## Lab 2

`all([])` is true. Require a named current-head completed-success test instead
of assuming the list is complete. Verify both lenses and separate run identities,
head/base/packet binding and readable input. Unknown is false. A correct learner
gate names these conditions and tests them; importing the completed reference
does not show that understanding. The small checkpoint deliberately does not
prove every production invariant.

## Lab 3

Hyphen splitting and long-word splitting are separate wrapper decisions.
The partial candidate changes only the former. The 90-character token exposes
the sibling gap. Disabling both keeps tokens intact but allows a token wider than
the line. That is a deliberate workshop tradeoff, not proof of the right global
Click design. Plain prose must still wrap. A production contribution needs
upstream design agreement, a broader regression suite and review.

## Lab 4

Independent contexts reduce anchoring; different run IDs alone do not prove
independence. Every changed head, base, diff or intent invalidates the packet.
The authenticated publisher attests the reviews and dispositions; the server
checks identity, completeness and freshness but cannot prove the model ran or
the prose test evidence is truthful. The deterministically executed tests and
human adjudication supply separate validation.

At the partial packet, `correctness:F1` and `boundaries:F1` are supported
long-token concerns. `boundaries:F2` is rebutted by the width-65 hyphen result.
Do not say F1 is fixed on that same defective packet. Either stop for repair
and rerun reviews on a new head, or document explicit acceptance/defer work in
an actual local issue with owner/due/acceptance. The rubric favors a tested repair.
Do not fabricate an issue URL to get a green offline demonstration.

## Lab 5

Silent unchanged ticks avoid paying for agent reasoning when no facts changed.
Bounds buy a human decision when progress stalls; automatically resetting them
makes the loop effectively unbounded. A meaningful change is a new head/base,
gate outcome, review, disposition or thread state, not a timestamp.

Capstone rubric, 0–2 points each:

1. New measurable policy and reason, not an unchanged supplied gate.
2. Positive, negative and unknown-input tests.
3. Wrapper combines reference readiness and the new gate; unknown rejects.
4. Trust boundary: policy changes do not self-authorize privileged execution.
5. Clear stop/change behavior and evidence-based explanation.

Pass: at least 8/10, and no zero in integration or trust boundary. A hard-coded
true/false, reference import alone, or model vote without a measurable rule fails.
No completed capstone implementation is supplied; facilitator inspection is required.

## Advanced

Reservations are taken before the request; reported token cost is computed after
it. Unknown usage retains the reservation and stops. A limit applies to this
runner ledger, not another process/account. Read pricing date, token caps,
attempt/round bounds and modifiers. Requested model identity is not served
identity; the adapter requires the returned model to match.

First-pass reviews have no peer evidence. Cross-critique may expose false positives
but cannot replace the original ledger. The authored example has one shared
validated long-token mechanism, one false positive from the boundaries replay,
and no measured model-performance comparison. Both providers see different lenses,
so even live differences are confounded by prompts and this one example.

Advanced rubric: pass only if the learner demonstrates independent input order,
retains first-pass/challenge separation, validates each disposition with a test,
labels fictional replay costs or real reported usage correctly, explains stop
conditions, and restricts conclusions to this example. Agreement alone fails.
