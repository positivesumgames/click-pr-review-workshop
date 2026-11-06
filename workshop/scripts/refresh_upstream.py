"""Prepare a manual refresh; never commit, push, or change published main."""

import argparse
import json
from pathlib import Path

from pr_review_workshop.contracts import ContractError
from pr_review_workshop.maintenance import refresh

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", required=True)
parser.add_argument("--root", default="..")
parser.add_argument("--branch")
args = parser.parse_args()
try:
    print(json.dumps(refresh(Path(args.root), args.repo, args.branch), indent=2))
except ContractError as error:
    parser.exit(2, f"Refresh stopped: {error}\n")
