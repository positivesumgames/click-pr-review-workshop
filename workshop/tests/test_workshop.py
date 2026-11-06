import subprocess
import sys


def test_workshop_structure():
    result = subprocess.run(
        [sys.executable, "scripts/validate_workshop.py"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
