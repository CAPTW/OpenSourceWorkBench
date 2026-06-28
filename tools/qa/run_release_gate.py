#!/usr/bin/env python3
"""Run the local static release-gate QA checks."""

from __future__ import annotations

from _common import python_executable, repo_root, run


def main() -> int:
    root = repo_root()
    commands: list[tuple[list[str], str]] = [
        (
            [python_executable(), "tools/qa/check_release_gate.py"],
            "python tools/qa/check_release_gate.py",
        ),
        (
            [python_executable(), "tools/qa/check_architecture_boundaries.py"],
            "python tools/qa/check_architecture_boundaries.py",
        ),
        (
            [python_executable(), "tools/qa/check_scope_drift.py"],
            "python tools/qa/check_scope_drift.py",
        ),
        (
            [python_executable(), "tools/qa/check_no_solver_artifacts_committed.py"],
            "python tools/qa/check_no_solver_artifacts_committed.py",
        ),
        (
            [python_executable(), "tools/qa/check_docs_links.py"],
            "python tools/qa/check_docs_links.py",
        ),
        (
            [python_executable(), "tools/qa/check_plugin_manifests.py"],
            "python tools/qa/check_plugin_manifests.py",
        ),
        (
            [
                python_executable(),
                "-m",
                "json.tool",
                "docs/release/functional_queue_state.json",
            ],
            "python -m json.tool docs/release/functional_queue_state.json",
        ),
    ]

    exit_code = 0
    for args, label in commands:
        exit_code = run(args, cwd=root, label=label) or exit_code
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
