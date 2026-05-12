#!/usr/bin/env python3
"""Hook entrypoint: reject obvious prompt scope drift."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", default="", help="Prompt text to scan.")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    cmd = [sys.executable, "tools/qa/check_scope_drift.py"]
    if args.text:
        cmd.extend(["--text", args.text])
    return subprocess.run(cmd, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
