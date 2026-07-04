from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / "openfoam_template_v12_pfinal_fix_design.md"
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _doc() -> str:
    return _collapse(DOC.read_text(encoding="utf-8"))


def test_design_doc_exists() -> None:
    assert DOC.exists()


def test_design_only_and_non_actions() -> None:
    doc = _doc()
    for phrase in (
        "design-only",
        "no source edits",
        "no template edits",
        "no golden fixture edits",
        "no solver execution",
        "no issue mutation",
        "no projectschema mutation",
        "no certification claim",
    ):
        assert phrase in doc, phrase


def test_mentions_issues() -> None:
    doc = _doc()
    assert "#19" in doc
    assert "#18" in doc


def test_mentions_finding_anchors() -> None:
    doc = _doc()
    for phrase in ("pfinal", "fvsolution", "icofoam", "piso", "simple", "simplefoam"):
        assert phrase in doc, phrase


def test_defines_required_policies() -> None:
    doc = _doc()
    for phrase in (
        "affected algorithms and cases",
        "supported variant/version policy",
        "fvsolution layout policy",
        "version/algorithm selection policy",
        "backward compatibility",
        "golden fixture strategy",
        "test strategy",
        "validation strategy",
    ):
        assert phrase in doc, phrase


def test_reserves_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSW_OPENFOAM_FVSOLUTION_PFINAL_REQUIRED",
        "OSW_OPENFOAM_FVSOLUTION_PFINAL_MISSING",
        "OSW_OPENFOAM_FVSOLUTION_PFINAL_ADDED",
        "OSW_OPENFOAM_FVSOLUTION_PISO_FINAL_PRESSURE",
        "OSW_OPENFOAM_FVSOLUTION_SIMPLE_NO_PFINAL",
        "OSW_OPENFOAM_FVSOLUTION_VARIANT_UNSUPPORTED",
        "OSW_OPENFOAM_FVSOLUTION_GENERATION_BLOCKED",
    ):
        assert code in text, code


def test_distinguishes_piso_from_simple() -> None:
    doc = _doc()
    # PISO/icoFoam is affected; SIMPLE/simpleFoam is not affected by pFinal.
    assert "not affected" in doc
    assert "reltol 0" in doc  # final solve tightens relTol to 0


def test_references_future_implementation_gate() -> None:
    doc = _doc()
    assert "osw-exp-144_openfoam_template_v12_pfinal_fix_implementation" in doc


def test_meta_docs_reference_openfoam_pfinal_fix() -> None:
    assert "ADR-0178" in DECISION_LOG.read_text(encoding="utf-8")
    assert "pfinal" in GUARDRAILS.read_text(encoding="utf-8").lower()
    assert "pfinal" in RISK_REGISTER.read_text(encoding="utf-8").lower()
    assert "pfinal" in VALIDATION_MATRIX.read_text(encoding="utf-8").lower()
    assert "pfinal" in RELEASE_CHECKLIST.read_text(encoding="utf-8").lower()
    assert "pfinal" in CHANGELOG.read_text(encoding="utf-8").lower()
