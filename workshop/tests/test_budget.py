from datetime import date
from decimal import Decimal

import pytest

from pr_review_workshop.budget import Budget, cost, estimate
from pr_review_workshop.contracts import ContractError


def make(pricing, limit=None):
    return Budget(pricing, limit, today=date(2026, 11, 6))


def test_reservation_before_dispatch(pricing):
    budget = make(pricing)
    rate = pricing["providers"][0]
    item = budget.reserve(rate, 1)
    assert item["status"] == "reserved" and budget.reserved > 0
    budget.settle(item, rate, {"input_tokens": 1000, "output_tokens": 200})
    assert budget.reserved == 0 and budget.reported == cost(rate, 1000, 200)


def test_refusal_before_sending(pricing):
    budget = make(pricing, "0.01")
    with pytest.raises(ContractError, match="exceed"):
        budget.reserve(pricing["providers"][0], 1)
    assert not budget.attempts and budget.reserved == 0


@pytest.mark.parametrize(
    "usage",
    [{}, {"input_tokens": None, "output_tokens": 1}, {"input_tokens": 1, "output_tokens": 4097}],
)
def test_unknown_usage_retains_reservation(pricing, usage):
    budget = make(pricing)
    rate = pricing["providers"][0]
    item = budget.reserve(rate, 1)
    reserved = budget.reserved
    with pytest.raises(ContractError, match="unresolved"):
        budget.settle(item, rate, usage)
    assert budget.stopped and budget.reserved == reserved
    with pytest.raises(ContractError):
        budget.reserve(rate, 1)


def test_every_attempt_counts(pricing):
    budget = make(pricing)
    rate = pricing["providers"][0]
    for _ in range(8):
        item = budget.reserve(rate, 1)
        budget.settle(item, rate, {"input_tokens": 0, "output_tokens": 0})
    with pytest.raises(ContractError, match="attempt limit"):
        budget.reserve(rate, 1)
    assert len(budget.attempts) == 8


def test_unknown_prices_and_round_limit(pricing):
    budget = make(pricing)
    with pytest.raises(ContractError):
        budget.reserve({"provider": "unknown"}, 1)
    with pytest.raises(ContractError):
        budget.reserve(pricing["providers"][0], 3)


def test_expired_rate_record(pricing):
    with pytest.raises(ContractError, match="pricing"):
        Budget(pricing, today=date(2027, 1, 1))


def test_estimate_is_not_account_cap(pricing):
    value = estimate(pricing)
    assert Decimal(value["eight_call_ceiling_usd"]) < 5
    assert value["account_wide_cap"] is False
