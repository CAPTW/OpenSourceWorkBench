from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_state_persistence_design.md"
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
        "no persistence implementation",
        "no file writes",
        "no settings file creation",
        "no project schema mutation",
        "no gui persistence behavior",
        "no cli persistence behavior",
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


def test_design_doc_defines_persisted_state_and_forbidden_content() -> None:
    doc = _doc()
    assert "definition of persisted manifest state" in doc
    assert "what persisted state must not include" in doc
    assert "must not include" in doc


def test_design_doc_describes_storage_location_options() -> None:
    doc = _doc()
    assert "storage location options" in doc
    assert "project-local" in doc
    assert "user profile" in doc or "user-profile" in doc
    assert "session-only" in doc


def test_design_doc_describes_acknowledgement_persistence_and_invalidation() -> None:
    doc = _doc()
    assert "acknowledgement persistence and invalidation" in doc
    assert "persistence_not_validation" in doc
    assert "local_path_redaction_reviewed" in doc
    assert "persisted_acknowledgements_may_expire" in doc
    assert "expire" in doc


def test_design_doc_describes_source_trust_provenance_labels() -> None:
    doc = _doc()
    assert "source_type" in doc
    assert "trust_label" in doc
    assert "persisted_state_kind" in doc
    assert "a trust label is not certification" in doc
    assert "redacted by default" in doc


def test_design_doc_describes_redaction_and_privacy_policy() -> None:
    doc = _doc()
    assert "redaction and privacy policy" in doc
    assert "absolute paths are not shown by default" in doc
    assert "secrets" in doc


def test_design_doc_describes_state_schema_model() -> None:
    doc = _doc()
    assert "state schema model" in doc
    assert "schema_version" in doc
    assert "migration_notes" in doc


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


def test_design_doc_describes_relationship_to_projectschema() -> None:
    doc = _doc()
    assert "relationship to projectschema" in doc
    assert "no projectschema mutation" in doc


def test_design_doc_describes_relationship_to_live_optional_validation_issues() -> None:
    doc = _doc()
    assert "#6" in doc and "#11" in doc
    assert "persisted state is not live optional validation" in doc


def test_design_doc_reserves_ospmg_persistence_diagnostics() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_PERSISTENCE_NOT_IMPLEMENTED",
        "OSPMG_PERSISTENCE_ACK_REQUIRED",
        "OSPMG_PERSISTENCE_REDACTION_REQUIRED",
        "OSPMG_PERSISTENCE_UNREDACTED_PATH_BLOCKED",
        "OSPMG_PERSISTENCE_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_PERSISTENCE_SCHEMA_VERSION_REQUIRED",
        "OSPMG_PERSISTENCE_SCHEMA_MIGRATION_REQUIRED",
        "OSPMG_PERSISTENCE_CONFLICT_BLOCKED",
        "OSPMG_PERSISTENCE_UNSAFE_CLAIM",
        "OSPMG_PERSISTENCE_FUTURE_GATE",
    ):
        assert code in doc, code


def test_design_doc_lists_future_gates() -> None:
    doc = _doc()
    assert "future gates" in doc
    assert "state_export_summary_design" in doc
    assert "persistence_viewmodel" in doc
    assert "persistence_schema_model" in doc


def test_decision_log_has_persistence_adr() -> None:
    text = DECISION_LOG.read_text(encoding="utf-8")
    assert "ADR-0124" in text
    assert "Persistence" in text or "persistence" in text


def test_meta_docs_reference_state_persistence() -> None:
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        assert "persistence" in path.read_text(encoding="utf-8").lower(), path.name
