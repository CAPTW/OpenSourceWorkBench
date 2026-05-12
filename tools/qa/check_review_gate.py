#!/usr/bin/env python3
"""Evaluate an OSW numeric review score against merge thresholds."""

from __future__ import annotations

import argparse


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--score", type=int, required=True)
    parser.add_argument("--hard-blocker", action="store_true")
    args = parser.parse_args()

    if args.hard_blocker:
        print("[fail] Review gate blocked by hard blocker.")
        return 1
    if args.score >= 90:
        print("[ok] Review gate passed: merge possible.")
        return 0
    if args.score >= 80:
        print("[warn] Review gate requires minor amend before merge.")
        return 2
    print("[fail] Review gate blocked.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
