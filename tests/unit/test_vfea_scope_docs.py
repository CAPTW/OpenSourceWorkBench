from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCOPE_DOC = REPO_ROOT / "docs" / "roadmap" / "vfea_experimental_scope.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_vfea_scope_doc_exists() -> None:
    assert SCOPE_DOC.exists()


def test_vfea_scope_status_is_planning_only() -> None:
    text = _read(SCOPE_DOC).lower()
    assert "planning-only" in text
    assert "experimental" in text
    assert "not implemented" in text


def test_vfea_scope_requires_human_review_before_solver_handoff() -> None:
    text = _read(SCOPE_DOC).lower()
    assert "no automatic unreviewed solver execution from image or vlm output" in text
    assert "human review" in text
    assert "users must approve" in text


def test_vfea_scope_defines_feaspec_candidate_and_validation() -> None:
    text = _read(SCOPE_DOC)
    assert "FEASpecCandidate" in text
    assert "FEASpecValidator" in text
    assert "FEASpec intermediate representation" in text


def test_vfea_scope_records_solver_boundaries() -> None:
    text = _read(SCOPE_DOC).lower()
    assert "calculix-first" in text
    assert "abaqus may be discussed only as optional" in text
    assert "must not require abaqus" in text


def test_vfea_scope_records_validation_and_benchmark_requirements() -> None:
    text = _read(SCOPE_DOC).lower()
    assert "schema validity" in text
    assert "graph connectivity" in text
    assert "node precision and recall" in text
    assert "connectivity f1" in text
    assert "boundary-condition detection accuracy" in text


def test_vfea_scope_records_non_goals() -> None:
    text = _read(SCOPE_DOC).lower()
    assert "topology optimization is a separate future plugin concept" in text
    assert "topology optimization implementation" in text
    assert "industrial certification, compliance, or production accuracy claims" in text
    assert "native commercial cad import" in text


def test_vfea_scope_does_not_claim_forbidden_capabilities() -> None:
    text = _read(SCOPE_DOC).lower()
    forbidden_positive_claims = (
        "vfea is implemented",
        "vfea implementation is complete",
        "automatic solver execution is allowed",
        "automatic unreviewed solver execution is allowed",
        "abaqus is required",
        "abaqus is mandatory",
        "requires abaqus",
        "industrial certification is provided",
        "native commercial cad import is supported",
    )
    for claim in forbidden_positive_claims:
        assert claim not in text
