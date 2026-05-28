from __future__ import annotations

import os
import sys
from pathlib import Path

from osw.core.executables import ExecutablePathRegistry
from osw.solvers.openfoam.case_generator import default_cavity_request, generate_openfoam_case
from osw.solvers.openfoam.model import OpenFOAMRunPolicy, OpenFOAMRunStatus
from osw.solvers.openfoam.runner import (
    OpenFOAMRunner,
    find_openfoam_executable,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "openfoam"


def test_find_openfoam_executable_missing_is_friendly() -> None:
    resolution = find_openfoam_executable("osw-missing-openfoam-test-executable")

    assert not resolution.found
    assert "OpenFOAM executable" in resolution.diagnostics.summary()


def test_fake_solver_success_captures_stdout_and_artifacts(tmp_path: Path) -> None:
    case_dir = _write_case(tmp_path)
    runner = OpenFOAMRunner(executable_registry=_registry_with_fake(tmp_path, "success"))

    result = runner.run_case(case_dir, "icoFoam", OpenFOAMRunPolicy(timeout_seconds=5.0))

    assert result.status is OpenFOAMRunStatus.COMPLETED
    assert "Solving for Ux" in result.stdout
    assert result.case_dir != case_dir
    assert (case_dir / "log.icoFoam").exists() is False
    roles = {artifact.role for artifact in result.artifacts}
    assert "solver_log" in roles
    assert "stdout_log" in roles
    assert result.residual_summary is not None
    assert result.residual_summary.final_residuals["p"] == 0.04


def test_fake_solver_failure_captures_stderr(tmp_path: Path) -> None:
    case_dir = _write_case(tmp_path)
    runner = OpenFOAMRunner(executable_registry=_registry_with_fake(tmp_path, "fail"))

    result = runner.run_case(case_dir, "icoFoam", OpenFOAMRunPolicy(timeout_seconds=5.0))

    assert result.status is OpenFOAMRunStatus.FAILED
    assert result.return_code == 3
    assert "fatal error" in result.stderr.lower()


def test_fake_solver_timeout(tmp_path: Path) -> None:
    case_dir = _write_case(tmp_path)
    runner = OpenFOAMRunner(executable_registry=_registry_with_fake(tmp_path, "sleep"))

    result = runner.run_case(case_dir, "icoFoam", OpenFOAMRunPolicy(timeout_seconds=0.1))

    assert result.status is OpenFOAMRunStatus.TIMED_OUT
    assert result.diagnostics.has_errors


def test_partial_solver_log_returns_completed_with_warning_summary(tmp_path: Path) -> None:
    case_dir = _write_case(tmp_path)
    runner = OpenFOAMRunner(executable_registry=_registry_with_fake(tmp_path, "partial"))

    result = runner.run_case(case_dir, "icoFoam", OpenFOAMRunPolicy(timeout_seconds=5.0))

    assert result.status is OpenFOAMRunStatus.COMPLETED
    assert result.residual_summary is not None
    assert result.residual_summary.final_residuals["Ux"] == 0.02


def test_missing_case_returns_friendly_diagnostic(tmp_path: Path) -> None:
    runner = OpenFOAMRunner(executable_registry=_registry_with_fake(tmp_path, "success"))

    result = runner.run_case(tmp_path / "missing", "icoFoam")

    assert result.status is OpenFOAMRunStatus.MISSING_CASE
    assert "case directory does not exist" in result.diagnostics.summary()


def test_run_result_serializes_to_json(tmp_path: Path) -> None:
    case_dir = _write_case(tmp_path)
    runner = OpenFOAMRunner(executable_registry=_registry_with_fake(tmp_path, "success"))

    result = runner.run_case(case_dir, "icoFoam", OpenFOAMRunPolicy(timeout_seconds=5.0))
    payload = result.to_dict()

    assert payload["status"] == "completed"
    assert payload["residual_summary"]["final_residuals"]["Ux"] == 0.01


def _write_case(tmp_path: Path) -> Path:
    result = generate_openfoam_case(default_cavity_request(tmp_path / "cases"))
    assert result.status == "ok"
    return result.case_dir


def _registry_with_fake(tmp_path: Path, mode: str) -> ExecutablePathRegistry:
    wrapper = _fake_solver_wrapper(tmp_path, mode)
    return ExecutablePathRegistry().register("icoFoam", wrapper)


def _fake_solver_wrapper(tmp_path: Path, mode: str) -> Path:
    fake = FIXTURES / "fake_openfoam_solver.py"
    if os.name == "nt":
        wrapper = tmp_path / f"fake_openfoam_{mode}.cmd"
        wrapper.write_text(
            f"@echo off\r\nset OSW_FAKE_OPENFOAM_MODE={mode}\r\n"
            f"\"{sys.executable}\" \"{fake}\" %*\r\n",
            encoding="utf-8",
        )
        return wrapper
    wrapper = tmp_path / f"fake_openfoam_{mode}"
    wrapper.write_text(
        "#!/usr/bin/env sh\n"
        f"OSW_FAKE_OPENFOAM_MODE={mode} \"{sys.executable}\" \"{fake}\" \"$@\"\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    return wrapper
