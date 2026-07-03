from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_prepared_machine_manifest_state_validation_prerequisites.md"
)


def _collapsed(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8")).lower()


def _doc() -> str:
    return _collapsed(DOC_PATH)


def test_prepared_machine_prerequisites_doc_exists_and_records_parked_gate() -> None:
    assert DOC_PATH.exists()
    text = _doc()
    assert "prepared-machine validation is currently parked" in text
    assert "osw-valid-optional_prepared_machine_manifest_state_validation" in text
    assert "42d687626955a516f4072ad07b058e0f665fceaf" in text
    assert "no current safe runnable prepared-machine manifest-state validation command" in text


def test_missing_prerequisites_are_named() -> None:
    text = _doc()
    assert "`gmsh` executable" in text
    assert "python `gmsh`" in text
    assert "`octave`" in text
    assert "`ccx`" in text
    assert "openfoam commands" in text
    assert "python `meshio`" in text
    assert "python `pyvista`" in text
    assert "python `vtk`" in text
    assert "python `coolprop`" in text
    assert "python `cantera`" in text


def test_non_actions_and_claim_boundaries_are_explicit() -> None:
    text = _doc()
    for phrase in (
        "no dependency installation",
        "no solver installation",
        "no solver execution",
        "no projectschema mutation",
        "no issue mutation",
        "no release mutation",
        "no tag mutation",
        "no asset mutation",
        "no version bump",
        "no certification claim",
        "no validation-pass claim",
        "no validation-fail claim",
        "issues `#6` through `#11` remain open",
    ):
        assert phrase in text


def test_doc_defines_required_prerequisite_sections() -> None:
    text = _doc()
    for phrase in (
        "non-mutating preflight checklist",
        "future prepared-machine validation command requirements",
        "evidence policy",
        "retry criteria",
        "future gates",
    ):
        assert phrase in text


def test_meta_docs_reference_prerequisite_boundary() -> None:
    decision_log = _collapsed(REPO_ROOT / "docs" / "07_decision_log.md")
    guardrails = _collapsed(REPO_ROOT / "docs" / "08_scope_guardrails.md")
    risk = _collapsed(REPO_ROOT / "docs" / "09_risk_register.md")
    checklist = _collapsed(REPO_ROOT / "docs" / "10_release_checklist.md")
    matrix = _collapsed(REPO_ROOT / "docs" / "04_validation_matrix.md")

    assert "adr-0173" in decision_log
    assert (
        "prepared-machine optional solver validation requires explicit local prerequisites"
        in decision_log
    )
    assert "prepared-machine prerequisite documentation" in guardrails
    assert "overclaimed from focused regression tests or docs-only evidence" in risk
    assert "prepared-machine manifest-state validation prerequisites" in checklist
    assert "prepared-machine manifest-state validation prerequisites" in matrix
