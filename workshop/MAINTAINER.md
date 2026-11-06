# Monthly refresh command and reminder

This is maintainer work outside the 90-minute workshop. Keep the same independent
repository; do not re-fork monthly or mirror/force-sync over curriculum changes.
Learners generate snapshots from tested main, not from unreviewed refresh branches.

## Reminder

`monthly-maintenance.yml` runs on the first day of each month at 16:17 UTC,
only in `positivesumgames/click-pr-review-workshop`. It has contents-read and
issues-write permissions, not branch/status write. It creates one outstanding
maintenance issue mentioning `positivesumgames`; it neither fetches upstream
nor opens/merges a refresh PR. Existing open reminders are not duplicated.

GitHub notifications depend on subscription/email settings. Scheduled runs can
be delayed, and public schedules can disable after 60 days without repository
activity. This is not guaranteed email delivery. Re-enable the workflow in
Actions if disabled. To issue a reminder manually:

```bash
gh workflow run monthly-maintenance.yml --repo positivesumgames/click-pr-review-workshop --ref main
```

Close the reminder after validation/publication or explain a deferral. Review
security/dependency changes sooner rather than waiting for the calendar.

## Prepare an update manually

Use a clean maintainer checkout on main. Its `origin` must be the maintainer
repository; `upstream` must be `https://github.com/pallets/click.git`.
The imported Git history preserves the common ancestry needed for later merges.
For a fresh maintainer clone, configure the read-only upstream once from its root:

```bash
git remote add upstream https://github.com/pallets/click.git
git remote set-url --push upstream no-push://pallets/click
```

If upstream already exists, inspect it rather than adding/replacing it blindly.
The invalid push transport prevents accidental upstream pushes; fetches still work.

```bash
cd workshop
.venv/bin/python scripts/refresh_upstream.py --repo positivesumgames/click-pr-review-workshop
```

The helper checks target, origin, clean state and branch uniqueness; fetches
upstream; creates `maintenance/click-YYYY-MM-DD`; and prepares a noncommitted
merge. It does not commit, push, change main or create a PR. If conflicts occur,
inspect them on that branch. Resolve only after understanding workshop effects,
or use `git merge --abort` to abandon this pending merge.

Upstream may add/change `.github` files. Keep its release/scheduled workflows
inactive in this teaching repository: move/reconcile them in `.upstream/github/workflows`,
and retain only the tested workshop workflows under `.github/workflows`.
Do not activate an upstream upload or release job while resolving the merge.

## Validate before publication

From `workshop/` on the refresh branch:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python scripts/validate_workshop.py --run
.venv/bin/python scripts/container_preflight.py
git diff --check
```

Also run the upstream Click test suite with its documented dependencies. If an
upstream fix removes #3362's baseline failure, do not release broken expected-fail
labs. Replace the case or explicitly update a labeled teaching fixture and its
source manifest; rerun before/partial/repair checkpoints. Update workshop version,
source SHA, dependencies, licenses and pricing record. Reprovision/test the
container when backend dependencies change.

Review the staged merge and curriculum changes. Commit and push the refresh
branch using your normal reviewed workflow, then open an internal refresh PR:

```bash
gh pr create --repo positivesumgames/click-pr-review-workshop --base main --head maintenance/click-YYYY-MM-DD
```

Control-code changes deliberately block automatic readiness and require a
maintainer ruling; do not disable the policy to self-approve them.
Release main/tag only after review, preferably between cohorts. The template
generates default main, not an arbitrary tag. Existing learner repositories
stay unchanged; publish an upgrade notice, not an automatic synchronization.

Local disposable-repository tests prove ancestry/curriculum preservation and
refusal boundaries. They do not prove every future upstream merge is conflict-free.
