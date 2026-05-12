from __future__ import annotations

import os
import stat
import sys
import time
from pathlib import Path

import pytest

from osw.core.run_manager import ExecutablePathRegistry
from osw.scripts.mscript.octave_runner import (
    OctaveExecutionNotConfirmed,
    OctaveRunner,
)
from osw.solvers.runner import RunStatus, TimeoutPolicy


def write_fake_octave(tmp_path: Path, *, slow: bool = False, exit_code: int = 0) -> Path:
    if os.name == "nt":
        fake_path = tmp_path / "fake-octave.cmd"
        body = [
            "@echo off",
            "echo fake octave stdout",
            "echo fake octave stderr 1>&2",
        ]
        if slow:
            body.append(f'"{sys.executable}" -c "import time; time.sleep(5)"')
        body.extend(
            [
                "echo generated artifact> figure.txt",
                f"exit /b {exit_code}",
            ]
        )
        fake_path.write_text("\n".join(body), encoding="utf-8")
    else:
        fake_path = tmp_path / "fake-octave"
        sleep_line = f'"{sys.executable}" -c "import time; time.sleep(5)"' if slow else ":"
        fake_path.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env sh",
                    "echo fake octave stdout",
                    "echo fake octave stderr >&2",
                    sleep_line,
                    "echo generated artifact > figure.txt",
                    f"exit {exit_code}",
                ]
            ),
            encoding="utf-8",
        )
        fake_path.chmod(fake_path.stat().st_mode | stat.S_IXUSR)
    return fake_path


def write_safe_script(tmp_path: Path) -> Path:
    script_path = tmp_path / "plot_demo.m"
    script_path.write_text(
        "\n".join(
            [
                "x = linspace(0, 1, 5);",
                "y = sin(x);",
                "plot(x, y);",
            ]
        ),
        encoding="utf-8",
    )
    return script_path


def test_octave_runner_requires_explicit_execution(tmp_path: Path) -> None:
    runner = OctaveRunner(executable=write_fake_octave(tmp_path))

    with pytest.raises(OctaveExecutionNotConfirmed, match="explicit execution"):
        runner.run_script(
            write_safe_script(tmp_path),
            artifact_dir=tmp_path / "artifacts",
        )


def test_fake_octave_captures_stdout_stderr_and_artifacts(tmp_path: Path) -> None:
    fake_octave = write_fake_octave(tmp_path)
    runner = OctaveRunner(executable=fake_octave)

    result = runner.run_script(
        write_safe_script(tmp_path),
        artifact_dir=tmp_path / "artifacts",
        allow_execution=True,
    )

    assert result.status == RunStatus.COMPLETED
    assert result.returncode == 0
    assert "fake octave stdout" in result.log.stdout
    assert "fake octave stderr" in result.log.stderr
    assert (result.artifact_dir / "stdout.txt").exists()
    assert any(artifact.path.name == "figure.txt" for artifact in result.artifacts)
    assert (result.artifact_dir / "octave_workspace" / "figure.txt").exists()


def test_octave_runner_timeout_terminates_process(tmp_path: Path) -> None:
    fake_octave = write_fake_octave(tmp_path, slow=True)
    runner = OctaveRunner(
        executable=fake_octave,
        timeout_policy=TimeoutPolicy(seconds=0.2),
    )
    started = time.monotonic()

    result = runner.run_script(
        write_safe_script(tmp_path),
        artifact_dir=tmp_path / "artifacts",
        allow_execution=True,
    )

    assert result.status == RunStatus.TIMED_OUT
    assert time.monotonic() - started < 3
    assert "timed out" in result.diagnostics.summary().lower()


def test_missing_octave_diagnostic_is_friendly(tmp_path: Path) -> None:
    runner = OctaveRunner(executable="osw-missing-octave-for-test")

    result = runner.run_script(
        write_safe_script(tmp_path),
        artifact_dir=tmp_path / "artifacts",
        allow_execution=True,
    )

    assert result.status == RunStatus.MISSING_EXECUTABLE
    assert result.diagnostics.has_errors
    assert "GNU Octave executable was not found" in result.diagnostics.summary()


def test_configured_registry_path_is_used(tmp_path: Path) -> None:
    fake_octave = write_fake_octave(tmp_path)
    registry = ExecutablePathRegistry().register("octave", fake_octave)
    runner = OctaveRunner(registry=registry)

    result = runner.run_script(
        write_safe_script(tmp_path),
        artifact_dir=tmp_path / "artifacts",
        allow_execution=True,
    )

    assert result.status == RunStatus.COMPLETED
    assert result.command[0] == str(fake_octave.resolve())
