"""Assemble an independent local distribution copy; never create/push a remote."""

import argparse
import shutil
import subprocess
from pathlib import Path

from pr_review_workshop.contracts import read_json, require
from pr_review_workshop.isolation import owned_path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--out", default=".work/template")
args = parser.parse_args()
root = Path.cwd().resolve()
destination = owned_path(root, args.out)
require(not destination.exists(), "Distribution target exists; do not overwrite it")
source = owned_path(root, ".work/click-source")
manifest = read_json("workshop-manifest.json")
head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
require(head == manifest["source_sha"], "Source copy differs from the pinned baseline")
require(
    subprocess.check_output(["git", "-C", str(source), "status", "--porcelain"], text=True).strip()
    == "",
    "Source copy is dirty",
)
subprocess.run(["git", "clone", "--no-hardlinks", str(source), str(destination)], check=True)
subprocess.run(
    ["git", "-C", str(destination), "remote", "rename", "origin", "upstream"], check=True
)
subprocess.run(
    [
        "git",
        "-C",
        str(destination),
        "remote",
        "set-url",
        "upstream",
        "https://github.com/pallets/click.git",
    ],
    check=True,
)
subprocess.run(
    [
        "git",
        "-C",
        str(destination),
        "remote",
        "set-url",
        "--push",
        "upstream",
        "no-push://pallets/click",
    ],
    check=True,
)
upstream = destination / ".upstream"
upstream.mkdir()
shutil.move(destination / ".github", upstream / "github")
shutil.copytree(root / ".github", destination / ".github")
shutil.copytree(root / ".kiro", destination / ".kiro")
package = destination / "workshop"
package.mkdir()
for filename in (
    "pyproject.toml",
    "README.md",
    "PREWORK.md",
    "WORKSHOP.md",
    "ADVANCED.md",
    "ANSWERS.md",
    "FACILITATOR.md",
    "MAINTAINER.md",
    "ATTRIBUTION.md",
    "LICENSE",
    "workshop-manifest.json",
    "workshop-commands.json",
    ".gitignore",
    ".dockerignore",
):
    shutil.copy2(root / filename, package / filename)
for directory in (
    "src/pr_review_workshop",
    "config",
    "scripts",
    "tests",
    "exercises",
    "container",
    ".kiro",
):
    shutil.copytree(
        root / directory,
        package / directory,
        ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"),
    )
shutil.move(destination / "README.md", destination / "CLICK_README.md")
(destination / "README.md").write_text(
    "# Click PR-review workshop\n\n"
    "Independent teaching template; not a GitHub fork of Click.\n\n"
    "Choose Use this template, default branch only, then create exercise branches "
    "from your own main. All practice PRs target your repository, never upstream.\n\n"
    "Start with [prework](workshop/PREWORK.md), then the "
    "[60-minute core](workshop/WORKSHOP.md) and optional "
    "[30-minute advanced lab](workshop/ADVANCED.md).\n\n"
    "Enter `workshop/` before running workshop commands. See "
    "[maintainer refresh and reminder](workshop/MAINTAINER.md) and "
    "[attribution](workshop/ATTRIBUTION.md). Click retains its BSD license; "
    "workshop material is Apache-2.0. Review-ready never authorizes merge.\n"
)
with (destination / ".gitignore").open("a") as file:
    file.write(
        "\n# Workshop state\nworkshop/.work/\nworkshop/.venv/\n"
        "workshop/.ruff_cache/\nworkshop/.pytest_cache/\nworkshop/src/*.egg-info/\n"
    )
print(f"Independent distribution assembled at {destination}; no remote was created or pushed.")
