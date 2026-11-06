import json
import os

from pr_review_workshop.maintenance import reminder

print(json.dumps(reminder(os.environ["GITHUB_REPOSITORY"]), indent=2))
