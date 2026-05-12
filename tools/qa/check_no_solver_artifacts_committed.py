#!/usr/bin/env python3
"""Detect staged or changed solver/runtime artifacts."""

from __future__ import annotations

import argparse
import re

from _common import capture, changed_files, repo_root


PATTERNS = [
    re.compile(r"(^|/)processor[0-9]+(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)postProcessing(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)dynamicCode(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)log\.(blockMesh|checkMesh|decomposePar|icoFoam|simpleFoam|snappyHexMesh|reconstructPar)$", re.IGNORECASE),
    re.compile(r"\.(frd|sta|cvg|12d|eig|mtx|nam|fcv|rout)$", re.IGNORECASE),
    re.compile(r"(^|/)(solver_runs|solver-runs|run_cases|scratch|work|tmp|temp)(/|$)", re.IGNORECASE),
    re.compile(r"(^|/)octave-workspace$", re.IGNORECASE),
]


def is_allowed(path: str) -> bool:
    lowered = path.replace("\\", "/").lower()
    return lowered.startswith("examples/") or lowered.startswith("tests/")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="develop")
    parser.add_argument("--staged", action="store_true", help="Check staged files instead of branch diff.")
    args = parser.parse_args()
    root = repo_root()

    if args.staged:
        proc = capture(["git", "diff", "--cached", "--name-only"], cwd=root)
        paths = [line for line in proc.stdout.splitlines() if line.strip()]
    else:
        paths = changed_files(args.base, root=root)

    failures = [
        path
        for path in paths
        if not is_allowed(path) and any(pattern.search(path.replace("\\", "/")) for pattern in PATTERNS)
    ]
    if failures:
        print("[fail] Solver/runtime artifact paths detected:")
        for path in failures:
            print(f"  - {path}")
        return 1
    print("[ok] No solver/runtime artifact paths detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
