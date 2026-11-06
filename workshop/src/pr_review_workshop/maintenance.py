"""Maintainer-only helper. No auto-merge, force-sync, or scheduled source fetching."""

import subprocess
from datetime import date
from pathlib import Path

from .contracts import require, target
from .github import api_pages, gh

MAINTAINER = "positivesumgames/click-pr-review-workshop"
TITLE = "[Maintenance] Refresh the Click PR-review workshop"
REMINDER_MARKER = "<!-- workshop-monthly-maintenance:v1 -->"


def reminder(repo, list_issues=api_pages, call=gh):
    target(repo, MAINTAINER)
    issues = list_issues(f"repos/{repo}/issues?state=open&per_page=100")
    existing = [
        i
        for i in issues
        if not i.get("pull_request")
        and i.get("title") == TITLE
        and i.get("user", {}).get("login") in {"positivesumgames", "github-actions[bot]"}
        and REMINDER_MARKER in (i.get("body") or "")
    ]
    if existing:
        return {"created": False, "issue": existing[0]["number"], "reason": "Outstanding reminder"}
    body = f"""{REMINDER_MARKER}
@positivesumgames Monthly maintenance reminder; no source update has been performed.

Run the refresh helper from a clean maintainer checkout:

    cd workshop
    .venv/bin/python scripts/refresh_upstream.py --repo {MAINTAINER}

Follow workshop/MAINTAINER.md: resolve conflicts, verify baseline and repaired cases,
run the full suite and learner commands, update source/version/pricing metadata, and
open a review PR into this repository. Release between cohorts only after approval.
Close this reminder after the refresh or record why it is deferred.
Never force-sync main, re-fork, auto-merge, or update learner repositories.
"""
    issue = call(
        "api",
        "--method",
        "POST",
        f"repos/{repo}/issues",
        "-f",
        f"title={TITLE}",
        "-f",
        f"body={body}",
    )
    return {"created": True, "issue": issue["number"]}


def git(root, *args):
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
        capture_output=True,
        text=True,
        timeout=60,
    )
    require(result.returncode == 0, f"Git operation failed: {args[0]}; inspect the checkout")
    return result.stdout.strip()


def remote_repo(url):
    prefixes = ("https://github.com/", "git@github.com:")
    for prefix in prefixes:
        if url.startswith(prefix):
            return url[len(prefix) :].removesuffix(".git").rstrip("/")
    return None


def refresh(root, repo, branch=None, *, fetch=True):
    root = Path(root).resolve()
    target(repo, MAINTAINER)
    require(
        remote_repo(git(root, "remote", "get-url", "origin")) == repo, "Wrong maintainer origin"
    )
    require(git(root, "status", "--porcelain") == "", "Refresh requires a clean worktree")
    require(git(root, "branch", "--show-current") == "main", "Start the refresh from main")
    require(
        git(root, "remote", "get-url", "upstream") == "https://github.com/pallets/click.git",
        "Upstream must be the read-only Click HTTPS remote",
    )
    branch = branch or f"maintenance/click-{date.today().isoformat()}"
    require(
        branch.startswith("maintenance/") and not any(c in branch for c in " ~^:?*[\\"),
        "Invalid refresh branch",
    )
    existing = subprocess.run(
        ["git", "-C", str(root), "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        capture_output=True,
    )
    require(
        existing.returncode == 1, "Refresh branch already exists; inspect it instead of overwriting"
    )
    if fetch:
        git(root, "fetch", "upstream", "main")
    before = git(root, "rev-parse", "main")
    git(root, "switch", "-c", branch)
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(root),
            "merge",
            "--no-commit",
            "--no-ff",
            "upstream/main",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    require(git(root, "rev-parse", "main") == before, "Main unexpectedly changed")
    return {
        "branch": branch,
        "main_unchanged": True,
        "merge_prepared": result.returncode == 0,
        "next": "Review merge/conflicts, validate all labs, update manifest; nothing was pushed",
        "merge_authorized": False,
    }
