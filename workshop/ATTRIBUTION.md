# Sources and licensing

This is an independent educational implementation, not Kiro Crew production
parity or an official Pallets/Kiro workshop.

Kiro Crew inspiration: the stability article, Crew docs, prepare-PR skill,
local-review/PR-status scripts, profile, readiness workflow and bounded-monitor
recipe at `8dbdf0443c7b2ccea832b343a5b26c86b75524fd`. The workshop retains the
ideas of independent read-only reviews, CI-derived contracts, exact-head binding,
finding dispositions, a single aggregate signal and bounded convergence.
It excludes auto-merge, full review fleet, main repair, queues and self-heal sweeps.
The workshop code/material is licensed Apache-2.0; see `LICENSE`.

Primary Kiro sources:

- https://kiro.dev/blog/software-factory-stability/
- https://kiro.dev/docs/crew/
- https://github.com/kirodotdev/KiroCrew

Click source remains BSD-3-Clause under its original `LICENSE.txt` at the teaching
repository root. Source pin:
`8abb77a8432e03ed14a95f972b44f905279415a7`. Melebius's report #3362 describes the
hyphen usage-wrap behavior reproduced here. This workshop independently restates
the case and adds a long-token boundary hypothesis; it does not copy a backlog
or claim an upstream-approved fix.

- https://github.com/pallets/click/issues/3362
- https://github.com/pallets/click

The partial/repaired in-memory candidates and `exercises/replay.json` are authored
teaching data. Replay is not a record of real provider calls. Artificial token
usage must not be quoted as measured cost or model-quality evidence.

Official provider docs fetched 2026-11-06:

- https://developers.openai.com/api/docs/models/gpt-5.4-mini
- https://developers.openai.com/api/reference/resources/responses/methods/create
- https://platform.claude.com/docs/en/about-claude/pricing
- https://platform.claude.com/docs/en/api/messages

GitHub references:

- https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-repository-from-a-template
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows
- https://docs.github.com/en/actions/how-tos/manage-workflow-runs/disable-and-enable-workflows

Check current documentation, rates and account access before a live run.
