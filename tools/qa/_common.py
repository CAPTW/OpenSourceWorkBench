#!/usr/bin/env python3
"""Shared helpers for OSW local QA scripts."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(args: list[str], *, cwd: Path, label: str | None = None) -> int:
    title = label or " ".join(args)
    print(f"[run] {title}")
    proc = subprocess.run(args, cwd=cwd, text=True, check=False)
    if proc.returncode == 0:
        print(f"[ok] {title}")
    else:
        print(f"[fail] {title}: exit {proc.returncode}")
    return proc.returncode


def capture(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, check=False)


def repo_root() -> Path:
    proc = capture(["git", "rev-parse", "--show-toplevel"], cwd=Path.cwd())
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "not a git repository")
    return Path(proc.stdout.strip())


def git_lines(args: list[str], *, cwd: Path) -> list[str]:
    proc = capture(["git", *args], cwd=cwd)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def existing_paths(paths: list[str], *, root: Path) -> list[Path]:
    return [root / item for item in paths if (root / item).exists()]


def text_files(paths: list[Path]) -> list[Path]:
    allowed = {".md", ".py", ".toml", ".yml", ".yaml", ".json", ".txt"}
    return [path for path in paths if path.is_file() and path.suffix.lower() in allowed]


def changed_files(base: str, *, root: Path) -> list[str]:
    proc = capture(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=root)
    if proc.returncode != 0:
        proc = capture(["git", "diff", "--name-only"], cwd=root)
    return [line for line in proc.stdout.splitlines() if line.strip()]


def build_base_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base", default="develop", help="Base branch for changed-file checks.")


def main_result(code: int) -> int:
    return 0 if code == 0 else 1


def python_executable() -> str:
    return sys.executable
