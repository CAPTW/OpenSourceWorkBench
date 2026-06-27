from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reactivation_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"


def _collapse(text: str) -> str:
    """Lowercase and collapse all whitespace so wrapped markdown still matches."""

    return re.sub(r"\s+", " ", text.lower())


def _doc() -> str:
    return _collapse(DOC.read_text(encoding="utf-8"))


def test_design_doc_exists() -> None:
    assert DOC.exists()


def test_design_doc_is_design_only_and_no_runtime_behavior() -> None:
    doc = _doc()
    assert "design-only" in doc
    assert "no runtime behavior" in doc


def test_design_doc_states_core_non_actions() -> None:
    doc = _doc()
    required = [
        "no reactivation implementation",
        "no reactivation persistence",
        "no gui reactivation",
        "no cli reactivation",
        "no automatic activation",
        "no file deletion",
        "no file rewrite",
        "no plugin package import",
        "no directory scan",
        "no network fetch",
        "no discovery execution",
        "no solver execution",
        "no release mutation",
        "no tag mutation",
        "no asset mutation",
        "no version bump",
        "no validation-pass claim",
        "no certification claim",
    ]
    for phrase in required:
        assert phrase in doc, phrase


def test_design_doc_states_trust_and_file_restoration_non_actions() -> None:
    doc = _doc()
    assert "no trust restoration" in doc or "not trust restoration" in doc
    assert "no file restoration" in doc or "not file restoration" in doc


def test_design_doc_states_dependency_non_actions() -> None:
    doc = _doc()
    assert "no dependency installation" in doc or "no dependency install" in doc
    assert "no dependency uninstall" in doc


def test_design_doc_states_validation_non_actions() -> None:
    doc = _doc()
    assert "no validation execution" in doc or "reactivation is not validation" in doc
    assert "no validation-fail claim" in doc or "no validation failure claim" in doc


def test_design_doc_states_issue_non_actions() -> None:
    doc = _doc()
    assert "no issue mutation" in doc or "no issue closure" in doc


def test_design_doc_defines_reactivation_and_non_meaning() -> None:
    doc = _doc()
    assert "definition of reactivation" in doc
    assert "what reactivation does not mean" in doc
    assert "reactivation must not mean" in doc


def test_design_doc_describes_acknowledgement_model() -> None:
    doc = _doc()
    assert "acknowledgement" in doc
    assert "reactivation_not_validation" in doc
    assert "reactivation_not_trust_restoration" in doc
    assert "reactivation_requires_activation_review" in doc
    assert "stale_source_requires_repreview" in doc


def test_design_doc_describes_source_trust_provenance_labels() -> None:
    doc = _doc()
    assert "source_type" in doc
    assert "trust_label" in doc
    assert "activation_state" in doc
    assert "a trust label is not certification" in doc
    assert "redacted by default" in doc


def test_design_doc_describes_state_machine_and_blocked_transitions() -> None:
    doc = _doc()
    assert "reactivation state machine" in doc
    assert "reactivation_requested" in doc
    assert "reactivation_blocked" in doc
    assert "reactivation_ready" in doc
    assert "future_activation_required" in doc
    assert "blocked transitions" in doc


def test_design_doc_describes_stale_source_and_repreview_policy() -> None:
    doc = _doc()
    assert "stale source" in doc
    assert "re-preview" in doc or "repreview" in doc
    assert "must not read files" in doc


def test_design_doc_describes_validation_and_evidence_policy() -> None:
    doc = _doc()
    assert "validation and evidence policy" in doc
    assert "deactivation history" in doc
    assert "skipped-missing remains skipped-missing" in doc
    assert "historical validation evidence" in doc


def test_design_doc_describes_relationship_to_live_optional_validation_issues() -> None:
    doc = _doc()
    assert "#6" in doc and "#11" in doc
    assert "reactivation is not live optional validation" in doc


def test_design_doc_reserves_ospmg_reactivation_diagnostics() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_REACTIVATION_DEACTIVATED_REQUIRED",
        "OSPMG_REACTIVATION_ACK_REQUIRED",
        "OSPMG_REACTIVATION_NOT_TRUST_RESTORE",
        "OSPMG_REACTIVATION_NOT_VALIDATION",
        "OSPMG_REACTIVATION_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_REACTIVATION_CONFLICT_BLOCKED",
        "OSPMG_REACTIVATION_SHARED_STACK_WARNING",
        "OSPMG_REACTIVATION_PERSISTENCE_NOT_IMPLEMENTED",
        "OSPMG_REACTIVATION_FUTURE_GATE",
    ):
        assert code in doc, code


def test_design_doc_lists_future_gates() -> None:
    doc = _doc()
    assert "future gates" in doc
    assert "reactivation_viewmodel_extension" in doc
    assert "reactivation_gui_implementation" in doc


def test_decision_log_has_reactivation_adr() -> None:
    text = DECISION_LOG.read_text(encoding="utf-8")
    assert "ADR-0121" in text
    assert "Reactivation" in text or "reactivation" in text


def test_meta_docs_reference_reactivation() -> None:
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        assert "reactivation" in path.read_text(encoding="utf-8").lower(), path.name
