#!/usr/bin/env python3
"""Warn when code changes lack nearby documentation changes."""

from __future__ import annotations

import subprocess
from pathlib import Path


def main() -> int:
    root = Path.cwd()
    proc = subprocess.run(["git", "diff", "--name-only", "develop...HEAD"], cwd=root, text=True, capture_output=True, check=False)
    paths = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    code_changed = any(path.startswith("src/") and path.endswith(".py") for path in paths)
    docs_changed = any(path.startswith("docs/") or path == "README.md" for path in paths)
    if code_changed and not docs_changed:
        print("[warn] Code changed without docs update.")
    else:
        print("[ok] Documentation update check complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
