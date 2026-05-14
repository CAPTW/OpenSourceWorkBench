from __future__ import annotations

from osw.solvers.su2.residuals import Su2ResidualParser


def test_su2_history_csv_residuals_parse_to_series() -> None:
    text = "\n".join(
        [
            '"Iter","rms[Rho]","rms[RhoE]","CL"',
            "1,-2.0,-2.5,0.1",
            "2,-3.0,-3.2,0.12",
        ]
    )

    series = Su2ResidualParser().parse_text(text)

    assert series.fields == ("rms[Rho]", "rms[RhoE]", "CL")
    assert len(series.points) == 2
    assert series.points[0].iteration == 1
    assert series.points[1].values["rms[Rho]"] == -3.0
    assert series.to_dict()["points"][1]["CL"] == 0.12


def test_su2_pipe_log_residuals_parse_to_series() -> None:
    text = "\n".join(
        [
            "| Iter | rms[Rho] | rms[RhoE] |",
            "| 1 | -2.0 | -2.5 |",
            "| 2 | -3.0 | -3.2 |",
        ]
    )

    series = Su2ResidualParser().parse_text(text)

    assert series.fields == ("rms[Rho]", "rms[RhoE]")
    assert series.points[-1].iteration == 2
    assert series.points[-1].values["rms[RhoE]"] == -3.2


def test_su2_residual_parser_reports_unreadable_input() -> None:
    series = Su2ResidualParser().parse_text("no residual rows here")

    assert series.points == ()
    assert any("No SU2 residual history rows were found" in warning for warning in series.warnings)
