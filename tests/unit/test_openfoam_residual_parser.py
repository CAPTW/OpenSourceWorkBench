from __future__ import annotations

from pathlib import Path

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


def test_residual_summary_bridges_to_result_dataset() -> None:
    summary = parse_openfoam_log(FIXTURES / "residual_simple.log")

    dataset = openfoam_residuals_to_result_dataset(summary, solver="icoFoam")

    assert dataset.source == "openfoam"
    assert dataset.solver == "icoFoam"
    assert dataset.field("residuals").components == ("Ux", "Uy", "Uz", "p")
    assert dataset.max_summary("final_residual_p").value == 0.04
    assert dataset.to_report_tables()
