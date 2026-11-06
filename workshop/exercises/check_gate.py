"""A learner checkpoint, separate from the reference implementation's green tests."""

import argparse
import copy
import importlib.util
from pathlib import Path

from pr_review_workshop.contracts import read_json

parser = argparse.ArgumentParser()
parser.add_argument("--gate", default="exercises/unsafe_gate.py")
args = parser.parse_args()
spec = importlib.util.spec_from_file_location("learner_gate", args.gate)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
ready = read_json("tests/fixtures/ready.json")
stale = read_json("tests/fixtures/stale-review.json")
pending = read_json("tests/fixtures/pending-check.json")
missing = copy.deepcopy(ready)
missing["checks"] = []
assert gate.ready(ready), "The clean, complete scenario must pass"
assert not gate.ready(stale), "Stale reviewer evidence must not pass"
assert not gate.ready(pending), "Running checks must not pass"
assert not gate.ready(missing), "An empty check list must not pass"
assert "pr_review_workshop.readiness" not in Path(args.gate).read_text(), (
    "Implement your own checks here; explain them before consulting the reference"
)
print("Checkpoint passed: explain which fact rejects each unsafe fixture.")
