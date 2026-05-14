from __future__ import annotations

from pathlib import Path

from osw.core.diagnostics import DiagnosticSeverity
from osw.core.run_manager import ExecutablePathRegistry
from osw.solvers.runner import RunStatus, TimeoutPolicy
from osw.solvers.su2.runner import Su2Runner


def test_su2_runner_missing_executable_is_friendly(tmp_path: Path) -> None:
    cfg_path = tmp_path / "case.cfg"
    cfg_path.write_text("SOLVER= EULER\nMESH_FILENAME= mesh.su2\n", encoding="utf-8")
    runner = Su2Runner(
        executable="osw-missing-su2-for-test",
        registry=ExecutablePathRegistry(),
        timeout_policy=TimeoutPolicy(seconds=1),
    )

    result = runner.run_config(cfg_path, artifact_dir=tmp_path / "artifacts")

    messages = [message.message for message in result.diagnostics.messages]
    diagnostic_summary = result.diagnostics.summary()
    assert result.status is RunStatus.MISSING_EXECUTABLE
    assert any(
        message.severity is DiagnosticSeverity.ERROR
        for message in result.diagnostics.messages
    )
    assert any(
        "osw-missing-su2-for-test executable was not found" in message
        for message in messages
    )
    assert "install osw-missing-su2-for-test on PATH" in diagnostic_summary
    assert "install SU2_CFD on PATH" not in diagnostic_summary
    assert any("ExecutablePathRegistry" in message for message in messages)
