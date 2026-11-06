"""Read-only gate for a real Click exercise change, separate from scenario reenactments."""

import json
import os
import subprocess
from pathlib import Path

from pr_review_workshop.click_cases import observe, source_root
from pr_review_workshop.contracts import require, sha

event_path = os.environ.get("GITHUB_EVENT_PATH")
if event_path:
    event = json.loads(Path(event_path).read_text())
    pr = event.get("pull_request")
    if pr:
        base, head = sha(pr["base"]["sha"]), sha(pr["head"]["sha"])
        root = source_root()
        result = subprocess.run(
            ["git", "-C", str(root), "diff", "--name-only", base, head],
            capture_output=True,
            text=True,
            check=True,
        )
        if "src/click/formatting.py" in result.stdout.splitlines():
            observation = observe("native")
            require(
                observation["hyphen_tokens_intact"] and observation["long_token_intact"],
                "Current Click candidate still splits a required token",
            )
            test = root / "tests/test_workshop_regression.py"
            require(test.is_file(), "Add the learner-owned Click regression test")
            completed = subprocess.run(
                [str(Path(".venv/bin/python").resolve()), "-m", "pytest", "-q", str(test)],
                env=os.environ | {"PYTHONPATH": str(root / "src")},
                check=False,
            )
            require(completed.returncode == 0, "Learner regression test did not pass")
            print("Actual PR source and learner regression test pass.")
        else:
            print("No Click formatter change; scenario contract gates still apply.")
    else:
        print("Not a PR event; actual candidate gate is not applicable.")
else:
    print("No live event; actual PR gate is unverified. Use native case observations locally.")
