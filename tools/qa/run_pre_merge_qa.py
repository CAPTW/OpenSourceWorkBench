#!/usr/bin/env python3
"""Run OSW checks intended before squash merge to develop."""

from __future__ import annotations

from _common import python_executable, repo_root, run


def main() -> int:
    root = repo_root()
    checks = [
        ([python_executable(), "tools/qa/run_fast_qa.py"], "python tools/qa/run_fast_qa.py"),
        (
            [python_executable(), "tools/qa/check_docs_links.py"],
            "python tools/qa/check_docs_links.py",
        ),
        (
            [python_executable(), "tools/qa/check_scope_drift.py"],
            "python tools/qa/check_scope_drift.py",
        ),
        (
            [python_executable(), "tools/qa/check_architecture_boundaries.py"],
            "python tools/qa/check_architecture_boundaries.py",
        ),
        (
            [python_executable(), "tools/qa/check_no_solver_artifacts_committed.py"],
            "python tools/qa/check_no_solver_artifacts_committed.py",
        ),
    ]
    exit_code = 0
    for args, label in checks:
        exit_code = run(args, cwd=root, label=label) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
