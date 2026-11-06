import copy

import pytest

from pr_review_workshop.contracts import read_json
from pr_review_workshop.monitor import tick
from pr_review_workshop.readiness import evaluate


def call(snapshot, policy, state=None, now=0, **kwargs):
    verdict = evaluate(snapshot, policy, snapshot["repository"], "learner")
    return tick(snapshot, verdict, state, policy, now, **kwargs)


def test_ready_stops(snapshot, policy):
    assert call(snapshot, policy)["stop_reason"] == "ready"


def test_change_only_and_stall(policy):
    snapshot = read_json("tests/fixtures/pending-check.json")
    first = call(snapshot, policy)
    second = call(snapshot, policy, first["state"], 60)
    assert first["dispatch"] and not second["dispatch"]
    snapshot["updated_at"] = "irrelevant metadata"
    third = call(snapshot, policy, second["state"], 120)
    assert not third["dispatch"]
    fourth = call(snapshot, policy, third["state"], 180)
    assert fourth["stop_reason"] == "stall" and fourth["dispatch"]


@pytest.mark.parametrize(
    ("change", "kwargs", "reason"),
    [
        ({"state": "CLOSED"}, {}, "terminal"),
        ({}, {"stop": True}, "user-stop"),
        ({}, {"budget_exhausted": True}, "budget-exhausted"),
        ({"isDraft": True}, {}, "blocked"),
    ],
)
def test_stop_conditions(policy, change, kwargs, reason):
    snapshot = read_json("tests/fixtures/pending-check.json")
    snapshot["pull_request"].update(change)
    assert call(snapshot, policy, **kwargs)["stop_reason"] == reason


def test_limits(policy):
    snapshot = read_json("tests/fixtures/pending-check.json")
    result = call(snapshot, policy)
    assert call(snapshot, policy, result["state"], 901)["stop_reason"] == "time-exhausted"
    limited = copy.deepcopy(policy)
    limited["max_cycles"] = 1
    assert call(snapshot, limited)["stop_reason"] == "cycles-exhausted"
