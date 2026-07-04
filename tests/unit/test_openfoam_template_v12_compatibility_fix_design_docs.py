from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / "openfoam_template_v12_compatibility_fix_design.md"
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


def test_mentions_finding_anchors() -> None:
    doc = _doc()
    for phrase in (
        "#18",
        "openfoam-write-case",
        "case_generator.py",
        "transportproperties",
        "physicalproperties",
    ):
        assert phrase in doc, phrase


def test_mentions_variants_and_versions() -> None:
    doc = _doc()
    assert "foundation v11/v12" in doc
    assert "foundation <= 10" in doc
    assert "esi" in doc


def test_defines_required_policies() -> None:
    doc = _doc()
    for phrase in (
        "supported variant/version policy",
        "template layout policy",
        "version/variant selection policy",
        "backward compatibility",
        "golden fixture strategy",
        "test strategy",
        "validation strategy",
    ):
        assert phrase in doc, phrase


def test_backward_compat_and_no_blanket_rename() -> None:
    doc = _doc()
    assert "blanket rename" in doc
    assert "do not remove" in doc  # no removing transportProperties without a deprecation gate


def test_reserves_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSW_OPENFOAM_TEMPLATE_VARIANT_UNSPECIFIED",
        "OSW_OPENFOAM_TEMPLATE_VARIANT_UNSUPPORTED",
        "OSW_OPENFOAM_TEMPLATE_FOUNDATION_V12_PHYSICAL_PROPERTIES",
        "OSW_OPENFOAM_TEMPLATE_LEGACY_TRANSPORT_PROPERTIES",
        "OSW_OPENFOAM_TEMPLATE_VARIANT_DETECTION_UNAVAILABLE",
        "OSW_OPENFOAM_TEMPLATE_COMPATIBILITY_WARNING",
        "OSW_OPENFOAM_TEMPLATE_GENERATION_BLOCKED",
    ):
        assert code in text, code


def test_references_future_gates() -> None:
    doc = _doc()
    assert "osw-exp-142_openfoam_template_v12_compatibility_fix_implementation" in doc
    assert "osw-valid-openfoam_template_v12_compatibility_live_validation" in doc


def test_meta_docs_reference_openfoam_template_fix_design() -> None:
    assert "ADR-0176" in DECISION_LOG.read_text(encoding="utf-8")
    assert "openfoam template" in GUARDRAILS.read_text(encoding="utf-8").lower()
    assert "openfoam template" in RISK_REGISTER.read_text(encoding="utf-8").lower()
    assert "openfoam" in VALIDATION_MATRIX.read_text(encoding="utf-8").lower()
    assert "openfoam template" in RELEASE_CHECKLIST.read_text(encoding="utf-8").lower()
    assert "openfoam template" in CHANGELOG.read_text(encoding="utf-8").lower()
