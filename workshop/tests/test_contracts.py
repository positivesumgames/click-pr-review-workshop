import pytest

from pr_review_workshop.contracts import ContractError, reconcile, validate_packet


def run(evidence, policy):
    return reconcile(
        evidence["reviews"],
        evidence["dispositions"],
        evidence["packet"],
        policy["required_lenses"],
        "learner",
    )


def finding(evidence, category="correctness"):
    evidence["reviews"][0]["findings"].append(
        {
            "id": "F1",
            "severity": "high",
            "category": category,
            "claim": "A reachable token splits",
            "location": "formatting.py:65",
            "reproduction": "Test a long token at width 30",
        }
    )


def disposition(evidence, outcome):
    evidence["dispositions"] = [
        {
            "finding": "correctness:F1",
            "outcome": outcome,
            "head_sha": evidence["packet"]["head_sha"],
            "decided_by": "learner",
            "evidence": "Regression test output and exact candidate diff inspected",
        }
    ]


@pytest.mark.parametrize("outcome", ["fixed", "rebutted"])
def test_visible_disposition(evidence, policy, outcome):
    finding(evidence)
    disposition(evidence, outcome)
    assert run(evidence, policy)["dispositions"][0]["outcome"] == outcome


def test_unanswered_finding(evidence, policy):
    finding(evidence)
    with pytest.raises(ContractError, match="exactly one"):
        run(evidence, policy)


def test_needs_human_decision(evidence, policy):
    finding(evidence)
    disposition(evidence, "needs-a-decision")
    with pytest.raises(ContractError, match="Human decision"):
        run(evidence, policy)


def test_duplicate_disposition(evidence, policy):
    finding(evidence)
    disposition(evidence, "fixed")
    evidence["dispositions"] *= 2
    with pytest.raises(ContractError, match="duplicate"):
        run(evidence, policy)


def test_deferred_requires_owner_local_issue_due_and_acceptance(evidence, policy):
    finding(evidence)
    disposition(evidence, "accepted-and-deferred")
    with pytest.raises(ContractError):
        run(evidence, policy)
    evidence["dispositions"][0].update(
        owner="learner",
        accepted_by="learner",
        due="2026-12-01",
        issue="https://github.com/learner/click-pr-review-workshop/issues/2",
    )
    assert run(evidence, policy)
    evidence["reviews"][0]["findings"][0]["category"] = "security"
    with pytest.raises(ContractError, match="cannot converge"):
        run(evidence, policy)


def test_same_run_is_not_independent(evidence, policy):
    evidence["reviews"][1]["run_id"] = evidence["reviews"][0]["run_id"]
    with pytest.raises(ContractError, match="same run"):
        run(evidence, policy)


def test_packet_tampering(evidence):
    evidence["packet"]["diff"] += "unreviewed"
    with pytest.raises(ContractError):
        validate_packet(evidence["packet"])
