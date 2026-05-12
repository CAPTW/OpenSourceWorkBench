from __future__ import annotations

import os
import stat
import sys
import time
from pathlib import Path

from osw.core.run_manager import ExecutablePathRegistry
from osw.solvers.calculix.ccx_runner import CalculixCcxRunner
from osw.solvers.runner import RunStatus, TimeoutPolicy


def write_input_deck(tmp_path: Path) -> Path:
    path = tmp_path / "cantilever.inp"
    path.write_text(
        "\n".join(
            [
                "*HEADING",
                "fake ccx test deck",
                "*NODE",
                "1, 0, 0, 0",
                "*END STEP",
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_fake_ccx(tmp_path: Path, *, slow: bool = False, exit_code: int = 0) -> Path:
    if os.name == "nt":
        fake_path = tmp_path / "fake-ccx.cmd"
        body = [
            "@echo off",
            "echo fake ccx stdout for %1",
            "echo fake ccx stderr for %1 1>&2",
        ]
        if slow:
            body.append(f'"{sys.executable}" -c "import time; time.sleep(5)"')
        body.extend(
            [
                "echo fake dat>%1.dat",
                "echo fake frd>%1.frd",
                "echo fake sta>%1.sta",
                f"exit /b {exit_code}",
            ]
        )
        fake_path.write_text("\n".join(body), encoding="utf-8")
    else:
        fake_path = tmp_path / "fake-ccx"
        sleep_line = f'"{sys.executable}" -c "import time; time.sleep(5)"' if slow else ":"
        fake_path.write_text(
            "\n".join(
                [
                    "#!/usr/bin/env sh",
                    "echo fake ccx stdout for \"$1\"",
                    "echo fake ccx stderr for \"$1\" >&2",
                    sleep_line,
                    "echo fake dat > \"$1.dat\"",
                    "echo fake frd > \"$1.frd\"",
                    "echo fake sta > \"$1.sta\"",
                    f"exit {exit_code}",
                ]
            ),
            encoding="utf-8",
        )
        fake_path.chmod(fake_path.stat().st_mode | stat.S_IXUSR)
    return fake_path


def test_fake_ccx_runs_in_case_directory_and_records_artifacts(tmp_path: Path) -> None:
    deck = write_input_deck(tmp_path)
    runner = CalculixCcxRunner(executable=write_fake_ccx(tmp_path))

    result = runner.run_input_deck(deck, artifact_dir=tmp_path / "artifacts")

    assert result.status == RunStatus.COMPLETED
    assert result.cwd == tmp_path.resolve()
    assert result.returncode == 0
    assert result.command[-1] == "cantilever"
    assert "fake ccx stdout" in result.log.stdout
    assert "fake ccx stderr" in result.log.stderr
    assert (tmp_path / "cantilever.dat").exists()
    assert (tmp_path / "cantilever.frd").exists()
    assert (tmp_path / "cantilever.sta").exists()
    assert (result.artifact_dir / "stdout.txt").exists()
    assert (result.artifact_dir / "stderr.txt").exists()
    assert any(artifact.kind == "calculix_dat" for artifact in result.artifacts)
    assert any(artifact.kind == "calculix_frd" for artifact in result.artifacts)
    assert any(artifact.kind == "calculix_sta" for artifact in result.artifacts)


def test_missing_ccx_executable_has_friendly_diagnostic(tmp_path: Path) -> None:
    deck = write_input_deck(tmp_path)
    runner = CalculixCcxRunner(executable="osw-missing-ccx-for-test")

    result = runner.run_input_deck(deck, artifact_dir=tmp_path / "artifacts")

    assert result.status == RunStatus.MISSING_EXECUTABLE
    assert result.diagnostics.has_errors
    assert "CalculiX ccx executable was not found" in result.diagnostics.summary()
    assert "ExecutablePathRegistry" in result.diagnostics.summary()


def test_ccx_timeout_is_reported_and_process_is_terminated(tmp_path: Path) -> None:
    deck = write_input_deck(tmp_path)
    runner = CalculixCcxRunner(
        executable=write_fake_ccx(tmp_path, slow=True),
        timeout_policy=TimeoutPolicy(seconds=0.2),
    )
    started = time.monotonic()

    result = runner.run_input_deck(deck, artifact_dir=tmp_path / "artifacts")

    assert result.status == RunStatus.TIMED_OUT
    assert time.monotonic() - started < 3
    assert result.diagnostics.has_errors
    assert "timed out" in result.diagnostics.summary().lower()


def test_configured_registry_path_is_used_for_ccx(tmp_path: Path) -> None:
    deck = write_input_deck(tmp_path)
    fake_ccx = write_fake_ccx(tmp_path)
    registry = ExecutablePathRegistry().register("ccx", fake_ccx)
    runner = CalculixCcxRunner(registry=registry)

    result = runner.run_input_deck(deck, artifact_dir=tmp_path / "artifacts")

    assert result.status == RunStatus.COMPLETED
    assert result.command[0] == str(fake_ccx.resolve())
