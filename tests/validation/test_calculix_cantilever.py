from __future__ import annotations

from pathlib import Path

from osw.solvers.calculix.result_parser import parse_calculix_results
from osw.solvers.calculix.results import CalculiXParsedResults
from osw.solvers.calculix.validation import (
    CantileverValidationInput,
    expected_cantilever_tip_displacement,
    validate_cantilever_displacement,
    validate_cantilever_tip_displacement,
)

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "calculix" / "results"


def test_expected_cantilever_tip_displacement_formula() -> None:
    expected = expected_cantilever_tip_displacement(
        force=120.0,
        length=2.0,
        elastic_modulus=200_000_000_000.0,
        second_moment_area=4.0e-7,
    )

    assert expected == 0.004


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
    assert validation.expected_max_displacement == 0.004
    assert validation.relative_error == 0.0
    assert validation.passed is True
    assert validation.to_dict()["formula"] == "F L^3 / (3 E I)"


def test_validate_cantilever_displacement_passes_within_tolerance() -> None:
    parsed = parse_calculix_results(dat_path=FIXTURE_DIR / "simple_success.dat")

    validation = validate_cantilever_displacement(
        parsed,
        CantileverValidationInput(
            force=100.0,
            length=1.0,
            elastic_modulus=210_000_000_000.0,
            second_moment_area=8.333333333e-10,
            tolerance_fraction=0.05,
        ),
    )

    assert validation.passed is True
    assert validation.relative_error < validation.tolerance_fraction


def test_validate_cantilever_displacement_fails_outside_tolerance() -> None:
    parsed = parse_calculix_results(dat_path=FIXTURE_DIR / "simple_success.dat")

    validation = validate_cantilever_displacement(
        parsed,
        CantileverValidationInput(
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


def test_missing_observed_displacement_gives_diagnostic() -> None:
    validation = validate_cantilever_displacement(
        CalculiXParsedResults(),
        CantileverValidationInput(
            force=100.0,
            length=1.0,
            elastic_modulus=210_000_000_000.0,
            second_moment_area=8.333333333e-10,
        ),
    )

    assert validation.passed is False
    assert validation.observed_displacement is None
    assert validation.diagnostics


def test_validation_matrix_documents_cantilever_case() -> None:
    matrix = Path("docs/04_validation_matrix.md").read_text(encoding="utf-8")

    assert "VAL-CAE-001" in matrix
    assert "F L^3 / (3 E I)" in matrix
