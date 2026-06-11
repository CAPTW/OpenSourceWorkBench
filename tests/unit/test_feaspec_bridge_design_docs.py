from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_to_projectschema_bridge_design.md"

REQUIRED_BRIDGE_CODES = {
    "FB_APPROVAL_REQUIRED",
    "FB_VALIDATION_BLOCKED",
    "FB_UNSUPPORTED_GEOMETRY",
    "FB_UNMAPPED_REGION",
    "FB_MISSING_MATERIAL",
    "FB_UNSUPPORTED_SECTION",
    "FB_INVALID_BC_TARGET",
    "FB_INVALID_LOAD_TARGET",
    "FB_UNSUPPORTED_LOAD_TYPE",
    "FB_UNITS_UNSUPPORTED",
    "FB_SOLVER_TARGET_UNSUPPORTED",
    "FB_PROVENANCE_INCOMPLETE",
}


def _read() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def test_feaspec_bridge_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_bridge_design_status_and_non_execution_boundaries() -> None:
    text = _read().lower()
    assert "design-only" in text
    assert "bridge not implemented" in text
    assert "no source bridge implementation" in text
    assert "no solver execution" in text
    assert "no vlm api" in text
    assert "credentials" in text


def test_bridge_design_defines_preconditions() -> None:
    text = _read().lower()
    assert "bridge preconditions" in text
    assert "approved feaspec" in text
    assert "validator report" in text
    assert "no blockers" in text
    assert "human_review" in text
    assert "explicit units" in text


def test_bridge_design_defines_mapping_and_strategies() -> None:
    text = _read().lower()
    assert "field mapping table" in text
    assert "geometry strategy" in text
    assert "material and section strategy" in text
    assert "boundary and load strategy" in text
    assert "units strategy" in text
    assert "provenance strategy" in text
    assert "source" in text
    assert "provenance" in text
    assert "evidence" in text
    assert "confidence" in text
    assert "geometry graph" in text
    assert "no meshing in bridge" in text
    assert "unmapped fields" in text


def test_bridge_design_includes_required_diagnostic_codes() -> None:
    text = _read()
    assert "Bridge diagnostic codes" in text
    for code in REQUIRED_BRIDGE_CODES:
        assert code in text


def test_bridge_design_defines_future_api_and_schema_boundaries() -> None:
    text = _read().lower()
    assert "future api sketch" in text
    assert "bridgeresult" in text
    assert "projectschema mutation is future work" in text
    assert "extension needs" in text
    assert "solveradapter/export is future work" in text
    assert "calculix-first" in text
    assert "abaqus is optional/non-default" in text
    assert "abaqus" in text


def test_bridge_design_does_not_claim_forbidden_implementation() -> None:
    text = _read().lower()
    forbidden_positive_claims = (
        "bridge is implemented",
        "projectschema bridge is implemented",
        "projectschema mutation is implemented",
        "solveradapter is implemented",
        "calculix export is implemented",
        "abaqus exporter is implemented",
        "automatic unreviewed solver execution is allowed",
        "abaqus is mandatory",
        "requires abaqus",
        "industrial certification is provided",
        "native commercial cad import is supported",
        "vfea is implemented",
    )
    for claim in forbidden_positive_claims:
        assert claim not in text
