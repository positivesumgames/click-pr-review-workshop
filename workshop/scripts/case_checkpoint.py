import argparse
import json

from pr_review_workshop.click_cases import observe

parser = argparse.ArgumentParser(
    description="Observe the pinned case or a labeled teaching candidate"
)
parser.add_argument("candidate", choices=["baseline", "partial", "repaired", "native"])
parser.add_argument("--require-intact", action="store_true")
args = parser.parse_args()
result = observe(args.candidate)
print(json.dumps(result, indent=2))
if args.require_intact and not (result["hyphen_tokens_intact"] and result["long_token_intact"]):
    parser.exit(1, "Expected teaching failure: at least one token still splits.\n")
