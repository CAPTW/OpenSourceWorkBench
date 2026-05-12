#!/usr/bin/env python3
"""Hook entrypoint for plugin manifest checks."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    return subprocess.run([sys.executable, "tools/qa/check_plugin_manifests.py"], cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
