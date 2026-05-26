from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from osw.core.diagnostics import DiagnosticCode
from osw.core.run_manager import ExecutablePathRegistry, RunManager
from osw.solvers.runner import (
    ExternalCommandRunner,
    RunRequest,
    RunResult,
    RunStatus,
    TimeoutPolicy,
)


def test_empty_command_fails_friendly(tmp_path: Path) -> None:
    result = ExternalCommandRunner().run(RunRequest([], cwd=tmp_path))

    assert result.status == RunStatus.FAILED
    assert result.diagnostics.has_errors
    assert "Run request command is empty" in result.diagnostics.summary()


def test_invalid_cwd_fails_friendly(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    result = ExternalCommandRunner().run_command([sys.executable, "-V"], cwd=missing)

    assert result.status == RunStatus.FAILED
    assert result.diagnostics.errors()[0].code == DiagnosticCode.INVALID_WORKING_DIRECTORY.value
    assert not missing.exists()


def test_successful_command_captures_stdout(tmp_path: Path) -> None:
    result = ExternalCommandRunner().run_command(
        [sys.executable, "-c", "print('runner stdout')"],
        cwd=tmp_path,
    )

    assert result.status == RunStatus.COMPLETED
    assert result.return_code == 0
    assert result.returncode == 0
    assert "runner stdout" in result.log.stdout


def test_stderr_is_captured(tmp_path: Path) -> None:
    result = ExternalCommandRunner().run_command(
        [sys.executable, "-c", "import sys; print('stderr line', file=sys.stderr)"],
        cwd=tmp_path,
    )

    assert result.status == RunStatus.COMPLETED
    assert "stderr line" in result.log.stderr
    assert "stderr line" in result.log.combined


def test_nonzero_exit_returns_failed_status(tmp_path: Path) -> None:
    result = ExternalCommandRunner().run_command(
        [sys.executable, "-c", "import sys; print('bad', file=sys.stderr); sys.exit(7)"],
        cwd=tmp_path,
    )

    assert result.status == RunStatus.FAILED
    assert result.return_code == 7
    assert "bad" in result.log.stderr


def test_timeout_returns_timed_out_status(tmp_path: Path) -> None:
    runner = ExternalCommandRunner(timeout_policy=TimeoutPolicy(seconds=0.2))
    started = time.monotonic()

    result = runner.run_command(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        cwd=tmp_path,
    )

    assert result.status == RunStatus.TIMED_OUT
    assert time.monotonic() - started < 3
    assert "timed out" in result.diagnostics.summary().lower()


def test_result_serializes_to_json(tmp_path: Path) -> None:
    result = ExternalCommandRunner().run_command(
        [sys.executable, "-c", "print('json')"],
        cwd=tmp_path,
    )

    restored = RunResult.from_dict(json.loads(json.dumps(result.to_dict())))

    assert restored.status == result.status
    assert restored.log.stdout == result.log.stdout


def test_artifact_collection_works_and_missing_pattern_warns(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    result = ExternalCommandRunner().run(
        sys.executable,
        ["-c", "from pathlib import Path; Path('result.dat').write_text('ok')"],
        cwd=tmp_path,
        artifact_dir=artifact_dir,
        artifact_patterns=["../result.dat", "*.missing"],
    )

    assert result.status == RunStatus.COMPLETED
    assert any(artifact.path.name == "result.dat" for artifact in result.artifacts)
    assert any(
        message.code == DiagnosticCode.ARTIFACT_MISSING.value
        for message in result.diagnostics.messages
    )


def test_registry_reports_missing_executable_without_crashing(tmp_path: Path) -> None:
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


def test_runner_rejects_invalid_timeout_policy() -> None:
    policy = TimeoutPolicy(seconds=0)

    assert policy.diagnostics().has_errors
    assert "timeout" in policy.diagnostics().summary().lower()


def test_configured_registry_path_is_used(tmp_path: Path) -> None:
    registry = ExecutablePathRegistry().register("python", sys.executable)
    runner = ExternalCommandRunner(registry=registry)

    result = runner.run("python", ["-c", "print('configured')"], cwd=tmp_path)

    assert result.status == RunStatus.COMPLETED
    assert result.command[0] == str(Path(sys.executable).resolve())


def test_run_manager_creates_run_dir_and_summary(tmp_path: Path) -> None:
    manager = RunManager()
    run_dir = manager.create_run_dir(tmp_path, run_id="run_test")
    result = ExternalCommandRunner().run_command(
        [sys.executable, "-c", "print('managed')"],
        cwd=tmp_path,
    )
    summary_path = run_dir / "summary.json"

    manager.save_result_summary(result, summary_path)
    restored = manager.load_result_summary(summary_path)

    assert run_dir.exists()
    assert restored.status == RunStatus.COMPLETED
