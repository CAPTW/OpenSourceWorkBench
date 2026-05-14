from __future__ import annotations

from pathlib import Path

REQUIRED_CASES = {
    "VAL-CAE-001": "delta = F L^3 / (3 E I)",
    "VAL-MESH-001": "Exact structural checks",
    "VAL-MSCRIPT-001": "preview/import does not execute automatically",
    "VAL-CHM-001": "990.0 < D < 1000.0 kg/m^3",
    "VAL-REPORT-001": "Exact section-name presence",
}

REQUIRED_COLUMNS = (
    "Case ID",
    "Domain",
    "Solver",
    "Input",
    "Expected result",
    "Tolerance / pass criterion",
    "Source / formula",
    "Status",
    "Last run",
)


def test_validation_matrix_contains_required_v0_1_cases() -> None:
    text = Path("docs/04_validation_matrix.md").read_text(encoding="utf-8")

    for case_id, pass_criterion in REQUIRED_CASES.items():
        assert case_id in text
        assert pass_criterion in text


def test_validation_matrix_contains_required_fields_and_limitations() -> None:
    text = Path("docs/04_validation_matrix.md").read_text(encoding="utf-8")

    for column in REQUIRED_COLUMNS:
        assert column in text
    assert 'fluid="Water"' in text
    assert "`pressure_pa=101325.0`" in text
    assert "`temperature_k=300.0`" in text
    assert "`996.6 kg/m^3`" in text
    assert "not certify" in text
    assert "Native commercial CAD direct import is not supported" in text
    assert "preview-first" in text
