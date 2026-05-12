from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_tool(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_scope_drift_flags_forbidden_positive_claim() -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", "Simulink support")

    assert proc.returncode != 0
    assert "Simulink" in proc.stdout


def test_scope_drift_allows_in_scope_adapter_text() -> None:
    proc = run_tool("tools/qa/check_scope_drift.py", "--text", "Gmsh adapter")

    assert proc.returncode == 0


def test_architecture_checker_runs_on_current_repo() -> None:
    proc = run_tool("tools/qa/check_architecture_boundaries.py")

    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_git_clean_reports_branch_and_status() -> None:
    proc = run_tool("tools/qa/check_git_clean.py", "--allow-dirty")

    assert proc.returncode == 0
    assert "branch:" in proc.stdout
    assert "status:" in proc.stdout


def test_fast_qa_runner_handles_available_checks() -> None:
    proc = run_tool("tools/qa/run_fast_qa.py")

    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "pytest tests/unit -q" in proc.stdout
