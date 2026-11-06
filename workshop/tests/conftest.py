import copy

import pytest

from pr_review_workshop.contracts import parse_evidence, read_json


@pytest.fixture
def snapshot():
    return copy.deepcopy(read_json("tests/fixtures/ready.json"))


@pytest.fixture
def evidence(snapshot):
    return parse_evidence(snapshot["comments"][0]["body"])


@pytest.fixture
def policy():
    return read_json("config/review-policy.json")


@pytest.fixture
def pricing():
    return read_json("config/providers.json")
