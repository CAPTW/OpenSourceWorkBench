#!/usr/bin/env python3
"""Check changed files against allowed and forbidden glob patterns."""

from __future__ import annotations

import argparse
import fnmatch

from _common import changed_files, repo_root


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="develop")
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--forbid", action="append", default=[])
    args = parser.parse_args()
    root = repo_root()
    paths = changed_files(args.base, root=root)
    failures: list[str] = []

    for path in paths:
        if args.allow and not matches_any(path, args.allow):
            failures.append(f"{path}: outside allowed patterns")
        if args.forbid and matches_any(path, args.forbid):
            failures.append(f"{path}: matches forbidden patterns")

    if failures:
        print("[fail] Changed-file scope issues:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("[ok] Changed files are within configured scope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
