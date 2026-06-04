#!/usr/bin/env python3
"""Report branch and dirty state, optionally failing on dirty worktrees."""

from __future__ import annotations

import argparse

from _common import capture, repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Return success even when status is dirty.",
    )
    args = parser.parse_args()
    root = repo_root()

    branch = capture(["git", "branch", "--show-current"], cwd=root).stdout.strip() or "<detached>"
    status = capture(["git", "status", "--short"], cwd=root).stdout.strip()
    print(f"branch: {branch}")
    print(f"status: {'dirty' if status else 'clean'}")
    if status:
        print(status)
        if not args.allow_dirty:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
