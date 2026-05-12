from __future__ import annotations

from pathlib import Path

from osw.solvers.calculix.result_parser import parse_calculix_dat
from osw.solvers.calculix.validation import (
    CantileverValidationInput,
    validate_cantilever_tip_displacement,
)


def test_cantilever_expected_displacement_uses_euler_bernoulli_formula() -> None:
    validation = validate_cantilever_tip_displacement(
        observed_displacement=0.004,
        inputs=CantileverValidationInput(
            force=120.0,
            length=2.0,
            young_modulus=200_000_000_000.0,
            second_moment_area=4.0e-7,
            tolerance_ratio=0.05,
        ),
    )

    assert validation.expected_displacement == 0.004
    assert validation.relative_error == 0.0
    assert validation.passed is True
    assert validation.to_dict()["formula"] == "F L^3 / (3 E I)"


def test_cantilever_validation_flags_out_of_tolerance_result(tmp_path: Path) -> None:
    dat_path = tmp_path / "cantilever.dat"
    dat_path.write_text(
        "\n".join(
            [
                "DISPLACEMENTS",
                "NODE U1 U2 U3",
                "1 0 0 0",
                "2 0 -0.006 0",
            ]
        ),
        encoding="utf-8",
    )
    dataset = parse_calculix_dat(dat_path)

    validation = validate_cantilever_tip_displacement(
        observed_displacement=dataset.max_summary("displacement_magnitude").value,
        inputs=CantileverValidationInput(
            force=120.0,
            length=2.0,
            young_modulus=200_000_000_000.0,
            second_moment_area=4.0e-7,
            tolerance_ratio=0.05,
        ),
    )

    assert validation.passed is False
    assert validation.relative_error > validation.tolerance_ratio
    assert "outside tolerance" in validation.message
