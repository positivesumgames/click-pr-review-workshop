"""All GitHub access uses gh. Privileged callers run only trusted base code."""

import json
import os
import subprocess

from .contracts import ContractError, packet, reconcile, render_evidence, require, sha, target
from .readiness import evaluate


def gh(*args, raw=False, stdin=None):
    result = subprocess.run(["gh", *args], input=stdin, text=True, capture_output=True, timeout=45)
    require(result.returncode == 0, "GitHub read/write failed; check access and retry explicitly")
    return result.stdout if raw else json.loads(result.stdout)


def api_pages(path):
    pages = gh("api", "--paginate", "--slurp", path)
    require(isinstance(pages, list), "Invalid GitHub pagination response")
    return [item for page in pages for item in page]


QUERY = """
query($owner:String!, $name:String!, $number:Int!) {
  repository(owner:$owner, name:$name) {
    pullRequest(number:$number) {
      number state isDraft mergeable reviewDecision title body baseRefName baseRefOid headRefOid
      headRepository { nameWithOwner } baseRepository { nameWithOwner }
      reviewThreads(first:100) { nodes { isResolved } pageInfo { hasNextPage } }
    }
  }
}
"""


def collect(repo, number, allowed_repo, publisher):
    target(repo, allowed_repo)
    require(type(number) is int and number > 0, "Invalid PR number")
    owner, name = repo.split("/")
    response = gh(
        "api",
        "graphql",
        "-f",
        f"query={QUERY}",
        "-f",
        f"owner={owner}",
        "-f",
        f"name={name}",
        "-F",
        f"number={number}",
    )
    require(not response.get("errors"), "GraphQL returned incomplete PR data")
    pr = response["data"]["repository"]["pullRequest"]
    require(pr is not None, "PR does not exist")
    require(
        pr["headRepository"]
        and pr["baseRepository"]
        and pr["headRepository"]["nameWithOwner"] == repo
        and pr["baseRepository"]["nameWithOwner"] == repo,
        "Cross-repository PR is unsupported",
    )
    require(
        not pr["reviewThreads"]["pageInfo"]["hasNextPage"],
        "More than 100 review threads; stop for a maintainer",
    )
    threads = pr.pop("reviewThreads")["nodes"]
    intent = pr.pop("title") + "\n" + pr.pop("body")
    pr["reviewDecision"] = pr["reviewDecision"] or ""
    head = sha(pr["headRefOid"])
    diff = gh("pr", "diff", str(number), "--repo", repo, raw=True)
    require(len(diff) <= 48000, "PR is too large for this workshop")
    files = api_pages(f"repos/{repo}/pulls/{number}/files?per_page=100")
    changed = sorted(
        {path for f in files for path in (f["filename"], f.get("previous_filename")) if path}
    )
    comments = api_pages(f"repos/{repo}/issues/{number}/comments?per_page=100")
    workflow = gh("api", f"repos/{repo}/actions/workflows/workshop-tests.yml")
    runs = gh(
        "api",
        "--paginate",
        "--slurp",
        f"repos/{repo}/actions/workflows/{workflow['id']}/runs"
        f"?event=pull_request&head_sha={head}&per_page=100",
    )
    checks = []
    for page in runs:
        for run in page["workflow_runs"]:
            if run["head_sha"] != head or run["head_repository"]["full_name"] != repo:
                continue
            require(run["workflow_id"] == workflow["id"], "Workflow identity mismatch")
            checks.append(
                {
                    "name": "Workshop Tests",
                    "id": run["id"],
                    "attempt": run["run_attempt"],
                    "headSha": head,
                    "status": run["status"],
                    "conclusion": run["conclusion"],
                    "trusted_workflow": True,
                }
            )
    permission = (
        gh("api", f"repos/{repo}/collaborators/{publisher}/permission") if publisher else {}
    )
    return {
        "schema_version": 1,
        "complete": True,
        "repository": repo,
        "pull_request": pr,
        "intent": intent,
        "diff": diff,
        "changed_files": changed,
        "checks": checks,
        "comments": comments,
        "threads": threads,
        "publisher_can_write": permission.get("permission") in {"admin", "maintain", "write"},
    }


