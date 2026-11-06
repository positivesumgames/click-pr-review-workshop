import pytest

from pr_review_workshop.contracts import ContractError, target
from pr_review_workshop.maintenance import MAINTAINER, REMINDER_MARKER, TITLE, reminder


@pytest.mark.parametrize("repo", ["pallets/click", "kirodotdev/KiroCrew", "another/repository"])
def test_unintended_target_refused(repo):
    with pytest.raises(ContractError):
        target(repo, "learner/click-pr-review-workshop")


def test_reminder_deduplicates():
    calls = []
    result = reminder(
        MAINTAINER,
        list_issues=lambda _: [
            {
                "number": 12,
                "body": REMINDER_MARKER,
                "title": TITLE,
                "user": {"login": "github-actions[bot]"},
            }
        ],
        call=lambda *args: calls.append(args),
    )
    assert not result["created"] and not calls


def test_reminder_only_mutates_approved_repo():
    calls = []

    def call(*args):
        calls.append(args)
        return {"number": 13}

    assert reminder(MAINTAINER, list_issues=lambda _: [], call=call)["created"]
    assert calls[0][0:3] == ("api", "--method", "POST")
    assert calls[0][3] == f"repos/{MAINTAINER}/issues"
    with pytest.raises(ContractError):
        reminder("learner/click-pr-review-workshop", list_issues=lambda _: [], call=call)
    assert len(calls) == 1
