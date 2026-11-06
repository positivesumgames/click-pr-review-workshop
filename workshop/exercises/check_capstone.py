import argparse
import importlib.util

parser = argparse.ArgumentParser()
parser.add_argument("--gate", default="exercises/capstone.py")
parser.add_argument("--cases", default="exercises/test_my_gate.py")
args = parser.parse_args()

spec = importlib.util.spec_from_file_location("capstone", args.gate)
capstone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capstone)
test_spec = importlib.util.spec_from_file_location("capstone_tests", args.cases)
tests = importlib.util.module_from_spec(test_spec)
test_spec.loader.exec_module(tests)
cases = tests.cases()
assert len(cases) >= 3, "Provide a positive, negative, and unknown-input test"
observed = set()
for packet, evidence, expected in cases:
    passed, reason = capstone.additional_gate(packet, evidence)
    assert type(passed) is bool and isinstance(reason, str) and reason.strip()
    assert passed is expected
    observed.add(passed)
assert observed == {False, True}, "Your gate must reject something and permit something"
print("Capstone tests pass. Facilitator must still score novelty and explanation with the rubric.")
