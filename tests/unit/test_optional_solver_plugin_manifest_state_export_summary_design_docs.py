from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_state_export_summary_design.md"
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
        "no export implementation",
        "no file writes",
        "no export file creation",
        "no reloadable bundle creation",
        "no clipboard behavior",
        "no open-output-folder behavior",
        "no persistence implementation",
        "no settings file creation",
        "no project schema mutation",
        "no gui export behavior",
        "no cli export behavior",
        "no automatic activation",
        "no trust restoration",
        "no file rewrite",
        "no file deletion",
        "no dependency uninstall",
        "no plugin package import",
        "no directory scan",
        "no network fetch",
        "no discovery execution",
        "no validation execution",
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


def test_design_doc_states_file_restore_and_dependency_non_actions() -> None:
    doc = _doc()
    assert "no file restoration" in doc or "no file restore" in doc
    assert "no dependency installation" in doc or "no dependency install" in doc


def test_design_doc_states_validation_and_issue_non_actions() -> None:
    doc = _doc()
    assert "no validation-fail claim" in doc or "no validation failure claim" in doc
    assert "no issue mutation" in doc or "no issue closure" in doc


def test_design_doc_defines_export_summary_and_forbidden_content() -> None:
    doc = _doc()
    assert "definition of export summary" in doc
    assert "what export summary must not include" in doc
    assert "must not include" in doc


def test_design_doc_distinguishes_export_from_persistence_and_bundle() -> None:
    doc = _doc()
    assert "export summary vs persistence vs reloadable bundle" in doc
    assert "export summary is not persistence" in doc
    assert "reloadable bundle" in doc


def test_design_doc_describes_export_preconditions() -> None:
    doc = _doc()
    assert "export preconditions" in doc
    assert "explicit user action" in doc
    assert "visible redaction preview" in doc


def test_design_doc_describes_acknowledgement_model() -> None:
    doc = _doc()
    assert "acknowledgement" in doc
    assert "export_not_validation" in doc
    assert "export_not_persistence" in doc
    assert "export_not_reloadable_bundle" in doc
    assert "redaction_reviewed" in doc


def test_design_doc_describes_redaction_and_privacy_policy() -> None:
    doc = _doc()
    assert "redaction and privacy policy" in doc
    assert "absolute paths are not shown by default" in doc
    assert "secrets" in doc


def test_design_doc_describes_summary_content_model() -> None:
    doc = _doc()
    assert "summary content model" in doc
    assert "redaction report" in doc
    assert "non-action" in doc


def test_design_doc_describes_source_trust_provenance_labels() -> None:
    doc = _doc()
    assert "source_type" in doc
    assert "trust_label" in doc
    assert "export_summary_kind" in doc
    assert "a trust label is not certification" in doc
    assert "redacted by default" in doc


def test_design_doc_describes_state_coverage_model() -> None:
    doc = _doc()
    assert "state coverage model" in doc
    assert "future_activation_required" in doc
    assert "blocked interpretations" in doc


def test_design_doc_describes_stale_source_and_repreview_policy() -> None:
    doc = _doc()
    assert "stale-source and re-preview policy" in doc
    assert "re-preview" in doc or "repreview" in doc
    assert "does no file io" in doc


def test_design_doc_describes_validation_and_evidence_policy() -> None:
    doc = _doc()
    assert "validation and evidence policy" in doc
    assert "skipped-missing remains skipped-missing" in doc
    assert "historical evidence" in doc


def test_design_doc_describes_relationship_to_persistence_design() -> None:
    doc = _doc()
    assert "relationship to state persistence design" in doc
    assert "osw-exp-090" in doc


def test_design_doc_describes_relationship_to_projectschema() -> None:
    doc = _doc()
    assert "relationship to projectschema" in doc
    assert "no projectschema mutation" in doc


def test_design_doc_describes_relationship_to_live_optional_validation_issues() -> None:
    doc = _doc()
    assert "#6" in doc and "#11" in doc
    assert "an export summary is not live optional validation" in doc


def test_design_doc_reserves_ospmg_export_summary_diagnostics() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED",
        "OSPMG_EXPORT_SUMMARY_ACK_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE",
        "OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE",
        "OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED",
        "OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED",
        "OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM",
        "OSPMG_EXPORT_SUMMARY_FUTURE_GATE",
    ):
        assert code in doc, code


def test_design_doc_lists_future_gates() -> None:
    doc = _doc()
    assert "future gates" in doc
    assert "persistence_viewmodel" in doc
    assert "export_summary_viewmodel" in doc


def test_decision_log_has_export_summary_adr() -> None:
    text = DECISION_LOG.read_text(encoding="utf-8")
    assert "ADR-0125" in text
    assert "Export Summary" in text or "export summary" in text.lower()


def test_meta_docs_reference_export_summary() -> None:
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        assert "export-summary" in path.read_text(encoding="utf-8").lower() or (
            "export summary" in path.read_text(encoding="utf-8").lower()
        ), path.name
