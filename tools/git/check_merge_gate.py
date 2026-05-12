#!/usr/bin/env python3
"""Merge-commit gate for OSW local Git hooks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import preflight_commit

CONFLICT_MARKERS = (b"<<<<<<< ", b"=======", b">>>>>>> ")


def run_git(
    args: Sequence[str],
    *,
    cwd: Path | None = None,
    text: bool = True,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=text,
        check=False,
    )


def staged_blob(root: Path, path: str) -> bytes:
    proc = run_git(["show", f":{path}"], cwd=root, text=False)
    if proc.returncode != 0:
        return b""
    return proc.stdout


def contains_conflict_marker(content: bytes) -> bool:
    for line in content.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(marker) for marker in CONFLICT_MARKERS):
            return True
    return False


def run_cached_diff_check(root: Path) -> list[str]:
    proc = run_git(["diff", "--cached", "--check"], cwd=root)
    if proc.returncode == 0:
        return []
    output = "\n".join(part for part in (proc.stdout, proc.stderr) if part)
    return [line for line in output.splitlines() if line.strip()]


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run OSW merge gate checks.")
    parser.add_argument("--hook", default="manual", help="Hook name for reporting context.")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    failures: list[str] = []

    try:
        root = preflight_commit.repo_root()
        print(f"OSW merge gate ({args.hook})")
        print(preflight_commit.git_status_summary(root))

        merge_head = root / ".git" / "MERGE_HEAD"
        if not merge_head.exists():
            print("[info] MERGE_HEAD not present; running gate in manual/non-merge mode.")

        staged = preflight_commit.staged_files(root)
        for path in staged:
            content = staged_blob(root, path)
            if contains_conflict_marker(content):
                failures.append(f"conflict marker staged: {path}")

        failures.extend(run_cached_diff_check(root))

        preflight_code = preflight_commit.main(["--hook", args.hook])
        if preflight_code != 0:
            failures.append(f"preflight failed with exit code {preflight_code}")

    except Exception as exc:
        print(f"[fail] merge gate crashed safely: {exc}", file=sys.stderr)
        return 2

    if failures:
        print("[fail] Merge gate failures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print("[ok] Merge gate checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
