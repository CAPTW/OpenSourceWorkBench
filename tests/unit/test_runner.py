from __future__ import annotations

import sys

from osw.core.run_manager import ExecutablePathRegistry
from osw.solvers.log_parser import LogSeverity, parse_run_log
from osw.solvers.runner import ExternalCommandRunner, RunStatus, TimeoutPolicy


def test_registry_resolves_registered_executable() -> None:
    registry = ExecutablePathRegistry()
    registry.register("python", sys.executable)

    result = registry.resolve("python")

    assert result.found
    assert result.path is not None
    assert result.path.exists()
    assert not result.diagnostics.has_errors


def test_registry_reports_friendly_missing_executable() -> None:
    result = ExecutablePathRegistry().resolve("osw-missing-executable-for-test")

    assert not result.found
    assert result.path is None
    assert result.diagnostics.has_errors
    assert "Executable not found" in result.diagnostics.summary()
    assert "osw-missing-executable-for-test" in result.diagnostics.summary()


def test_runner_rejects_invalid_timeout_policy() -> None:
    policy = TimeoutPolicy(seconds=0)

    assert policy.diagnostics().has_errors
    assert "timeout" in policy.diagnostics().summary().lower()


def test_runner_reports_missing_executable_without_crashing(tmp_path) -> None:
    runner = ExternalCommandRunner()

    result = runner.run(
        "osw-missing-executable-for-test",
        cwd=tmp_path,
        artifact_dir=tmp_path / "artifacts",
    )

    assert result.status == RunStatus.MISSING_EXECUTABLE
    assert result.returncode is None
    assert result.diagnostics.has_errors
    assert "Executable not found" in result.diagnostics.summary()
    assert result.artifact_dir.exists()


def test_log_parser_classifies_warnings_and_errors() -> None:
    findings = parse_run_log("line 1\nwarning: mesh quality\nfatal error: no input\n")

    assert [finding.severity for finding in findings] == [
        LogSeverity.WARNING,
        LogSeverity.ERROR,
    ]
    assert findings[0].line_number == 2
    assert findings[1].line_number == 3
