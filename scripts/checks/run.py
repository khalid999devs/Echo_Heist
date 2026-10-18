"""Run the agreed checks with the current locked project interpreter."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    commands = (
        (sys.executable, "scripts/checks/structure.py"),
        (sys.executable, "-m", "ruff", "check", "."),
        (sys.executable, "-m", "ruff", "format", "--check", "."),
        (sys.executable, "-m", "mypy"),
        (sys.executable, "-m", "pytest"),
    )
    for command in commands:
        print("Running: " + " ".join(command[1:]), flush=True)
        result = subprocess.run(command, cwd=ROOT, check=False)
        if result.returncode:
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
