import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

for arguments in (
    ["ruff", "check", "."],
    ["ruff", "format", "--check", "."],
    ["mypy"],
    ["pytest", "-q"],
):
    subprocess.run([sys.executable, "-m", *arguments], cwd=ROOT, check=True)
