"""Pure evaluator: unknown information is never success."""

from dataclasses import asdict, dataclass

from .contracts import (
    MARKER,
    ContractError,
    packet,
    parse_evidence,
    reconcile,
    require,
    target,
    validate_packet,
)

EXIT_CODES = {"ready": 0, "running": 10, "blocked": 20, "environment-error": 2}


@dataclass(frozen=True)
class Verdict:
    state: str
    head_sha: str | None
    reasons: tuple

    @property
    def exit_code(self):
        return EXIT_CODES[self.state]

    def to_dict(self):
        return asdict(self) | {"exit_code": self.exit_code, "merge_authorized": False}


def evaluate(snapshot, policy, allowed_repo, publisher):
    head = None
    try:
        require(snapshot.get("schema_version") == 1, "Unknown snapshot schema")
        require(snapshot.get("complete") is True, "Snapshot is incomplete or unreadable")
        repo = target(snapshot["repository"], allowed_repo)
        pr = snapshot["pull_request"]
        source = packet(
            repo,
            pr["number"],
            pr["baseRefOid"],
            pr["headRefOid"],
            snapshot["intent"],
            snapshot["diff"],
        )
        head = source["head_sha"]
        require(
            pr["headRepository"]["nameWithOwner"] == repo
            and pr["baseRepository"]["nameWithOwner"] == repo,
            "Cross-repository PR is unsupported",
        )
        require(pr["baseRefName"] == "main", "Only the trusted main branch is supported")
        require(pr["state"] in {"OPEN", "CLOSED", "MERGED"}, "Unknown PR state")
        if pr["state"] != "OPEN":
            return Verdict("blocked", head, ("PR is terminal",))
        require(type(pr["isDraft"]) is bool, "Draft state is unknown")
        require(pr["mergeable"] in {"MERGEABLE", "CONFLICTING", "UNKNOWN"}, "Unknown merge state")
        require(
            pr["reviewDecision"] in {"", "APPROVED", "REVIEW_REQUIRED", "CHANGES_REQUESTED"},
            "Review decision is unknown",
        )
        require(isinstance(snapshot["threads"], list), "Review threads are unreadable")
        require(
            all(type(t.get("isResolved")) is bool for t in snapshot["threads"]),
            "Thread resolution is unknown",
        )
        require(isinstance(snapshot["changed_files"], list), "Changed files are unreadable")
        blocked = []
        running = []
        if pr["isDraft"]:
            blocked.append("PR is a draft")
        if pr["mergeable"] == "CONFLICTING":
            blocked.append("PR has merge conflicts")
        if pr["mergeable"] == "UNKNOWN":
            running.append("GitHub has not computed mergeability")
        if pr["reviewDecision"] == "CHANGES_REQUESTED":
            blocked.append("A reviewer requested changes")
        if any(not t["isResolved"] for t in snapshot["threads"]):
            blocked.append("Unanswered review thread")
        for filename in snapshot["changed_files"]:
            require(isinstance(filename, str), "Invalid changed filename")
            if any(filename.startswith(p) for p in policy["protected_prefixes"]):
                blocked.append(f"Maintainer decision required for trusted control code: {filename}")
        checks = snapshot["checks"]
        require(isinstance(checks, list), "Checks are unreadable")
        for name in policy["required_checks"]:
            matches = [c for c in checks if c.get("name") == name and c.get("headSha") == head]
            if not matches:
                blocked.append(f"Missing current-head check: {name}")
                continue
            require(
                all(type(c.get("id")) is int and type(c.get("attempt")) is int for c in matches),
                "Check identity is unknown",
            )
            latest = max(matches, key=lambda c: (c["id"], c["attempt"]))
            require(latest.get("trusted_workflow") is True, "Check source is not verified")
            require(
                latest.get("status")
                in {"queued", "in_progress", "completed", "waiting", "requested", "pending"},
                "Unknown check status",
            )
            if latest["status"] != "completed":
                running.append(f"{name} is {latest['status']}")
            elif latest.get("conclusion") == "success":
                pass
            elif latest.get("conclusion") in {
                "failure",
                "cancelled",
                "timed_out",
                "skipped",
                "neutral",
                "action_required",
                "stale",
                "startup_failure",
            }:
                blocked.append(f"{name} did not pass: {latest['conclusion']}")
            else:
                raise ContractError(f"Unknown {name} conclusion")
        require(
            publisher and snapshot.get("publisher_can_write") is True,
            "Configure an evidence publisher with repository write permission",
        )
        require(isinstance(snapshot["comments"], list), "Comments are unreadable")
        candidates = [
            c
            for c in snapshot["comments"]
            if c.get("user", {}).get("login") == publisher and c.get("body", "").startswith(MARKER)
        ]
        if not candidates:
            blocked.append("Missing trusted reviewer evidence")
        else:
            require(
                all(type(c.get("id")) is int for c in candidates), "Comment identity is unknown"
            )
            evidence = parse_evidence(max(candidates, key=lambda c: c["id"])["body"])
            require(evidence.get("publisher") == publisher, "Evidence publisher mismatch")
            validate_packet(evidence["packet"])
            require(evidence["packet"] == source, "Review packet is stale or for a different PR")
            current_findings = {
                f"{r['lens']}:{f['id']}": f for r in evidence["reviews"] for f in r["findings"]
            }
            for comment in candidates:
                try:
                    earlier = parse_evidence(comment["body"])
                except (ContractError, ValueError):
                    continue
                if earlier.get("packet") != source:
                    continue
                for review in earlier["reviews"]:
                    for finding in review["findings"]:
                        key = f"{review['lens']}:{finding['id']}"
                        require(
                            current_findings.get(key) == finding,
                            "A raised finding disappeared; preserve it and give a disposition",
                        )
            try:
                reconcile(
                    evidence["reviews"],
                    evidence["dispositions"],
                    source,
                    policy["required_lenses"],
                    publisher,
                )
            except ContractError as error:
                blocked.append(str(error))
        if blocked:
            return Verdict("blocked", head, tuple(blocked + running))
        if running:
            return Verdict("running", head, tuple(running))
        return Verdict("ready", head, ("Current-head gates and published review evidence pass",))
    except (ContractError, KeyError, TypeError, ValueError, AttributeError) as error:
        return Verdict("environment-error", head, (f"Cannot prove readiness: {error}",))
