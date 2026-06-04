#!/usr/bin/env python3
"""Scan MATLAB/Octave scripts for obvious unsafe operations."""

from __future__ import annotations

import argparse
from pathlib import Path

UNSAFE = ["system(", "unix(", "dos(", "!", "webread(", "urlread(", "delete(", "rmdir("]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", default=["examples", "tests"])
    args = parser.parse_args()
    root = Path.cwd()
    failures: list[str] = []
    for item in args.paths:
        path = root / item
        files = [path] if path.is_file() else list(path.rglob("*.m")) if path.exists() else []
        for file_path in files:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            for marker in UNSAFE:
                if marker in text:
                    failures.append(f"{file_path}: contains {marker}")
    if failures:
        print("[fail] Unsafe mscript markers:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("[ok] No obvious mscript safety markers found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
