from __future__ import annotations

import importlib
from pathlib import Path

from osw.solvers.calculix.dat_parser import (
    extract_displacement_summary_from_dat,
    extract_stress_summary_from_dat,
    parse_calculix_dat,
)
from osw.solvers.calculix.results import CalculiXResultStatus

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "calculix" / "results"


def test_module_imports_without_ccx_or_pyside6() -> None:
    module = importlib.import_module("osw.solvers.calculix.dat_parser")

    assert hasattr(module, "parse_calculix_dat")


def test_parse_simple_success_dat_max_displacement() -> None:
    parsed = parse_calculix_dat(FIXTURE_DIR / "simple_success.dat")

    assert parsed.status is CalculiXResultStatus.PARSED
    assert parsed.displacement_summary is not None
    assert parsed.displacement_summary.max_magnitude == 1.904761905e-01
    assert parsed.displacement_summary.max_node_id == 42


def test_parse_simple_success_dat_max_von_mises_stress() -> None:
    parsed = parse_calculix_dat(FIXTURE_DIR / "simple_success.dat")

    assert parsed.stress_summary is not None
    assert parsed.stress_summary.max_von_mises == 2.345e08
    assert parsed.stress_summary.max_element_id == 7


def test_warning_lines_produce_diagnostics_and_log_events() -> None:
    parsed = parse_calculix_dat(FIXTURE_DIR / "simple_warning.dat")

    assert parsed.log_events
    assert parsed.diagnostics.has_warnings
    assert "convergence warning" in parsed.diagnostics.summary()


def test_corrupt_partial_dat_returns_partial_warning() -> None:
    parsed = parse_calculix_dat(FIXTURE_DIR / "corrupt_partial.dat")

    assert parsed.status is CalculiXResultStatus.PARTIAL
    assert parsed.diagnostics.has_warnings
    assert "Could not parse displacement row" in parsed.diagnostics.summary()
    assert "max displacement summary" in parsed.diagnostics.summary()


def test_empty_dat_returns_friendly_diagnostic() -> None:
    parsed = parse_calculix_dat(FIXTURE_DIR / "empty.dat")

    assert parsed.status is CalculiXResultStatus.PARTIAL
    assert parsed.diagnostics.has_warnings
    assert "empty" in parsed.diagnostics.summary().lower()


def test_missing_dat_returns_friendly_diagnostic(tmp_path: Path) -> None:
    parsed = parse_calculix_dat(tmp_path / "missing.dat")

    assert parsed.status is CalculiXResultStatus.MISSING_ARTIFACTS
    assert parsed.diagnostics.has_errors
    assert "was not found" in parsed.diagnostics.summary()


def test_summary_extractors_parse_explicit_lines() -> None:
    text = (
        "MAX DISPLACEMENT MAGNITUDE: 3.0e-3 NODE: 9\n"
        "MAX VON MISES STRESS: 4.0e7 ELEMENT: 11\n"
    )

    assert extract_displacement_summary_from_dat(text).max_node_id == 9  # type: ignore[union-attr]
    assert extract_stress_summary_from_dat(text).max_element_id == 11  # type: ignore[union-attr]
