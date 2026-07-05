from __future__ import annotations

from pathlib import Path

from osw.cli.main import main
from osw.solvers.openfoam.residual_parser import (
    parse_openfoam_log,
    parse_openfoam_residuals_from_text,
)
from osw.solvers.openfoam.results import openfoam_residuals_to_result_dataset

FIXTURES = Path(__file__).parents[1] / "fixtures" / "openfoam"


def test_parse_simple_openfoam_residual_log() -> None:
    summary = parse_openfoam_log(FIXTURES / "residual_simple.log")

    assert summary.iteration_count == 4
    assert summary.final_residuals["Ux"] == 0.01
    assert summary.final_residuals["Uy"] == 0.02
    assert summary.final_residuals["Uz"] == 0.03
    assert summary.final_residuals["p"] == 0.04
    assert summary.converged is True
    assert [series.field for series in summary.series] == ["Ux", "Uy", "Uz", "p"]


def test_partial_log_returns_partial_summary() -> None:
    summary = parse_openfoam_log(FIXTURES / "residual_partial.log")

    assert summary.iteration_count == 1
    assert summary.final_residuals["Ux"] == 0.02
    assert not summary.diagnostics.has_errors


def test_corrupt_log_gives_friendly_diagnostic() -> None:
    summary = parse_openfoam_log(FIXTURES / "residual_corrupt.log")

    assert summary.iteration_count == 0
    assert summary.diagnostics.has_warnings
    assert "No OpenFOAM residual lines" in summary.diagnostics.summary()


def test_missing_log_gives_friendly_diagnostic(tmp_path: Path) -> None:
    summary = parse_openfoam_log(tmp_path / "missing.log")

    assert summary.diagnostics.has_errors
    assert "does not exist" in summary.diagnostics.summary()


def test_empty_text_gives_warning() -> None:
    summary = parse_openfoam_residuals_from_text("")

    assert summary.diagnostics.has_warnings
    assert summary.iteration_count == 0


def test_continuity_reports_are_non_error_metrics() -> None:
    summary = parse_openfoam_residuals_from_text(_icofoam_log_with_continuity())

    assert summary.iteration_count == 3
    assert summary.final_residuals["Ux"] == 2.0e-8
    assert summary.final_residuals["Uy"] == 3.0e-8
    assert summary.final_residuals["p"] == 4.0e-7
    assert summary.converged is True
    assert not summary.diagnostics.has_errors
    assert not summary.diagnostics.errors()
    continuity_reports = summary.metadata["continuity_reports"]
    assert continuity_reports == [
        {
            "time": 1.0,
            "sum_local": 2.5e-12,
            "global": -1.0e-13,
            "cumulative": 4.0e-12,
        }
    ]
    assert any(
        message.code == "openfoam-continuity-reports-parsed"
        for message in summary.diagnostics.messages
    )


def test_openfoam_parse_log_cli_exits_zero_for_continuity_reports(
    tmp_path: Path,
    capsys,
) -> None:
    log_path = tmp_path / "log.icoFoam"
    log_path.write_text(_icofoam_log_with_continuity(), encoding="utf-8")

    code = main(["openfoam-parse-log", str(log_path)])

    captured = capsys.readouterr()
    assert code == 0
    assert "OpenFOAM residual summary" in captured.out
    assert "Iterations: 3" in captured.out
    assert "p: 4e-07" in captured.out
    assert "ERROR" not in captured.err


def test_real_fatal_marker_remains_error() -> None:
    summary = parse_openfoam_residuals_from_text(
        "\n".join(
            [
                "Time = 1",
                (
                    "smoothSolver:  Solving for Ux, Initial residual = 1, "
                    "Final residual = 0.1, No Iterations 2"
                ),
                "FOAM FATAL ERROR: synthetic dictionary failure",
            ]
        )
    )

    assert summary.iteration_count == 1
    assert summary.diagnostics.has_errors
    assert any(
        message.code == "openfoam-fatal-detected"
        for message in summary.diagnostics.errors()
    )


def test_floating_point_exception_crash_remains_error() -> None:
    summary = parse_openfoam_residuals_from_text("Floating point exception (core dumped)")

    assert summary.diagnostics.has_errors
    assert any(
        message.code == "openfoam-fatal-detected"
        for message in summary.diagnostics.errors()
    )


def test_openfoam_parse_log_cli_exits_nonzero_for_fatal_marker(
    tmp_path: Path,
    capsys,
) -> None:
    log_path = tmp_path / "log.icoFoam"
    log_path.write_text(
        "\n".join(
            [
                "Time = 1",
                (
                    "smoothSolver:  Solving for p, Initial residual = 1, "
                    "Final residual = 0.1, No Iterations 2"
                ),
                "FOAM FATAL ERROR: synthetic dictionary failure",
            ]
        ),
        encoding="utf-8",
    )

    code = main(["openfoam-parse-log", str(log_path)])

    captured = capsys.readouterr()
    assert code == 1
    assert "OpenFOAM residual summary" in captured.out
    assert "ERROR openfoam-fatal-detected" in captured.err


def test_residual_summary_bridges_to_result_dataset() -> None:
    summary = parse_openfoam_log(FIXTURES / "residual_simple.log")

    dataset = openfoam_residuals_to_result_dataset(summary, solver="icoFoam")

    assert dataset.source == "openfoam"
    assert dataset.solver == "icoFoam"
    assert dataset.field("residuals").components == ("Ux", "Uy", "Uz", "p")
    assert dataset.max_summary("final_residual_p").value == 0.04
    assert dataset.to_report_tables()


def _icofoam_log_with_continuity() -> str:
    return "\n".join(
        [
            "sigFpe : Enabling floating point exception trapping (FOAM_SIGFPE).",
            "Time = 1",
            (
                "smoothSolver:  Solving for Ux, Initial residual = 1, "
                "Final residual = 2e-08, No Iterations 2"
            ),
            (
                "smoothSolver:  Solving for Uy, Initial residual = 1, "
                "Final residual = 3e-08, No Iterations 2"
            ),
            (
                "GAMG:  Solving for p, Initial residual = 1, "
                "Final residual = 4e-07, No Iterations 3"
            ),
            (
                "time step continuity errors : sum local = 2.5e-12, "
                "global = -1e-13, cumulative = 4e-12"
            ),
            "End",
        ]
    )
