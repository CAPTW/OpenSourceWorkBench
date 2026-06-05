from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path

from osw.core.run_manager import ExecutablePathRegistry
from osw.solvers.calculix.runner import (
    CalculiXRunner,
    CalculiXRunPolicy,
    CalculiXRunRequest,
    CalculiXRunResult,
    CalculiXRunStatus,
    find_ccx_executable,
)

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "calculix"
SIMPLE_DECK = FIXTURE_DIR / "simple_valid.inp"
FAKE_CCX = FIXTURE_DIR / "fake_ccx.py"


class FakeCalculiXRunner(CalculiXRunner):
    """Run the fake ccx fixture as the direct child process under test."""

    def __init__(self, mode: str) -> None:
        registry = ExecutablePathRegistry().register("ccx", sys.executable)
        super().__init__(executable_registry=registry)
        self._mode = mode

    def build_command(
        self,
        request: CalculiXRunRequest,
        case_dir: str | Path,
        ccx_path: str | Path,
        job_name: str | None = None,
    ) -> list[str]:
        del request, case_dir
        return [str(ccx_path), str(FAKE_CCX), "--mode", self._mode, job_name or "calculix"]


def runner_with_fake_ccx(tmp_path: Path, mode: str) -> CalculiXRunner:
    del tmp_path
    return FakeCalculiXRunner(mode)


def test_module_imports_without_ccx_or_pyside6() -> None:
    module = importlib.import_module("osw.solvers.calculix.runner")

    assert hasattr(module, "CalculiXRunner")


def test_find_ccx_executable_missing_has_friendly_diagnostic(tmp_path: Path) -> None:
    registry = ExecutablePathRegistry().register("ccx", tmp_path / "missing-ccx")

    resolution = find_ccx_executable(registry)

    assert not resolution.found
    assert resolution.diagnostics.has_errors
    assert "CalculiX executable `ccx` was not found" in resolution.diagnostics.summary()
    assert "Plugin Manager" in resolution.diagnostics.summary()


def test_fake_ccx_success_uses_isolated_case_dir_and_collects_artifacts(
    tmp_path: Path,
) -> None:
    case_dir = tmp_path / "case"
    runner = runner_with_fake_ccx(tmp_path, "success")

    result = runner.run_input_deck(SIMPLE_DECK, case_dir=case_dir)

    assert result.status is CalculiXRunStatus.COMPLETED
    assert result.case_dir == case_dir.resolve()
    assert result.input_deck_path == SIMPLE_DECK
    assert result.return_code == 0
    assert result.command[-1] == "simple_valid"
    assert "fake ccx stdout" in result.stdout
    assert "fake ccx stderr" in result.stderr
    assert (case_dir / "simple_valid.inp").exists()
    assert (case_dir / "simple_valid.dat").exists()
    assert (case_dir / "simple_valid.frd").exists()
    assert (case_dir / "simple_valid.sta").exists()
    assert not (SIMPLE_DECK.parent / "simple_valid.dat").exists()
    roles = {artifact.role for artifact in result.artifacts}
    assert {"input_deck", "dat_result", "frd_result", "status"} <= roles
    assert {"stdout_log", "stderr_log", "run_summary"} <= roles


def test_fake_ccx_failure_captures_stderr_and_nonzero_return_code(tmp_path: Path) -> None:
    runner = runner_with_fake_ccx(tmp_path, "fail")

    result = runner.run_input_deck(SIMPLE_DECK, case_dir=tmp_path / "case")

    assert result.status is CalculiXRunStatus.FAILED
    assert result.return_code == 7
    assert "fake ccx stderr" in result.stderr
    assert result.diagnostics.has_errors
    assert "ccx-run-failed" in result.diagnostics.summary()


def test_fake_ccx_timeout_returns_timed_out(tmp_path: Path) -> None:
    runner = runner_with_fake_ccx(tmp_path, "sleep")
    started = time.monotonic()

    result = runner.run_input_deck(
        SIMPLE_DECK,
        case_dir=tmp_path / "case",
        policy=CalculiXRunPolicy(timeout_seconds=0.2, kill_grace_seconds=0.1),
    )

    assert result.status is CalculiXRunStatus.TIMED_OUT
    assert time.monotonic() - started < 4
    assert result.diagnostics.has_errors
    assert "timed out" in result.diagnostics.summary().lower()


def test_fake_ccx_partial_artifacts_warns_without_crashing(tmp_path: Path) -> None:
    runner = runner_with_fake_ccx(tmp_path, "partial")

    result = runner.run_input_deck(SIMPLE_DECK, case_dir=tmp_path / "case")

    assert result.status is CalculiXRunStatus.COMPLETED
    assert any(artifact.role == "status" for artifact in result.artifacts)
    assert result.diagnostics.has_warnings
    assert "expected artifact is missing" in result.diagnostics.summary()


def test_missing_input_deck_gives_friendly_diagnostic(tmp_path: Path) -> None:
    runner = runner_with_fake_ccx(tmp_path, "success")

    result = runner.run_input_deck(tmp_path / "missing.inp", case_dir=tmp_path / "case")

    assert result.status is CalculiXRunStatus.MISSING_INPUT_DECK
    assert result.diagnostics.has_errors
    assert "does not exist" in result.diagnostics.summary()


def test_invalid_extension_gives_friendly_diagnostic(tmp_path: Path) -> None:
    deck = tmp_path / "simple.txt"
    deck.write_text("*HEADING\n", encoding="utf-8")
    runner = runner_with_fake_ccx(tmp_path, "success")

    result = runner.run_input_deck(deck, case_dir=tmp_path / "case")

    assert result.status is CalculiXRunStatus.FAILED
    assert result.diagnostics.has_errors
    assert "expects a .inp input deck" in result.diagnostics.summary()


def test_missing_ccx_run_result_is_serializable(tmp_path: Path) -> None:
    registry = ExecutablePathRegistry().register("ccx", tmp_path / "missing-ccx")
    runner = CalculiXRunner(executable_registry=registry)

    result = runner.run_input_deck(SIMPLE_DECK, case_dir=tmp_path / "case")
    payload = result.to_dict()
    restored = CalculiXRunResult.from_dict(payload)

    assert result.status is CalculiXRunStatus.MISSING_EXECUTABLE
    assert restored.status is CalculiXRunStatus.MISSING_EXECUTABLE
    assert restored.job_name == "simple_valid"
    assert json.loads(json.dumps(payload))["status"] == "missing_executable"


def test_request_round_trip_and_no_shell_command(tmp_path: Path) -> None:
    request = CalculiXRunRequest(
        SIMPLE_DECK,
        case_dir=tmp_path / "case",
        policy=CalculiXRunPolicy(timeout_seconds=3.0),
    )
    restored = CalculiXRunRequest.from_dict(request.to_dict())
    runner = runner_with_fake_ccx(tmp_path, "success")

    result = runner.run(restored)

    assert result.status is CalculiXRunStatus.COMPLETED
    assert result.run_result is not None
    assert result.run_result.command[0] == result.command[0]
    assert "shell" not in " ".join(result.command).lower()
