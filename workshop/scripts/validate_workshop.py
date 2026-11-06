"""Check curriculum structure and execute documented offline commands with expected exit codes."""

import argparse
import json
import re
import subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--run", action="store_true")
args = parser.parse_args()
root = Path.cwd()
workshop = (root / "WORKSHOP.md").read_text()
labs = re.split(r"^## Lab ", workshop, flags=re.MULTILINE)[1:]
assert len(labs) == 5
minutes = 0
for lab in labs:
    minutes += int(re.search(r"\((\d+) minutes\)", lab.splitlines()[0]).group(1))
    for field in ("Decision", "Build", "Checkpoint", "Comprehension"):
        assert f"### {field}" in lab, f"Missing {field}"
assert minutes == 60
advanced = (root / "ADVANCED.md").read_text()
assert sum(map(int, re.findall(r"^## .* \((\d+) minutes\)", advanced, re.MULTILINE))) == 30
assert "Authored teaching" in advanced and "agreement" in advanced
for doc in (
    "README.md",
    "PREWORK.md",
    "WORKSHOP.md",
    "ADVANCED.md",
    "ANSWERS.md",
    "FACILITATOR.md",
    "MAINTAINER.md",
    "ATTRIBUTION.md",
):
    content = (root / doc).read_text()
    for link in re.findall(r"\]\(([^)]+)\)", content):
        if "://" not in link and not link.startswith("#"):
            assert (root / link.split("#")[0]).exists(), f"Broken {doc} link: {link}"
commands = json.loads((root / "workshop-commands.json").read_text())
if args.run:
    for entry in commands:
        command = [str(root / ".venv/bin/python"), *entry["args"]]
        completed = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=60)
        assert completed.returncode == entry["expected_exit"], (
            entry["name"],
            completed.returncode,
            completed.stdout,
            completed.stderr,
        )
        print(f"{entry['name']}: expected exit {completed.returncode}")
print("Workshop structure, time boxes, links and command manifest are valid.")