def source_packet(snapshot):
    pr = snapshot["pull_request"]
    return packet(
        snapshot["repository"],
        pr["number"],
        pr["baseRefOid"],
        pr["headRefOid"],
        snapshot["intent"],
        snapshot["diff"],
    )


def publish(repo, number, allowed_repo, publisher, evidence, policy):
    snapshot = collect(repo, number, allowed_repo, publisher)
    source = source_packet(snapshot)
    require(snapshot["publisher_can_write"], "Publisher does not have write permission")
    require(gh("api", "user")["login"] == publisher, "Current GitHub account is not the publisher")
    require(evidence["packet"] == source, "PR changed since review; rerun the reviewers")
    reconcile(
        evidence["reviews"], evidence["dispositions"], source, policy["required_lenses"], publisher
    )
    require(evidence["publisher"] == publisher, "Publisher mismatch")
    body = render_evidence(evidence)
    require(len(body) <= 65000, "Evidence exceeds GitHub comment size")
    gh("pr", "comment", str(number), "--repo", repo, "--body-file", "-", raw=True, stdin=body)
    return {"published": True, "head_sha": source["head_sha"], "merge_authorized": False}


def status(repo, number, allowed_repo, publisher, policy):
    snapshot = collect(repo, number, allowed_repo, publisher)
    verdict = evaluate(snapshot, policy, allowed_repo, publisher)
    head = snapshot["pull_request"]["headRefOid"]
    latest = gh("api", f"repos/{repo}/pulls/{number}")["head"]["sha"]
    if latest != head:
        return {"skipped": "Head changed; this run cannot publish a current verdict"}
    mapped = {
        "ready": "success",
        "running": "pending",
        "blocked": "failure",
        "environment-error": "error",
    }
    gh(
        "api",
        "--method",
        "POST",
        f"repos/{repo}/statuses/{head}",
        "-f",
        "context=PR Readiness",
        "-f",
        f"state={mapped[verdict.state]}",
        "-f",
        f"description={'; '.join(verdict.reasons)[:140]}",
    )
    return verdict.to_dict()


def event_prs(event, repo):
    require(event.get("repository", {}).get("full_name") == repo, "Event repository mismatch")
    if "pull_request" in event:
        return [event["pull_request"]["number"]]
    if event.get("issue", {}).get("pull_request"):
        return [event["issue"]["number"]]
    if "workflow_run" in event:
        run = event["workflow_run"]
        require(run["event"] == "pull_request", "Only pull_request test runs are aggregated")
        require(run["head_repository"]["full_name"] == repo, "Foreign run repository")
        return [pr["number"] for pr in run["pull_requests"]]
    number = event.get("inputs", {}).get("pr")
    require(
        isinstance(number, str) and number.isdigit() and int(number) > 0,
        "Manual readiness refresh needs a PR number",
    )
    return [int(number)]


def action(policy):
    repo = os.environ["GITHUB_REPOSITORY"]
    with open(os.environ["GITHUB_EVENT_PATH"]) as file:
        event = json.load(file)
    publisher = os.environ.get("WORKSHOP_EVIDENCE_PUBLISHER", "")
    results = []
    for number in event_prs(event, repo):
        try:
            results.append(status(repo, number, repo, publisher, policy))
        except (ContractError, KeyError, ValueError, subprocess.TimeoutExpired):
            # Never leave a previous success standing after an unreadable refresh.
            head = sha(gh("api", f"repos/{repo}/pulls/{number}")["head"]["sha"])
            gh(
                "api",
                "--method",
                "POST",
                f"repos/{repo}/statuses/{head}",
                "-f",
                "context=PR Readiness",
                "-f",
                "state=error",
                "-f",
                "description=Readiness is unreadable; check publisher/access and rerun",
            )
            results.append({"state": "environment-error", "head_sha": head})
    return results
