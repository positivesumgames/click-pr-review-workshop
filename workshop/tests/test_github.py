import copy

import pytest

from pr_review_workshop import github
from pr_review_workshop.contracts import ContractError


def test_collection_verifies_workflow_identity_and_pagination(monkeypatch, snapshot):
    pr = copy.deepcopy(snapshot["pull_request"])
    pr.update(
        title="Fix wrapping",
        body="Intent",
        reviewThreads={
            "nodes": [],
            "pageInfo": {"hasNextPage": False},
        },
    )
    calls = []

    def call(*args, raw=False, stdin=None):
        calls.append(args)
        if "graphql" in args:
            return {"data": {"repository": {"pullRequest": pr}}}
        if args[0] == "pr":
            return snapshot["diff"]
        path = args[-1]
        if "/files?" in path:
            return [[{"filename": "new-name", "previous_filename": ".github/old-file"}]]
        if "/comments?" in path:
            return [snapshot["comments"]]
        if "/runs?" in path:
            return [
                {
                    "workflow_runs": [
                        {
                            "head_sha": snapshot["pull_request"]["headRefOid"],
                            "head_repository": {"full_name": snapshot["repository"]},
                            "workflow_id": 23,
                            "id": 12,
                            "run_attempt": 2,
                            "status": "in_progress",
                            "conclusion": None,
                        }
                    ]
                }
            ]
        if "/permission" in path:
            return {"permission": "write"}
        if "/workflows/" in path:
            return {"id": 23}
        raise AssertionError(args)

    monkeypatch.setattr(github, "gh", call)
    result = github.collect(snapshot["repository"], 1, snapshot["repository"], "learner")
    assert result["complete"] and result["checks"][0]["attempt"] == 2
    assert ".github/old-file" in result["changed_files"]
    assert any("--paginate" in c for c in calls)


def test_publisher_account_and_changed_head_guard(monkeypatch, snapshot, evidence, policy):
    monkeypatch.setattr(github, "collect", lambda *args: snapshot)
    calls = []

    def call(*args, **kwargs):
        calls.append(args)
        if args[:2] == ("api", "user"):
            return {"login": "someone-else"}
        return {"head": {"sha": "c" * 40}}

    monkeypatch.setattr(github, "gh", call)
    with pytest.raises(ContractError, match="account"):
        github.publish(
            snapshot["repository"], 1, snapshot["repository"], "learner", evidence, policy
        )
    assert github.status(snapshot["repository"], 1, snapshot["repository"], "learner", policy)[
        "skipped"
    ]
    assert not any("--method" in c for c in calls)


def test_dispatch_and_foreign_event_guard():
    repo = "learner/click-pr-review-workshop"
    event = {"repository": {"full_name": repo}, "inputs": {"pr": "12"}}
    assert github.event_prs(event, repo) == [12]
    with pytest.raises(ContractError):
        github.event_prs(event, "pallets/click")


def test_unreadable_refresh_replaces_green_with_error(monkeypatch, policy):
    repo = "learner/click-pr-review-workshop"
    monkeypatch.setenv("GITHUB_REPOSITORY", repo)
    monkeypatch.setenv("GITHUB_EVENT_PATH", "tests/fixtures/action-event.json")
    monkeypatch.setattr(
        github, "status", lambda *args: (_ for _ in ()).throw(ContractError("unknown"))
    )
    calls = []

    def call(*args):
        calls.append(args)
        return {"head": {"sha": "a" * 40}}

    monkeypatch.setattr(github, "gh", call)
    assert github.action(policy)[0]["state"] == "environment-error"
    assert "state=error" in calls[-1]
