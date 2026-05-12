#!/usr/bin/env python3
"""Create non-destructive rescue artifacts for a dirty OSW worktree."""

from __future__ import annotations

import argparse
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class RescuePaths:
    directory: Path
    unstaged_patch: Path
    staged_patch: Path
    untracked_manifest: Path


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


def repo_root() -> Path:
    proc = run_git(["rev-parse", "--show-toplevel"])
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "not a git repository")
    return Path(proc.stdout.strip())


def git_dir(root: Path) -> Path:
    proc = run_git(["rev-parse", "--git-dir"], cwd=root)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "cannot locate .git directory")
    path = Path(proc.stdout.strip())
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def build_rescue_paths(repo_root: Path, timestamp: str) -> RescuePaths:
    directory = repo_root / ".git" / "osw-rescue" / timestamp
    return RescuePaths(
        directory=directory,
        unstaged_patch=directory / "unstaged.patch",
        staged_patch=directory / "staged.patch",
        untracked_manifest=directory / "untracked-files.txt",
    )


def build_rescue_paths_for_git_dir(git_directory: Path, timestamp: str) -> RescuePaths:
    directory = git_directory / "osw-rescue" / timestamp
    return RescuePaths(
        directory=directory,
        unstaged_patch=directory / "unstaged.patch",
        staged_patch=directory / "staged.patch",
        untracked_manifest=directory / "untracked-files.txt",
    )


def write_command_output(
    args: Sequence[str],
    destination: Path,
    root: Path,
    *,
    text: bool = True,
) -> None:
    proc = run_git(args, cwd=root, text=text)
    data = proc.stdout if text else proc.stdout
    if isinstance(data, bytes):
        destination.write_bytes(data)
    else:
        destination.write_text(data, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")


def write_rescue(paths: RescuePaths, root: Path) -> None:
    paths.directory.mkdir(parents=True, exist_ok=False)
    write_command_output(["diff", "--binary"], paths.unstaged_patch, root)
    write_command_output(["diff", "--cached", "--binary"], paths.staged_patch, root)

    proc = run_git(["ls-files", "--others", "--exclude-standard"], cwd=root)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git ls-files failed")
    paths.untracked_manifest.write_text(proc.stdout, encoding="utf-8")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Save dirty worktree patches without resetting or cleaning."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write rescue files under .git/osw-rescue/<timestamp>.",
    )
    parser.add_argument(
        "--timestamp",
        help="Override timestamp, mainly for tests or reproducible runs.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    try:
        root = repo_root()
        timestamp = args.timestamp or datetime.now().strftime("%Y%m%d-%H%M%S")
        paths = build_rescue_paths_for_git_dir(git_dir(root), timestamp)

        print(f"Rescue directory: {paths.directory}")
        print(f"Unstaged patch: {paths.unstaged_patch}")
        print(f"Staged patch: {paths.staged_patch}")
        print(f"Untracked manifest: {paths.untracked_manifest}")

        if not args.write:
            print("[dry-run] Pass --write to create rescue files. No worktree changes made.")
            return 0

        write_rescue(paths, root)
        print(
            "[ok] Rescue files written. No reset, clean, checkout, push, "
            "or remote change performed."
        )
        return 0
    except Exception as exc:
        print(f"[fail] {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
