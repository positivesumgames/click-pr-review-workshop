"""Small explicit commands, each completing one prepare-PR stage."""

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

from . import github
from .budget import Budget, estimate
from .contracts import ContractError, read_json, reconcile, require, validate_packet
from .isolation import owned_path
from .monitor import tick
from .providers import live_request, replay_request, require_container, run_pair
from .readiness import evaluate


def save(path, value):
    destination = owned_path(Path.cwd(), path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(value, indent=2) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Review-ready is not permission to merge.")
    parser.add_argument("--policy", default="config/review-policy.json")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("preflight", "evaluate", "packet", "watch", "publish"):
        item = sub.add_parser(command)
        item.add_argument("--fixture")
        item.add_argument("--repo")
        item.add_argument("--allowed-repo")
        item.add_argument("--pr", type=int)
        item.add_argument(
            "--publisher", default=os.environ.get("WORKSHOP_EVIDENCE_PUBLISHER", "learner")
        )
        if command == "packet":
            item.add_argument("--out", default=".work/packet.json")
        if command == "watch":
            item.add_argument("--state", default=".work/watch.json")
            item.add_argument("--stop", action="store_true")
            item.add_argument("--budget-exhausted", action="store_true")
        if command == "publish":
            item.add_argument("--evidence", required=True)
    item = sub.add_parser("reconcile")
    item.add_argument("--packet", required=True)
    item.add_argument("--reviews", nargs="+", required=True)
    item.add_argument("--dispositions", required=True)
    item.add_argument("--publisher", required=True)
    item.add_argument("--out", default=".work/evidence.json")
    item = sub.add_parser("review")
    item.add_argument("--packet", required=True)
    item.add_argument("--pricing", default="config/providers.json")
    item.add_argument("--mode", choices=("replay", "live"), default="replay")
    item.add_argument("--replay", default="exercises/replay.json")
    item.add_argument("--budget")
    item.add_argument("--approve-paid-run", action="store_true")
    item.add_argument("--out", default=".work/review-run.json")
    item = sub.add_parser("estimate")
    item.add_argument("--pricing", default="config/providers.json")
    sub.add_parser("action")
    args = parser.parse_args(argv)
    try:
        policy = read_json(args.policy)
        if args.command == "estimate":
            result = estimate(read_json(args.pricing))
        elif args.command == "review":
            source = validate_packet(read_json(args.packet))
            config = read_json(args.pricing)
            if args.mode == "live":
                require_container()
                require(args.approve_paid_run, "Approve selected models and budget before sending")
                require(
                    not Path(args.out).exists(), "Use a new run path; never reset a saved budget"
                )
                budget = Budget(config, args.budget)
                request = live_request
            else:
                # Replay date/usage are fictional and must not authorize future live prices.
                from datetime import date

                budget = Budget(config, args.budget, today=date.fromisoformat(config["checked_on"]))
                request = replay_request(read_json(args.replay))
            result = run_pair(
                source, policy, config, budget, request, persist=lambda value: save(args.out, value)
            )
            result["provenance"] = (
                "Authored teaching replay; usage is fictional"
                if args.mode == "replay"
                else "Live API results; validate all claims"
            )
            save(args.out, result)
        elif args.command == "reconcile":
            source = validate_packet(read_json(args.packet))
            result = reconcile(
                [read_json(p) for p in args.reviews],
                read_json(args.dispositions),
                source,
                policy["required_lenses"],
                args.publisher,
            )
            save(args.out, result)
        elif args.command == "action":
            result = github.action(policy)
        else:
            if args.fixture:
                require(args.command != "publish", "Replay cannot publish live PR evidence")
                snapshot = read_json(args.fixture)
                allowed = args.allowed_repo or snapshot["repository"]
            else:
                require(
                    args.repo and args.allowed_repo and args.pr,
                    "Live mode requires --repo, --allowed-repo, and --pr",
                )
                snapshot = github.collect(args.repo, args.pr, args.allowed_repo, args.publisher)
                allowed = args.allowed_repo
            if args.command == "publish":
                result = github.publish(
                    args.repo, args.pr, allowed, args.publisher, read_json(args.evidence), policy
                )
            elif args.command in {"preflight", "packet"}:
                result = github.source_packet(snapshot)
                require(snapshot["pull_request"]["baseRefName"] == "main", "Base must be main")
                if args.command == "packet":
                    save(args.out, result)
                else:
                    result = {
                        "stage": "preflight",
                        "packet_digest": result["input_digest"],
                        "head_sha": result["head_sha"],
                        "paid_calls": 0,
                    }
            else:
                verdict = evaluate(snapshot, policy, allowed, args.publisher)
                if args.command == "watch":
                    state = read_json(args.state) if Path(args.state).exists() else None
                    require(
                        not state or not state.get("stopped"),
                        "Monitor stopped; review before restarting",
                    )
                    result = tick(
                        snapshot,
                        verdict,
                        state,
                        policy,
                        time.time(),
                        stop=args.stop,
                        budget_exhausted=args.budget_exhausted,
                    )
                    save(args.state, result["state"])
                else:
                    print(json.dumps(verdict.to_dict(), indent=2))
                    return verdict.exit_code
        print(json.dumps(result, indent=2))
        return 0
    except (
        ContractError,
        KeyError,
        ValueError,
        TypeError,
        OSError,
        subprocess.TimeoutExpired,
    ) as error:
        print(
            json.dumps(
                {"state": "environment-error", "reason": str(error), "merge_authorized": False},
                indent=2,
            )
        )
        return 2
