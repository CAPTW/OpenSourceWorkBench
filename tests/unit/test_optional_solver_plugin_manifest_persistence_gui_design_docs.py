from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_persistence_gui_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"


def _collapse(text: str) -> str:
    """Lowercase and collapse whitespace so wrapped markdown still matches."""

    return re.sub(r"\s+", " ", text.lower())


def _doc() -> str:
    return _collapse(DOC.read_text(encoding="utf-8"))


def test_design_doc_exists() -> None:
    assert DOC.exists()


def test_design_doc_is_design_only_and_non_runtime() -> None:
    doc = _doc()
    for phrase in (
        "design-only",
        "no runtime behavior",
        "no gui implementation",
        "no persistence implementation",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no file writes",
        "no settings file creation",
        "no runtime state file creation",
        "no schema file creation",
        "no projectschema mutation",
        "no file dialog",
        "no save dialog",
        "no reload behavior",
        "no export behavior",
        "no clipboard behavior",
        "no open-output-folder behavior",
        "no cli behavior",
        "no automatic activation",
        "no trust restoration",
        "no file rewrite",
        "no file deletion",
        "no dependency uninstall",
        "no solver uninstall",
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
    )
    for phrase in required:
        assert phrase in doc, phrase


def test_design_doc_states_alternate_required_non_actions() -> None:
    doc = _doc()
    assert "no file restoration" in doc or "no file restore" in doc
    assert "no dependency installation" in doc or "no dependency install" in doc
    assert "no issue mutation" in doc or "no issue closure" in doc
    assert "no validation-fail claim" in doc or "no validation failure claim" in doc


def test_design_doc_defines_persistence_gui_and_user_flow() -> None:
    doc = _doc()
    assert "definition of persistence gui" in doc
    assert "view-model/schema-model driven review surface" in doc
    assert "user flow states" in doc
    for state in (
        "no state supplied / persistence unavailable",
        "no explicit persistence request",
        "candidate/source review",
        "acknowledgement review",
        "redaction review required",
        "unredacted path blocked",
        "stale-source/re-preview required",
        "schema version missing",
        "schema migration required",
        "conflict/shared-stack blocked",
        "unsafe claim blocked",
        "ready preview only",
        "future write required",
        "schema review required",
        "persistence error",
    ):
        assert state in doc, state


