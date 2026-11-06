from pathlib import Path

import yaml


def workflows():
    root = Path(".github/workflows")
    if not root.exists():
        root = Path("../.github/workflows")
    return [yaml.safe_load(p.read_text()) for p in root.glob("*.yml")]


def test_write_workflows_only_checkout_main():
    for workflow in workflows():
        if "write" not in workflow["permissions"].values():
            continue
        for job in workflow["jobs"].values():
            for step in job["steps"]:
                if step.get("uses", "").startswith("actions/checkout"):
                    assert step["with"]["ref"] == "main"
                    assert step["with"]["persist-credentials"] is False
                assert "pip install" not in step.get("run", "")
                assert "download-artifact" not in step.get("uses", "")


def test_pr_tests_read_only():
    workflow = next(w for w in workflows() if w["name"] == "Workshop Tests")
    assert workflow["permissions"] == {"contents": "read"}
    for step in workflow["jobs"]["tests"]["steps"]:
        assert "secrets." not in str(step)


def test_reminder_guard_and_permissions():
    workflow = next(w for w in workflows() if w["name"] == "Monthly workshop reminder")
    assert workflow["permissions"] == {"contents": "read", "issues": "write"}
    assert workflow["jobs"]["remind"]["if"] == (
        "github.repository == 'positivesumgames/click-pr-review-workshop'"
    )
    assert "statuses" not in workflow["permissions"] and "actions" not in workflow["permissions"]
