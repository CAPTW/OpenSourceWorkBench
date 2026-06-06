from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = REPO_ROOT / "docs" / "experimental" / "feaspec_ir_design.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_feaspec_ir_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_feaspec_ir_design_status_is_design_only() -> None:
    text = _read(DESIGN_DOC).lower()
    assert "design-only" in text
    assert "experimental" in text
    assert "not implemented" in text


def test_feaspec_ir_defines_candidate_and_approved_spec() -> None:
    text = _read(DESIGN_DOC)
    assert "FEASpecCandidate" in text
    assert "approved FEASpec" in text or "Approved FEASpec" in text
    assert "Only an approved FEASpec may proceed" in text


def test_feaspec_ir_requires_human_review_before_solver_handoff() -> None:
    text = _read(DESIGN_DOC).lower()
    assert "human review" in text
    assert "requires human review" in text or "require human review" in text
    assert "only an approved feaspec may proceed" in text
    assert "no automatic unreviewed solver execution" in text


def test_feaspec_ir_requires_explicit_units() -> None:
    text = _read(DESIGN_DOC).lower()
    assert "explicit units" in text
    assert "no silent unit inference" in text
    assert "unknown units must block approval" in text


def test_feaspec_ir_includes_geometry_bcs_loads_and_evidence() -> None:
    text = _read(DESIGN_DOC)
    assert "GeometryGraph" in text or "geometry_graph" in text
    assert "boundary_conditions" in text
    assert "loads" in text
    assert "evidence" in text
    assert "confidence" in text


def test_feaspec_ir_includes_diagnostics_validation_and_solver_path() -> None:
    text = _read(DESIGN_DOC).lower()
    assert "diagnostics" in text
    assert "validation states" in text
    assert "valid-with-warnings" in text
    assert "solver_compatibility" in text
    assert "calculix-first" in text


def test_feaspec_ir_records_vlm_and_commercial_solver_boundaries() -> None:
    text = _read(DESIGN_DOC).lower()
    assert "no vlm api" in text
    assert "credentials" in text
    assert "abaqus may appear only as optional" in text
    assert "abaqus must not be required" in text
    assert "no industrial certification" in text


def test_feaspec_ir_does_not_claim_implementation_exists() -> None:
    text = _read(DESIGN_DOC).lower()
    forbidden_positive_claims = (
        "feaspec implementation exists",
        "feaspec is implemented",
        "vfea implementation exists",
        "vfea is implemented",
        "automatic unreviewed solver execution is allowed",
        "abaqus is mandatory",
        "abaqus is required",
        "requires abaqus",
        "industrial certification is provided",
    )
    for claim in forbidden_positive_claims:
        assert claim not in text
