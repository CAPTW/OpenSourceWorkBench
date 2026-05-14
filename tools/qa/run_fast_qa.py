#!/usr/bin/env python3
"""Run the default fast local OSW QA suite."""

from __future__ import annotations

import os
import shutil

from _common import python_executable, repo_root, run


def main() -> int:
    root = repo_root()
    commands: list[tuple[list[str], str]] = [
        ([python_executable(), "-m", "osw.cli", "--version"], "python -m osw.cli --version"),
        ([python_executable(), "-m", "osw.cli", "doctor"], "python -m osw.cli doctor"),
        (
            [python_executable(), "tools/qa/check_duplicate_test_basenames.py"],
            "python tools/qa/check_duplicate_test_basenames.py",
        ),
        (
            [python_executable(), "tools/qa/check_docs_links.py"],
            "python tools/qa/check_docs_links.py",
        ),
    ]
    if shutil.which("ruff"):
        commands.append((["ruff", "check", "src", "tests"], "ruff check src tests"))
    else:
        print("[skip] ruff check src tests: ruff not found")

    exit_code = 0
    for args, label in commands:
        exit_code = run(args, cwd=root, label=label) or exit_code

    pytest_label = "pytest tests/unit -q"
    if os.environ.get("PYTEST_CURRENT_TEST"):
        print(f"[skip] {pytest_label}: running inside pytest")
    else:
        exit_code = run(["pytest", "tests/unit", "-q"], cwd=root, label=pytest_label) or exit_code

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
