# Prework — outside the timed session

Audience: developers comfortable with Git, GitHub Actions and agentic coding,
but new to Crew. Use Python 3.12, Git, `gh`, a GitHub account and an editor.
Allow 20–30 minutes for repository/tool setup; Crew backend login can take longer.
The 60/90-minute timing assumes prework is complete and needs a human pilot.

## Get your own repository

Open `positivesumgames/click-pr-review-workshop` and choose **Use this template**.
Generate from the default branch only, not all branches. Template generation
creates fresh history; create exercise branches from your own new main.
Do not fork Click, copy issues en masse, or open practice PRs against upstream.
Existing learner repositories are snapshots and do not auto-sync.

After creation, inspect the destination with `gh repo view OWNER/NAME`; clone that
exact repository with `gh repo clone OWNER/NAME`. Set the learner-specific shell
variable below to that repository, not the maintainer repository:

```bash
export WORKSHOP_REPO="YOUR-LOGIN/YOUR-WORKSHOP-REPOSITORY"
gh repo view "$WORKSHOP_REPO" --json nameWithOwner,isFork,isTemplate,defaultBranchRef
gh variable set WORKSHOP_EVIDENCE_PUBLISHER --repo "$WORKSHOP_REPO" --body YOUR-LOGIN
cd workshop
python3.12 -m venv .venv
mkdir -p .work/tmp .work/pip
TMPDIR="$PWD/.work/tmp" PIP_CACHE_DIR="$PWD/.work/pip" .venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest -q
```

Verify main is the default branch and this is your repository. These commands
need your GitHub permissions; an offline fixture is not a live generation test.
Evidence publication is trusted to the configured publisher with write permission,
not to an arbitrary comment or PR body. This is an educational attestation,
not cryptographic proof of independent reviewer execution.

For the authoring workspace only, obtain the independent source copy:

```bash
git clone https://github.com/pallets/click.git .work/click-source
git -C .work/click-source switch --detach 8abb77a8432e03ed14a95f972b44f905279415a7
```

Do not repeat these commands in the published template; it already contains Click.

## Recommended agent path and isolation

Use `.kiro/skills/workshop-prepare-pr`, not the installed `kirocrew-prepare-pr`.
Do not overwrite installed skills, reconfigure global Crew, reuse an active
gateway, or mount your home, credentials, Crew data or Docker socket.

For live Crew, provision a fresh Crew runtime and its authenticated backend
inside a disposable container, following the current official Crew installation
guide. Pin Crew to the source version in `workshop-manifest.json`. Install/login
only inside that container, never on an existing host setup. The supplied
`container/compose.yml` is the boundary recipe, not a pre-authenticated Crew image.
It publishes no ports and exposes only this workshop copy read-only.
Do not broaden mounts if backend login fails; use the manual/replay path.

```bash
.venv/bin/python scripts/container_preflight.py
docker compose -f container/compose.yml build
docker compose -f container/compose.yml run --rm review
```

Docker is needed only for live runs. Inspect the resolved mounts, non-root user,
read-only root, capabilities and temporary state before proceeding.
The base image supports the optional tool-free provider CLI; Crew/backend
provisioning remains an explicit prework step, not an automatic host install.
No container engine means live Crew remains unverified, not permission to use
your active setup. Two human reviewers can use the same review schema.

## Optional provider prework

The advanced replay needs no keys. For live use, separately approve both exact
models in `config/providers.json` and a runner limit before sending requests.
The supplied rate record expires after 30 days; check official rates and account
access, then update it deliberately. Do not treat a listed model as entitlement.

Enter approved keys interactively inside the disposable container. Do not put
keys in command examples, recorded notes, source files, arguments or transcripts.
Only `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` for this run are needed; do not mount
an unrelated credential directory. Start in `/state`, copy the workshop files to
`/state/workshop` (ordinary copies, not links), and run from that writable copy.
The live CLI requires the container marker and `WORKSHOP_ISOLATED=1`.

## Check before the clock starts

Explain where your PR will go, identify the installed skill you must not change,
run the reference suite, and confirm whether you are using replay or isolated
live reviewers. If any of these is unclear, use offline mode for this session.
