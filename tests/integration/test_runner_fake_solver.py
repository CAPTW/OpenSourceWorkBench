from __future__ import annotations

import sys
import time
from pathlib import Path

from osw.solvers.runner import ExternalCommandRunner, RunStatus, TimeoutPolicy

FAKE_SOLVER = Path(__file__).parents[1] / "fixtures" / "runner" / "fake_solver.py"


def fake_solver_command(mode: str, *extra: str) -> list[str]:
    return [sys.executable, str(FAKE_SOLVER), "--mode", mode, *extra]


def test_fake_success_run(tmp_path: Path) -> None:
    result = ExternalCommandRunner().run_command(fake_solver_command("success"), cwd=tmp_path)

    assert result.status == RunStatus.COMPLETED
    assert "fake solver stdout: success" in result.log.stdout


def test_fake_failure_run(tmp_path: Path) -> None:
    result = ExternalCommandRunner().run_command(fake_solver_command("fail"), cwd=tmp_path)

    assert result.status == RunStatus.FAILED
    assert result.return_code == 7
    assert "fake solver stderr: error" in result.log.stderr


def test_fake_timeout_run(tmp_path: Path) -> None:
    runner = ExternalCommandRunner(timeout_policy=TimeoutPolicy(seconds=0.2))
    started = time.monotonic()

    result = runner.run_command(fake_solver_command("sleep"), cwd=tmp_path)

    assert result.status == RunStatus.TIMED_OUT
    assert time.monotonic() - started < 3


def test_fake_artifact_run(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "artifacts"
    result = ExternalCommandRunner().run(
        sys.executable,
        [
            str(FAKE_SOLVER),
            "--mode",
            "artifact",
            "--artifact",
            str(artifact_dir / "solver.out"),
        ],
        cwd=tmp_path,
        artifact_dir=artifact_dir,
        artifact_patterns=["solver.out"],
    )

    assert result.status == RunStatus.COMPLETED
    assert (artifact_dir / "solver.out").exists()
    assert any(artifact.path.name == "solver.out" for artifact in result.artifacts)


def test_fake_solver_helper_uses_python_executable() -> None:
    command = fake_solver_command("success")

    assert command[:2] == [sys.executable, str(FAKE_SOLVER)]
