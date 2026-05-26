from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

from osw.core.run_manager import ExecutablePathRegistry
from osw.scripts.mscript.execution_policy import OctaveExecutionPolicy
from osw.scripts.mscript.octave_runner import (
    OctaveExecutionNotConfirmed,
    OctaveRunner,
    OctaveRunRequest,
    OctaveRunResult,
    OctaveRunStatus,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "mscript"


def fake_octave_executable(tmp_path: Path) -> Path:
    helper = FIXTURES / "fake_octave.py"
    if os.name == "nt":
        wrapper = tmp_path / "fake-octave.cmd"
        wrapper.write_text(
            f'@echo off\r\n"{sys.executable}" "{helper}" %*\r\n',
            encoding="utf-8",
        )
        return wrapper
    wrapper = tmp_path / "fake-octave"
    wrapper.write_text(
        f'#!/usr/bin/env sh\n"{sys.executable}" "{helper}" "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
    return wrapper


def test_module_imports_without_octave_matlab_or_pyside6() -> None:
    from osw.scripts.mscript import octave_runner

    assert octave_runner.OctaveRunner


def test_find_octave_executable_reports_missing_explicit_path() -> None:
    runner = OctaveRunner(executable="osw-missing-octave-for-test")

    resolution = runner.find_executable()

    assert not resolution.found
    assert "GNU Octave executable was not found" in resolution.diagnostics.summary()


def test_run_script_compatibility_requires_explicit_execution(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))

    try:
        runner.run_script(FIXTURES / "run_success.m", working_directory=tmp_path / "runs")
    except OctaveExecutionNotConfirmed as exc:
        assert "explicit execution" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("run_script should require explicit approval")


def test_fake_octave_success_captures_stdout_and_artifact(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))

    result = runner.run(
        OctaveRunRequest(
            FIXTURES / "run_success.m",
            working_directory=tmp_path / "runs",
            run_id="run-success",
        )
    )

    assert result.status is OctaveRunStatus.COMPLETED
    assert result.return_code == 0
    assert "fake octave stdout" in result.stdout
    assert any(artifact.path.name == "result.txt" for artifact in result.artifacts)
    assert Path(result.workspace_dir).is_relative_to(tmp_path)


def test_fake_octave_failure_captures_stderr_and_return_code(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))

    result = runner.run(
        OctaveRunRequest(
            FIXTURES / "run_error.m",
            working_directory=tmp_path / "runs",
            run_id="run-error",
        )
    )

    assert result.status is OctaveRunStatus.FAILED
    assert result.return_code == 7
    assert "intentional failure" in result.stderr


def test_fake_octave_timeout_returns_timed_out(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))

    result = runner.run(
        OctaveRunRequest(
            FIXTURES / "run_long_sleep.m",
            working_directory=tmp_path / "runs",
            run_id="run-timeout",
            policy=OctaveExecutionPolicy(timeout_seconds=0.2),
        )
    )

    assert result.status is OctaveRunStatus.TIMED_OUT
    assert "timed out" in result.diagnostics.summary().lower()


def test_fake_octave_artifact_collection_works(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))

    result = runner.run(
        OctaveRunRequest(
            FIXTURES / "run_artifact_csv.m",
            working_directory=tmp_path / "runs",
            run_id="run-artifact",
        )
    )

    assert result.status is OctaveRunStatus.COMPLETED
    assert any(artifact.path.name == "artifact.csv" for artifact in result.artifacts)


def test_missing_script_and_unsupported_extension_are_friendly(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))
    text_path = tmp_path / "notes.txt"
    text_path.write_text("x = 1;", encoding="utf-8")

    missing = runner.run(OctaveRunRequest(tmp_path / "missing.m"))
    unsupported = runner.run(OctaveRunRequest(text_path))

    assert missing.status is OctaveRunStatus.FAILED
    assert "does not exist" in missing.diagnostics.summary()
    assert unsupported.status is OctaveRunStatus.FAILED
    assert "Only .m scripts" in unsupported.diagnostics.summary()


def test_missing_octave_diagnostic_is_friendly(tmp_path: Path) -> None:
    runner = OctaveRunner(executable="osw-missing-octave-for-test")

    result = runner.run(OctaveRunRequest(FIXTURES / "run_success.m", working_directory=tmp_path))

    assert result.status is OctaveRunStatus.MISSING_EXECUTABLE
    assert "GNU Octave executable was not found" in result.diagnostics.summary()


def test_high_and_blocked_scripts_are_not_executed_by_default(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))

    high = runner.run(
        OctaveRunRequest(
            FIXTURES / "dangerous_system.m",
            working_directory=tmp_path / "runs",
            run_id="high",
        )
    )
    blocked = runner.run(
        OctaveRunRequest(
            FIXTURES / "simulink_out_of_scope.m",
            working_directory=tmp_path / "runs",
            run_id="blocked",
        )
    )

    assert high.status is OctaveRunStatus.BLOCKED_BY_SAFETY
    assert blocked.status is OctaveRunStatus.BLOCKED_BY_SAFETY
    assert not (tmp_path / "runs" / "high" / "result.txt").exists()
    assert not (tmp_path / "runs" / "blocked" / "result.txt").exists()
    assert "high-risk" in high.diagnostics.summary()
    assert "blocked" in blocked.diagnostics.summary().lower()


def test_allow_high_risk_still_blocks_out_of_scope_findings(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))

    high = runner.run(
        OctaveRunRequest(
            FIXTURES / "dangerous_system.m",
            working_directory=tmp_path / "runs",
            run_id="high-allowed",
            policy=OctaveExecutionPolicy(allow_high_risk=True),
        )
    )
    blocked = runner.run(
        OctaveRunRequest(
            FIXTURES / "simulink_out_of_scope.m",
            working_directory=tmp_path / "runs",
            run_id="blocked-default",
            policy=OctaveExecutionPolicy(allow_high_risk=True),
        )
    )

    assert high.status is OctaveRunStatus.COMPLETED
    assert blocked.status is OctaveRunStatus.BLOCKED_BY_SAFETY


def test_original_fixture_directory_is_not_mutated(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))
    before = {path.name for path in FIXTURES.iterdir()}

    result = runner.run(
        OctaveRunRequest(
            FIXTURES / "run_success.m",
            working_directory=tmp_path / "runs",
            run_id="mutate-check",
        )
    )

    assert result.status is OctaveRunStatus.COMPLETED
    assert {path.name for path in FIXTURES.iterdir()} == before
    assert not (FIXTURES / "result.txt").exists()


def test_configured_registry_path_is_used(tmp_path: Path) -> None:
    fake_octave = fake_octave_executable(tmp_path)
    registry = ExecutablePathRegistry().register("octave", fake_octave)
    runner = OctaveRunner(executable_registry=registry)

    result = runner.run(
        OctaveRunRequest(
            FIXTURES / "run_success.m",
            working_directory=tmp_path / "runs",
            run_id="registry",
        )
    )

    assert result.status is OctaveRunStatus.COMPLETED
    assert result.command[0] == str(fake_octave.resolve())


def test_octave_run_result_serializes_to_json(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=fake_octave_executable(tmp_path))
    result = runner.run(
        OctaveRunRequest(
            FIXTURES / "run_success.m",
            working_directory=tmp_path / "runs",
            run_id="serialize",
        )
    )

    restored = OctaveRunResult.from_dict(json.loads(json.dumps(result.to_dict())))

    assert restored.status is OctaveRunStatus.COMPLETED
    assert restored.stdout == result.stdout
    assert restored.artifacts
