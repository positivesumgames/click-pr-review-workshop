"""A single finite tick; the host schedules the next tick, never a sleeping agent."""

from .contracts import digest, require


def tick(snapshot, verdict, state, policy, now, *, stop=False, budget_exhausted=False):
    require(type(now) in {int, float}, "Invalid monitor time")
    state = dict(state or {"started_at": now, "cycles": 0, "unchanged": 0})
    require(now >= state["started_at"], "Monitor clock moved backwards")
    state["cycles"] += 1
    meaningful = digest(
        {
            key: snapshot.get(key)
            for key in (
                "repository",
                "pull_request",
                "checks",
                "threads",
                "comments",
                "changed_files",
                "publisher_can_write",
                "complete",
                "intent",
                "diff",
            )
        }
    )
    changed = state.get("digest") != meaningful
    state["unchanged"] = 0 if changed else state["unchanged"] + 1
    state["digest"] = meaningful
    reason = None
    if stop:
        reason = "user-stop"
    elif snapshot.get("pull_request", {}).get("state") in {"MERGED", "CLOSED"}:
        reason = "terminal"
    elif verdict.state == "ready":
        reason = "ready"
    elif verdict.state in {"blocked", "environment-error"}:
        reason = verdict.state
    elif budget_exhausted:
        reason = "budget-exhausted"
    elif now - state["started_at"] >= policy["max_runtime_seconds"]:
        reason = "time-exhausted"
    elif state["cycles"] >= policy["max_cycles"]:
        reason = "cycles-exhausted"
    elif state["unchanged"] >= policy["max_unchanged_cycles"]:
        reason = "stall"
    state["stopped"] = bool(reason)
    return {
        "state": state,
        "dispatch": changed or bool(reason),
        "stop_reason": reason,
        "verdict": verdict.to_dict(),
        "next_check_seconds": None if reason else 60,
    }
