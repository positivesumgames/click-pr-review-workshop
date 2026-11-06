import copy

import pytest

from pr_review_workshop.contracts import read_json, render_evidence
from pr_review_workshop.readiness import evaluate


def verdict(snapshot, policy):
    return evaluate(snapshot, policy, snapshot["repository"], "learner")


def test_clean(snapshot, policy):
    result = verdict(snapshot, policy)
    assert result.state == "ready" and result.exit_code == 0
    assert result.to_dict()["merge_authorized"] is False


@pytest.mark.parametrize(
    ("filename", "state", "code"),
    [
        ("stale-review", "blocked", 20),
        ("pending-check", "running", 10),
    ],
)
def test_recorded_scenarios(filename, state, code, policy):
    result = verdict(read_json(f"tests/fixtures/{filename}.json"), policy)
    assert (result.state, result.exit_code) == (state, code)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(checks=[]),
        lambda s: s.update(comments=[]),
        lambda s: s["pull_request"].update(isDraft=True),
        lambda s: s["pull_request"].update(mergeable="CONFLICTING"),
        lambda s: s["pull_request"].update(reviewDecision="CHANGES_REQUESTED"),
        lambda s: s.update(threads=[{"isResolved": False}]),
        lambda s: s["checks"][0].update(conclusion="failure"),
        lambda s: s["checks"][0].update(conclusion="skipped"),
        lambda s: s["checks"][0].update(headSha="c" * 40),
        lambda s: s.update(changed_files=[".github/workflows/pr-readiness.yml"]),
    ],
)
def test_known_blockers(snapshot, policy, mutation):
    mutation(snapshot)
    assert verdict(snapshot, policy).state == "blocked"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda s: s.update(complete=False),
        lambda s: s.update(publisher_can_write=False),
        lambda s: s.pop("threads"),
        lambda s: s.update(threads=[{}]),
        lambda s: s["checks"][0].update(status="mystery"),
        lambda s: s["checks"][0].update(conclusion="mystery"),
        lambda s: s["checks"][0].update(trusted_workflow=False),
        lambda s: s["pull_request"].update(mergeable=None),
        lambda s: s["pull_request"].update(isDraft="false"),
        lambda s: s["pull_request"].update(headRepository={"nameWithOwner": "pallets/click"}),
        lambda s: s.update(intent="Intent changed after review"),
    ],
)
def test_unknown_or_untrusted(snapshot, policy, mutation):
    mutation(snapshot)
    assert verdict(snapshot, policy).state == "environment-error"


def test_forged_publisher_ignored(snapshot, policy):
    snapshot["comments"][0]["user"]["login"] = "stranger"
    assert verdict(snapshot, policy).state == "blocked"


def test_new_rerun_supersedes_old_success(snapshot, policy):
    newer = copy.deepcopy(snapshot["checks"][0])
    newer.update(attempt=2, status="in_progress", conclusion=None)
    snapshot["checks"].append(newer)
    assert verdict(snapshot, policy).state == "running"
    newer.update(status="completed", conclusion="failure")
    assert verdict(snapshot, policy).state == "blocked"


def test_missing_lens(snapshot, evidence, policy):
    evidence["reviews"].pop()
    snapshot["comments"][0]["body"] = render_evidence(evidence)
    assert verdict(snapshot, policy).state == "blocked"


def test_unknown_reviewer(snapshot, evidence, policy):
    evidence["reviews"][0]["status"] = "unavailable"
    snapshot["comments"][0]["body"] = render_evidence(evidence)
    assert verdict(snapshot, policy).state == "blocked"


def test_latest_bad_comment_cannot_fall_back_to_green(snapshot, policy):
    bad = copy.deepcopy(snapshot["comments"][0])
    bad.update(id=2, body="<!-- workshop-review:v1 -->\nmalformed")
    snapshot["comments"].append(bad)
    assert verdict(snapshot, policy).state == "environment-error"


def test_source_sha_is_not_live_head(snapshot, evidence, policy):
    evidence["reviews"][0]["head_sha"] = read_json("workshop-manifest.json")["source_sha"]
    snapshot["comments"][0]["body"] = render_evidence(evidence)
    assert verdict(snapshot, policy).state != "ready"


def test_finding_cannot_disappear_in_latest_stamp(snapshot, evidence, policy):
    original = copy.deepcopy(evidence)
    original["reviews"][0]["findings"].append(
        {
            "id": "F1",
            "severity": "high",
            "category": "correctness",
            "claim": "Still broken",
            "location": "formatting.py:65",
            "reproduction": "long-token test",
        }
    )
    snapshot["comments"] = [
        {"id": 1, "user": {"login": "learner"}, "body": render_evidence(original)},
        {"id": 2, "user": {"login": "learner"}, "body": render_evidence(evidence)},
    ]
    assert verdict(snapshot, policy).state == "environment-error"
