#!/usr/bin/env python3
"""Print a compact local Git status report for OSW."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence
from pathlib import Path


def run_git(args: Sequence[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def value_or_missing(args: Sequence[str], *, cwd: Path | None = None) -> str:
    proc = run_git(args, cwd=cwd)
    if proc.returncode != 0 or not proc.stdout.strip():
        return "<missing>"
    return proc.stdout.strip()


def main() -> int:
    version = value_or_missing(["--version"])
    root_text = value_or_missing(["rev-parse", "--show-toplevel"])
    root = Path(root_text) if root_text != "<missing>" else None
    cwd = root if root else None

    print(f"Git version: {version}")
    print(f"Repo root: {root_text}")
    print(f"Current branch: {value_or_missing(['symbolic-ref', '--short', 'HEAD'], cwd=cwd)}")
    print(f"HEAD: {value_or_missing(['rev-parse', '--short', 'HEAD'], cwd=cwd)}")
    hooks_path = value_or_missing(["config", "--local", "--get", "core.hooksPath"], cwd=cwd)
    commit_template = value_or_missing(
        ["config", "--local", "--get", "commit.template"],
        cwd=cwd,
    )
    print(f"hooksPath: {hooks_path}")
    print(f"commit.template: {commit_template}")
    print(f"user.name: {value_or_missing(['config', '--get', 'user.name'], cwd=cwd)}")
    print(f"user.email: {value_or_missing(['config', '--get', 'user.email'], cwd=cwd)}")

    branches = value_or_missing(["branch", "--list", "--format=%(refname:short)"], cwd=cwd)
    print("Branches:")
    if branches == "<missing>":
        print("  <none>")
    else:
        for branch in branches.splitlines():
            print(f"  {branch}")

    status = value_or_missing(["status", "--short", "--branch"], cwd=cwd)
    print("Status:")
    for line in status.splitlines() or ["<missing>"]:
        print(f"  {line}")
    return 0 if root else 2


if __name__ == "__main__":
    raise SystemExit(main())
