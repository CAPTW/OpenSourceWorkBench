from __future__ import annotations

import importlib

from osw.cli import main as cli_main
from osw.cli import main as cli_package_main
from osw.experimental.optional_solvers import (
    OptionalSolverDiscoveryReport,
    OptionalSolverExecutableDiscovery,
    OptionalSolverHealthState,
    OptionalSolverStackDiscovery,
)

cli_module = importlib.import_module("osw.cli.main")


def _stack(stack_id: str, state: OptionalSolverHealthState) -> OptionalSolverStackDiscovery:
    return OptionalSolverStackDiscovery(
        stack_id=stack_id,
        display_name=stack_id.title(),
        related_issue=6,
        health_state=state,
        executables=(
            OptionalSolverExecutableDiscovery(
                identifier=f"{stack_id}-tool",
                found=state != OptionalSolverHealthState.MISSING,
                redacted_path=(
                    f"<redacted:{stack_id}-tool.exe>"
                    if state != OptionalSolverHealthState.MISSING
                    else ""
                ),
            ),
        ),
    )


def test_optional_solver_doctor_missing_stacks_exit_zero(capsys) -> None:
    exit_code = cli_package_main(["optional-solver-doctor", "--stack", "calculix"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "calculix" in output
    assert "Passive discovery only" in output
    assert "not validation-pass evidence" in output


def test_optional_solver_doctor_renders_missing_partial_discovered(
    monkeypatch,
    capsys,
) -> None:
    report = OptionalSolverDiscoveryReport(
        stacks=(
            _stack("missing", OptionalSolverHealthState.MISSING),
            _stack("partial", OptionalSolverHealthState.PARTIALLY_INSTALLED),
            _stack("discovered", OptionalSolverHealthState.DISCOVERED),
        )
    )
    monkeypatch.setattr(cli_module, "_optional_solver_doctor_report", lambda *_a, **_k: report)
    monkeypatch.setattr(cli_module, "_select_optional_solver_manifests", lambda _ids: ())

    exit_code = cli_main(["optional-solver-doctor", "--all"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "missing: missing" in output
    assert "partial: partially_installed" in output
    assert "discovered: discovered" in output


def test_optional_solver_doctor_unknown_stack_exits_nonzero(capsys) -> None:
    exit_code = cli_package_main(
        ["optional-solver-doctor", "--stack", "does_not_exist"]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "does_not_exist" in captured.err


def test_optional_solver_doctor_show_full_paths_is_explicit(
    monkeypatch,
    capsys,
) -> None:
    calls: list[bool] = []

    def fake_report(_manifests, *, show_full_paths: bool) -> OptionalSolverDiscoveryReport:
        calls.append(show_full_paths)
        return OptionalSolverDiscoveryReport(stacks=())

    monkeypatch.setattr(cli_module, "_optional_solver_doctor_report", fake_report)
    monkeypatch.setattr(cli_module, "_select_optional_solver_manifests", lambda _ids: ())

    assert cli_main(["optional-solver-doctor", "--all"]) == 0
    assert cli_main(["optional-solver-doctor", "--all", "--show-full-paths"]) == 0
    capsys.readouterr()
    assert calls == [False, True]
