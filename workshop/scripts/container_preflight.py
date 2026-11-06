import json
import shutil
from pathlib import Path

import yaml

from pr_review_workshop.isolation import container_config

config = yaml.safe_load(Path("container/compose.yml").read_text())
result = container_config(config)
result["engine_available"] = bool(shutil.which("docker"))
result["next"] = (
    "Build and inspect the container before any approved live run"
    if result["engine_available"]
    else "Use replay; live Crew/provider path unverified"
)
print(json.dumps(result, indent=2))
