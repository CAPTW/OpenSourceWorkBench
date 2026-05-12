#!/usr/bin/env python3
"""Create an OSW feature worktree without touching remotes."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_WORKTREE_ROOT = Path("../_worktrees")
DEFAULT_BRANCH_PREFIX = "feature/osw-"
DEFAULT_BASE_BRANCH = "develop"


@dataclass(frozen=True)
class WorktreePlan:
    slug: str
    branch_name: str
    path: Path
    base_branch: str


def run_git(args: Sequence[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def repo_root() -> Path:
    proc = run_git(["rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "not a git repository")
    return Path(proc.stdout.strip())


def sanitize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        raise ValueError("worktree name must contain at least one letter or digit")
    return slug[:64].strip("-")


def resolve_worktree_root(repo_root: Path, worktree_root: Path) -> Path:
    if worktree_root.is_absolute():
        return worktree_root
    return (repo_root / worktree_root).resolve()


def build_worktree_plan(
    name: str,
    *,
    repo_root: Path,
    worktree_root: Path = DEFAULT_WORKTREE_ROOT,
    base_branch: str = DEFAULT_BASE_BRANCH,
    branch_prefix: str = DEFAULT_BRANCH_PREFIX,
) -> WorktreePlan:
    slug = sanitize_slug(name)
    root = resolve_worktree_root(repo_root, worktree_root)
    return WorktreePlan(
        slug=slug,
        branch_name=f"{branch_prefix}{slug}",
        path=root / slug,
        base_branch=base_branch,
    )


def local_branch_exists(branch: str, root: Path) -> bool:
    proc = run_git(["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=root)
    return proc.returncode == 0


def validate_branch_name(branch: str, root: Path) -> None:
    proc = run_git(["check-ref-format", "--branch", branch], cwd=root)
    if proc.returncode != 0:
        raise ValueError(proc.stderr.strip() or f"invalid branch name: {branch}")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create an OSW feature branch and worktree.")
    parser.add_argument("name", help="Human-readable feature name, converted to a safe slug.")
    parser.add_argument(
        "--base",
        default=DEFAULT_BASE_BRANCH,
        help="Local base branch. Default: develop.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_WORKTREE_ROOT,
        help="Worktree root. Default: ../_worktrees",
    )
    parser.add_argument(
        "--branch-prefix",
        default=DEFAULT_BRANCH_PREFIX,
        help="Feature branch prefix.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned git command without creating anything.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        root = repo_root()
        plan = build_worktree_plan(
            args.name,
            repo_root=root,
            worktree_root=args.root,
            base_branch=args.base,
            branch_prefix=args.branch_prefix,
        )
        validate_branch_name(plan.branch_name, root)

        if plan.path.exists():
            raise RuntimeError(f"worktree path already exists: {plan.path}")
        if local_branch_exists(plan.branch_name, root):
            raise RuntimeError(f"local branch already exists: {plan.branch_name}")
        if not local_branch_exists(plan.base_branch, root):
            raise RuntimeError(f"base branch does not exist locally: {plan.base_branch}")

        command = [
            "git",
            "worktree",
            "add",
            "-b",
            plan.branch_name,
            str(plan.path),
            plan.base_branch,
        ]
        print(" ".join(command))
        if args.dry_run:
            print("[dry-run] No worktree created.")
            return 0

        proc = subprocess.run(command, cwd=root, check=False)
        return proc.returncode
    except Exception as exc:
        print(f"[fail] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
