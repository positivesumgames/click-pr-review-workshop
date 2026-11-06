"""Validate untrusted review data before it can influence readiness."""

import hashlib
import json
import re
from pathlib import Path

MARKER = "<!-- workshop-review:v1 -->"
SHA = re.compile(r"[0-9a-f]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


class ContractError(ValueError):
    """Input is missing, ambiguous, stale, or outside the workshop boundary."""


def require(condition, message):
    if not condition:
        raise ContractError(message)


def text(value, label, limit=8000):
    require(isinstance(value, str) and 0 < len(value.strip()) <= limit, f"Invalid {label}")
    return value


def sha(value):
    require(isinstance(value, str) and SHA.fullmatch(value), "Expected a full commit SHA")
    return value


def target(repo, allowed):
    require(isinstance(repo, str) and REPO.fullmatch(repo), "Use an explicit owner/repository")
    require(repo == allowed, "PR target differs from the approved teaching repository")
    require(
        repo.lower() not in {"pallets/click", "kirodotdev/kirocrew"}, "Upstream is not a PR target"
    )
    return repo


def digest(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def packet(repository, number, base_sha, head_sha, intent, diff):
    target(repository, repository)
    require(type(number) is int and number > 0, "Invalid PR number")
    result = {
        "schema_version": 1,
        "repository": repository,
        "pr": number,
        "base_sha": sha(base_sha),
        "head_sha": sha(head_sha),
        "intent": text(intent, "intent", 12000),
        "diff": text(diff, "diff", 48000),
    }
    result["input_digest"] = digest(result)
    return result


def validate_packet(value):
    expected = packet(
        value["repository"],
        value["pr"],
        value["base_sha"],
        value["head_sha"],
        value["intent"],
        value["diff"],
    )
    require(value == expected, "Packet changed or contains unknown fields")
    return expected


def validate_review(review, source, lenses, phase="independent"):
    require(isinstance(review, dict), "Review must be an object")
    require(review.get("schema_version") == 1, "Unknown review schema")
    require(review.get("head_sha") == source["head_sha"], "Review is for a stale head")
    require(review.get("base_sha") == source["base_sha"], "Review is for a stale base")
    require(review.get("input_digest") == source["input_digest"], "Review input differs")
    require(review.get("phase") == phase, "Independent review and cross-critique are separate")
    require(review.get("lens") in lenses, "Unknown review lens")
    text(review.get("run_id"), "review run ID", 160)
    text(review.get("reviewer"), "reviewer", 160)
    require(review.get("status") == "completed", "Reviewer did not complete")
    require(review.get("read_only") is True, "Review must attest read-only execution")
    findings = review.get("findings")
    require(isinstance(findings, list) and len(findings) <= 30, "Invalid findings")
    ids = set()
    for finding in findings:
        require(isinstance(finding, dict), "Finding must be an object")
        identifier = text(finding.get("id"), "finding ID", 100)
        require(identifier not in ids, "Duplicate finding ID")
        ids.add(identifier)
        require(finding.get("severity") in {"high", "medium", "low"}, "Unknown severity")
        require(
            finding.get("category") in {"correctness", "security", "data-loss", "style"},
            "Unknown finding category",
        )
        for field in ("claim", "location", "reproduction"):
            text(finding.get(field), field)
    return review


def reconcile(reviews, dispositions, source, lenses, publisher):
    require(isinstance(reviews, list) and len(reviews) == len(lenses), "Missing required reviewer")
    require({r.get("lens") for r in reviews} == set(lenses), "Missing or duplicate lens")
    run_ids = set()
    findings = {}
    for review in reviews:
        validate_review(review, source, lenses)
        require(review["run_id"] not in run_ids, "Reviewers reused the same run")
        run_ids.add(review["run_id"])
        for finding in review["findings"]:
            key = f"{review['lens']}:{finding['id']}"
            findings[key] = finding
    require(isinstance(dispositions, list), "Dispositions must be a list")
    outcomes = {}
    for item in dispositions:
        require(isinstance(item, dict), "Disposition must be an object")
        key = item.get("finding")
        require(key in findings and key not in outcomes, "Unknown or duplicate disposition")
        outcome = item.get("outcome")
        require(
            outcome in {"fixed", "rebutted", "accepted-and-deferred", "needs-a-decision"},
            "Unknown disposition",
        )
        text(item.get("evidence"), "disposition evidence")
        require(item.get("head_sha") == source["head_sha"], "Disposition is stale")
        require(item.get("decided_by") == publisher, "Disposition needs the trusted publisher")
        if outcome == "needs-a-decision":
            raise ContractError(f"Human decision needed: {key}")
        if outcome == "accepted-and-deferred":
            require(
                findings[key]["category"] not in {"security", "data-loss"},
                "Security/data-loss findings cannot converge by deferral",
            )
            require(item.get("accepted_by") == publisher, "Deferral needs explicit acceptance")
            require(
                re.fullmatch(r"\d{4}-\d{2}-\d{2}", item.get("due", "")), "Deferral needs due date"
            )
            text(item.get("owner"), "deferral owner", 100)
            prefix = f"https://github.com/{source['repository']}/issues/"
            require(
                item.get("issue", "").startswith(prefix) and item["issue"][len(prefix) :].isdigit(),
                "Deferral needs a local issue",
            )
        outcomes[key] = outcome
    require(set(outcomes) == set(findings), "Every finding needs exactly one disposition")
    return {
        "schema_version": 1,
        "packet": source,
        "reviews": reviews,
        "dispositions": dispositions,
        "publisher": publisher,
    }


def render_evidence(evidence):
    return MARKER + "\n```json\n" + json.dumps(evidence, indent=2) + "\n```\n"


def parse_evidence(body):
    require(isinstance(body, str) and len(body) <= 65000, "Evidence comment is too large")
    require(
        body.startswith(MARKER + "\n```json\n") and body.endswith("\n```\n"),
        "Invalid review comment envelope",
    )
    return json.loads(body[len(MARKER + "\n```json\n") : -len("\n```\n")])


def read_json(path):
    return json.loads(Path(path).read_text())
