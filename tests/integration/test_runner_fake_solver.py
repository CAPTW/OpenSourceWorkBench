from __future__ import annotations

import sys
import time

from osw.solvers.runner import ExternalCommandRunner, RunStatus, TimeoutPolicy


def fake_solver_command(*statements: str) -> list[str]:
    return [sys.executable, "-c", "; ".join(statements)]


def test_fake_solver_captures_stdout_and_stderr(tmp_path) -> None:
    runner = ExternalCommandRunner()
    artifact_dir = tmp_path / "artifacts"

    result = runner.run(
        sys.executable,
        [
            "-c",
            (
                "import sys; "
                "print('solver stdout line'); "
                "print('solver stderr line', file=sys.stderr)"
            ),
        ],
        cwd=tmp_path,
        artifact_dir=artifact_dir,
    )

    assert result.status == RunStatus.COMPLETED
    assert result.returncode == 0
    assert "solver stdout line" in result.log.stdout
    assert "solver stderr line" in result.log.stderr
    assert artifact_dir.exists()
    assert (artifact_dir / "stdout.txt").read_text(encoding="utf-8").strip()
    assert (artifact_dir / "stderr.txt").read_text(encoding="utf-8").strip()
    assert any(artifact.kind == "stdout" for artifact in result.artifacts)


def test_fake_solver_failure_is_reported_without_exception(tmp_path) -> None:
    runner = ExternalCommandRunner()

    result = runner.run(
        sys.executable,
        ["-c", "import sys; print('bad input', file=sys.stderr); raise SystemExit(7)"],
        cwd=tmp_path,
        artifact_dir=tmp_path / "artifacts",
    )

    assert result.status == RunStatus.FAILED
    assert result.returncode == 7
    assert "bad input" in result.log.stderr
    assert result.diagnostics.has_errors


def test_fake_solver_timeout_terminates_process(tmp_path) -> None:
    runner = ExternalCommandRunner(timeout_policy=TimeoutPolicy(seconds=0.2))
    started = time.monotonic()

    result = runner.run(
        sys.executable,
        ["-c", "import time; time.sleep(5)"],
        cwd=tmp_path,
        artifact_dir=tmp_path / "artifacts",
    )

    assert result.status == RunStatus.TIMED_OUT
    assert time.monotonic() - started < 3
    assert result.diagnostics.has_errors
    assert "timed out" in result.diagnostics.summary().lower()


def test_fake_solver_helper_uses_python_executable() -> None:
    command = fake_solver_command("print('ok')")

    assert command[:2] == [sys.executable, "-c"]
