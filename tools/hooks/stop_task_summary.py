#!/usr/bin/env python3
"""Print a local stop-task summary for Codex reports."""

from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    for args in (["git", "branch", "--show-current"], ["git", "status", "--short"], ["git", "log", "--oneline", "-3"]):
        print(f"$ {' '.join(args)}")
        subprocess.run(args, cwd=root, check=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
