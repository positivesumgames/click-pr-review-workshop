"""Split a saved run into individually reviewable files; never assign dispositions."""

import argparse

from pr_review_workshop.cli import save
from pr_review_workshop.contracts import read_json

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--run", default=".work/review-run.json")
args = parser.parse_args()
run = read_json(args.run)
for review in run["independent"]:
    save(f".work/{review['lens']}.json", review)
print("Independent reviews exported. Verify claims and write your own dispositions.")
