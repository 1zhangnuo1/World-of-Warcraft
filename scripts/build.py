"""Run with `uv run python scripts/build.py` on the target OS."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    # Console mode preserves --headless reports and diagnostic errors on both OSes.
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--onedir",
            "--name",
            "NavigationLab",
            "--paths",
            str(ROOT / "src"),
            "--distpath",
            str(ROOT / "dist"),
            "--workpath",
            str(ROOT / "build"),
            "--specpath",
            str(ROOT / "build"),
            str(ROOT / "scripts" / "entrypoint.py"),
        ],
        cwd=ROOT,
        check=True,
    )
    print(f"Built for {sys.platform}: {ROOT / 'dist' / 'NavigationLab'}")


if __name__ == "__main__":
    main()
