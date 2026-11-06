from datetime import date

import pytest

from pr_review_workshop.budget import Budget
from pr_review_workshop.contracts import ContractError, read_json
from pr_review_workshop.providers import (
    live_request,
    replay_request,
    request_body,
    require_container,
    run_pair,
)


def test_first_passes_are_independent_and_challenges_separate(evidence, policy, pricing):
    seen = []
    budget = Budget(pricing, today=date(2026, 11, 6))

    def request(rate, payload, limit):
        assert budget.attempts[-1]["status"] == "reserved"
        seen.append(payload)
        return {
            "content": {"findings": []},
            "usage": {"input_tokens": 200, "output_tokens": 50},
            "served_model": rate["model"],
            "request_id": str(len(seen)),
        }

    result = run_pair(evidence["packet"], policy, pricing, budget, request)
    assert "peer_review" not in seen[0] and "peer_review" not in seen[1]
    assert seen[2]["peer_review"] == result["independent"][1]
    assert seen[3]["peer_review"] == result["independent"][0]
    assert len(result["cross_critique"]) == 2
    assert {r["head_sha"] for r in result["independent"] + result["cross_critique"]} == {
        evidence["packet"]["head_sha"]
    }


def test_replay_schema(evidence, policy, pricing):
    budget = Budget(pricing, today=date(2026, 11, 6))
    result = run_pair(
        evidence["packet"],
        policy,
        pricing,
        budget,
        replay_request(read_json("exercises/replay.json")),
    )
    assert len(result["independent"][1]["findings"]) == 2
    assert len(budget.attempts) == 4


def test_unknown_response_stops_without_retry(evidence, policy, pricing):
    budget = Budget(pricing, today=date(2026, 11, 6))
    calls = []

    def request(*args):
        calls.append(args)
        return {}

    with pytest.raises(ContractError):
        run_pair(evidence["packet"], policy, pricing, budget, request)
    assert len(calls) == 1 and budget.stopped and budget.reserved > 0


def test_same_provider_rejected(evidence, policy, pricing):
    pricing["providers"][1]["provider"] = "openai"
    with pytest.raises(ContractError, match="distinct"):
        run_pair(
            evidence["packet"],
            policy,
            pricing,
            Budget(pricing, today=date(2026, 11, 6)),
            lambda *args: {},
        )


@pytest.mark.parametrize("provider_index", [0, 1])
def test_actual_adapter_request_and_usage(monkeypatch, pricing, provider_index):
    rate = pricing["providers"][provider_index]
    monkeypatch.setenv("OPENAI_API_KEY", "test-only-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-only-key")
    seen = []

    def send(url, headers, body):
        seen.append((url, headers, body))
        usage = {"input_tokens": 100, "output_tokens": 20}
        if rate["provider"] == "openai":
            return {
                "id": "r1",
                "model": rate["model"],
                "status": "completed",
                "usage": usage,
                "output": [
                    {
                        "type": "message",
                        "content": [{"type": "output_text", "text": '{"findings":[]}'}],
                    }
                ],
            }
        return {
            "id": "r2",
            "model": rate["model"],
            "stop_reason": "end_turn",
            "usage": usage,
            "content": [{"type": "text", "text": '{"findings":[]}'}],
        }

    result = live_request(rate, {"packet": "test"}, 100, send=send)
    assert result["content"] == {"findings": []} and result["usage"]["input_tokens"] == 100
    assert "test-only-key" not in str(seen[0][2])
    assert not seen[0][2].get("tools")


def test_live_host_refused():
    with pytest.raises(ContractError, match="container"):
        require_container()


def test_large_input_refused(pricing):
    with pytest.raises(ContractError, match="allowance"):
        request_body(pricing["providers"][0], {"diff": "X" * 48001}, 4096)
