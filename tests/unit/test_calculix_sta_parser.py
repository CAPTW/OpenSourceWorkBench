from __future__ import annotations

from pathlib import Path

from osw.solvers.calculix.sta_parser import parse_calculix_sta, parse_sta_text

FIXTURE_DIR = Path(__file__).parents[1] / "fixtures" / "calculix" / "results"


def test_parse_simple_success_sta() -> None:
    summary = parse_calculix_sta(FIXTURE_DIR / "simple_success.sta")

    assert summary.completed is True
    assert summary.increments == 2
    assert summary.last_step == 1
    assert summary.last_increment == 2


def test_warning_error_detection_works() -> None:
    summary = parse_sta_text("STEP 1 INC 1\nWARNING: small pivot\nERROR: failed\n")

    assert summary.completed is False
    assert summary.warnings == ("WARNING: small pivot",)
    assert summary.errors == ("ERROR: failed",)


def test_empty_sta_is_handled_gracefully() -> None:
    summary = parse_sta_text("")

    assert summary.completed is None
    assert summary.warnings
    assert "empty" in summary.warnings[0].lower()


def test_missing_sta_is_handled_gracefully(tmp_path: Path) -> None:
    summary = parse_calculix_sta(tmp_path / "missing.sta")

    assert summary.completed is None
    assert summary.errors
    assert "was not found" in summary.errors[0]
