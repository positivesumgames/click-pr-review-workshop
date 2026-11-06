"""A single-run request ledger, not an account-wide spending control."""

from datetime import date
from decimal import Decimal, InvalidOperation

from .contracts import ContractError, require


def money(value):
    try:
        result = Decimal(str(value))
        require(result.is_finite() and result >= 0, "Cost must be finite and nonnegative")
        return result
    except InvalidOperation as error:
        raise ContractError("Unknown price") from error


def cost(rate, input_tokens, output_tokens):
    require(type(input_tokens) is int and input_tokens >= 0, "Unknown input usage")
    require(type(output_tokens) is int and output_tokens >= 0, "Unknown output usage")
    try:
        return (
            money(rate["input_usd_per_million"]) * input_tokens
            + money(rate["output_usd_per_million"]) * output_tokens
        ) / Decimal(1000000)
    except (KeyError, TypeError) as error:
        raise ContractError("Unknown price; no request may be sent") from error


class Budget:
    def __init__(self, config, limit=None, today=None):
        today = today or date.today()
        age = (today - date.fromisoformat(config["checked_on"])).days
        require(
            0 <= age <= config["expires_after_days"], "Refresh the pricing record before live use"
        )
        require(
            1 <= config["max_rounds"] <= 2 and 1 <= config["max_calls"] <= 8,
            "Round/call limits exceed the workshop bounds",
        )
        require(
            1 <= config["output_limit"] <= 4096 and config["input_allowance"] == 64000,
            "Unknown token allowance",
        )
        self.config = config
        self.limit = money(config["runner_budget_usd"] if limit is None else limit)
        self.reported = Decimal(0)
        self.reserved = Decimal(0)
        self.attempts = []
        self.stopped = False

    def reserve(self, rate, round_number):
        require(not self.stopped, "Usage is unresolved; this run is stopped")
        require(
            type(round_number) is int and 1 <= round_number <= self.config["max_rounds"],
            "Round limit reached",
        )
        require(len(self.attempts) < self.config["max_calls"], "Call/attempt limit reached")
        reservation = cost(rate, self.config["input_allowance"], self.config["output_limit"])
        require(
            self.reported + self.reserved + reservation <= self.limit,
            "Request would exceed the runner budget",
        )
        item = {
            "attempt": len(self.attempts) + 1,
            "provider": rate["provider"],
            "model": rate["model"],
            "round": round_number,
            "reserved_usd": str(reservation),
            "reported_usd": None,
            "status": "reserved",
        }
        self.attempts.append(item)
        self.reserved += reservation
        return item

    def settle(self, item, rate, usage):
        try:
            require(item["status"] == "reserved", "Attempt is already settled")
            actual = cost(rate, usage["input_tokens"], usage["output_tokens"])
            require(
                usage["input_tokens"] <= self.config["input_allowance"]
                and usage["output_tokens"] <= self.config["output_limit"],
                "Provider usage exceeded the reservation allowance",
            )
            require(actual <= money(item["reserved_usd"]), "Usage exceeded reservation")
            self.reserved -= money(item["reserved_usd"])
            self.reported += actual
            item.update(status="reported", reported_usd=str(actual))
        except (ContractError, KeyError, TypeError):
            self.unknown(item)
            raise ContractError(
                "Usage is unresolved; reservation retained and run stopped"
            ) from None

    def unknown(self, item):
        item["status"] = "unresolved"
        self.stopped = True

    def report(self):
        return {
            "runner_limit_usd": str(self.limit),
            "reserved_usd": str(self.reserved),
            "reported_usd": str(self.reported),
            "attempts": self.attempts,
            "stopped": self.stopped,
            "account_wide_cap": False,
        }


def estimate(config):
    return {
        "basis": "Conservative allowances, not measured usage; uncached standard first-party rates",
        "checked_on": config["checked_on"],
        "four_call_reservation_usd": str(
            sum(
                cost(r, config["input_allowance"], config["output_limit"]) * 2
                for r in config["providers"]
            )
        ),
        "eight_call_ceiling_usd": str(
            sum(
                cost(r, config["input_allowance"], config["output_limit"]) * 4
                for r in config["providers"]
            )
        ),
        "account_wide_cap": False,
    }