def test_design_doc_describes_entry_points_and_rendered_sections() -> None:
    doc = _doc()
    assert "gui entry points" in doc
    assert "this gate adds no menu item" in doc
    assert "rendered sections" in doc
    for phrase in (
        "summary",
        "sources/provenance",
        "candidates",
        "acknowledgements",
        "diagnostics",
        "redaction/privacy",
        "schema/migration",
        "stale-source/re-preview",
        "conflicts/shared-stack",
        "unsafe claims",
        "evidence/history",
        "trust/provenance badges",
        "action states",
        "non-action flags",
        "safety guidance",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_summary_fields() -> None:
    doc = _doc()
    for phrase in (
        "state scope",
        "schema version display",
        "candidate count",
        "source count",
        "acknowledgement count",
        "acknowledgement required count",
        "diagnostic count",
        "conflict count",
        "unsafe claim count",
        "stale source count",
        "redaction required count",
        "migration required count",
        "evidence retained",
        "history retained",
        "persistence ready count",
        "persistence blocked count",
        "persistence performed false",
        "file write performed false",
        "settings file created false",
        "projectschema mutation performed false",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_candidate_and_source_review() -> None:
    doc = _doc()
    assert "candidate/source review" in doc
    for phrase in (
        "stack id",
        "display name",
        "source id",
        "source type",
        "source label",
        "source reference display",
        "trust label",
        "activation state",
        "deactivation state",
        "reactivation state",
        "discovery-refresh state",
        "persistence state",
        "readiness",
        "stale source state",
        "re-preview required",
        "redaction status",
        "built-in relationship",
        "shared-stack indicators",
        "evidence/history state",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_acknowledgement_review_and_expiry_policy() -> None:
    doc = _doc()
    assert "acknowledgement review" in doc
    assert "persisted acknowledgement expiry policy" in doc
    for ack in (
        "persistence_not_validation",
        "persistence_not_trust_restoration",
        "persistence_not_install",
        "persistence_no_solver_execution",
        "persistence_not_issue_closure",
        "persistence_not_release_mutation",
        "local_path_redaction_reviewed",
        "persisted_acknowledgements_may_expire",
        "stale_source_requires_repreview",
        "untrusted_source_remains_untrusted",
        "activation_review_required_after_reload",
        "no_discovery_execution",
        "no_plugin_package_import",
        "trust_label_not_certification",
    ):
        assert ack in doc, ack
    for phrase in (
        "expires on reload",
        "expires on source change",
        "expires on schema change",
        "expires on unsafe claims",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_redaction_schema_stale_conflict_and_claim_reviews() -> None:
    doc = _doc()
    for phrase in (
        "redaction/privacy review",
        "raw absolute paths are not shown by default",
        "schema/migration review",
        "missing schema version",
        "unsupported schema version",
        "stale-source/re-preview review",
        "not silently trusted",
        "conflict/shared-stack review",
        "built-ins remain authoritative by default",
        "unsafe-claim review",
        "unsafe claims are blocked display state",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_evidence_history_trust_and_actions() -> None:
    doc = _doc()
    for phrase in (
        "evidence/history review",
        "historical validation evidence retained",
        "skipped-missing remains skipped-missing",
        "trust/provenance behavior",
        "trust label is not certification",
        "user-selected and plugin-provided manifests untrusted by default",
        "action-state model",
        "all save/settings/projectschema/reload/export actions are disabled",
        "all discovery/validation/install/uninstall/solver/issue/release actions",
        "non-action flags",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_relationships() -> None:
    doc = _doc()
    for phrase in (
        "relationship to osw-exp-092 persistence view-model",
        "relationship to osw-exp-093 schema model",
        "relationship to projectschema",
        "relationship to activation/deactivation/reactivation/discovery-refresh",
        "relationship to gui, cli, reload, export, and reports",
        "relationship to live optional validation issues",
    ):
        assert phrase in doc, phrase


def test_design_doc_reserves_persistence_gui_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_PERSISTENCE_GUI_NOT_IMPLEMENTED",
        "OSPMG_PERSISTENCE_GUI_STATE_UNAVAILABLE",
        "OSPMG_PERSISTENCE_GUI_EXPLICIT_REQUEST_REQUIRED",
        "OSPMG_PERSISTENCE_GUI_ACK_REQUIRED",
        "OSPMG_PERSISTENCE_GUI_NOT_VALIDATION",
        "OSPMG_PERSISTENCE_GUI_NOT_TRUST_RESTORE",
        "OSPMG_PERSISTENCE_GUI_NO_INSTALL",
        "OSPMG_PERSISTENCE_GUI_NO_SOLVER_EXECUTION",
        "OSPMG_PERSISTENCE_GUI_NOT_ISSUE_CLOSURE",
        "OSPMG_PERSISTENCE_GUI_NOT_RELEASE_MUTATION",
        "OSPMG_PERSISTENCE_GUI_REDACTION_REQUIRED",
        "OSPMG_PERSISTENCE_GUI_UNREDACTED_PATH_BLOCKED",
        "OSPMG_PERSISTENCE_GUI_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_PERSISTENCE_GUI_SCHEMA_VERSION_REQUIRED",
        "OSPMG_PERSISTENCE_GUI_SCHEMA_MIGRATION_REQUIRED",
        "OSPMG_PERSISTENCE_GUI_UNTRUSTED_SOURCE",
        "OSPMG_PERSISTENCE_GUI_CONFLICT_BLOCKED",
        "OSPMG_PERSISTENCE_GUI_UNSAFE_CLAIM",
        "OSPMG_PERSISTENCE_GUI_EVIDENCE_RETAINED",
        "OSPMG_PERSISTENCE_GUI_HISTORY_RETAINED",
        "OSPMG_PERSISTENCE_GUI_NO_DISCOVERY_EXECUTION",
        "OSPMG_PERSISTENCE_GUI_NO_PLUGIN_IMPORT",
        "OSPMG_PERSISTENCE_GUI_FUTURE_GATE",
    ):
        assert code in text, code


def test_design_doc_lists_future_gates() -> None:
    doc = _doc()
    assert "future gates" in doc
    for gate in (
        "osw-exp-095_optional_solver_plugin_manifest_persistence_gui_implementation",
        "osw-exp-096_optional_solver_plugin_manifest_persistence_cli_design",
        "osw-exp-097_optional_solver_plugin_manifest_export_summary_viewmodel",
        "osw-exp-098_optional_solver_plugin_manifest_export_summary_gui_design",
        "osw-exp-099_optional_solver_plugin_manifest_export_summary_gui_implementation",
        "osw-exp-100_optional_solver_plugin_manifest_state_writer_design",
        "osw-valid-optional_prepared_machine_manifest_state_validation",
    ):
        assert gate in doc, gate


def test_meta_docs_reference_persistence_gui_design() -> None:
    assert "ADR-0128" in DECISION_LOG.read_text(encoding="utf-8")
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        text = path.read_text(encoding="utf-8").lower()
        assert "persistence gui" in text or "persistence gui design" in text, path.name
