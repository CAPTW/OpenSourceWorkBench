from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_state_writer_design.md"
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
        "no writer implementation",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no file writes",
        "no runtime state file creation",
        "no settings file creation",
        "no schema file creation",
        "no export file creation",
        "no report file creation",
        "no reloadable bundle creation",
        "no projectschema mutation",
        "no gui behavior",
        "no cli behavior",
        "no reload behavior",
        "no export behavior",
        "no clipboard behavior",
        "no report attachment",
        "no open-output-folder behavior",
        "no file dialog",
        "no save dialog",
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
    assert "no runtime state files" in doc or "no runtime state file creation" in doc
    assert "no export files" in doc or "no export file creation" in doc
    assert "no report files" in doc or "no report file creation" in doc
    assert "no file restoration" in doc or "no file restore" in doc
    assert "no dependency installation" in doc or "no dependency install" in doc
    assert "no issue mutation" in doc or "no issue closure" in doc
    assert "no validation-fail claim" in doc or "no validation failure claim" in doc


def test_design_doc_defines_state_writer_and_future_storage() -> None:
    doc = _doc()
    assert "definition of state writer" in doc
    assert "future storage-location options" in doc
    for phrase in (
        "project-local `.osw/optional_solver_manifest_state.json`",
        "user-profile/cache location",
        "session-local ephemeral file",
        "explicit user-chosen file",
        "no default write path",
        "disabled until an explicit implementation gate",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_file_format_and_write_preconditions() -> None:
    doc = _doc()
    for phrase in (
        "file format boundary",
        "versioned json-like state",
        "schema version required",
        "stable keys",
        "deterministic ordering",
        "redaction metadata",
        "migration notes",
        "no schema file is created",
        "no actual json writer",
        "write preconditions",
        "explicit user action",
        "explicit state scope",
        "redaction review complete",
        "required acknowledgements satisfied",
        "stale-source/re-preview reviewed",
        "unsafe claims blocked",
        "dry-run/write plan available",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_dry_run_redaction_and_acknowledgements() -> None:
    doc = _doc()
    for phrase in (
        "dry-run/write-plan model",
        "dry-run is required before any future write",
        "dry-run success is not persistence success",
        "write-plan readiness is not validation success",
        "redaction/privacy policy",
        "raw absolute paths are hidden by default",
        "home directories are redacted",
        "secrets, tokens, api keys",
        "acknowledgement model and expiry policy",
        "persisted_acknowledgements_may_expire",
        "expire on reload",
        "source change",
        "schema change",
        "unsafe claims",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_schema_stale_conflict_and_unsafe_claims() -> None:
    doc = _doc()
    for phrase in (
        "schema and migration behavior",
        "unsupported schema is blocked",
        "migration-required state is visible",
        "stale-source and re-preview behavior",
        "old preview records are not silently trusted",
        "conflict/shared-stack behavior",
        "built-ins remain authoritative by default",
        "user/plugin manifests remain untrusted by default",
        "unsafe-claim behavior",
        "validation success",
        "validation failure",
        "unsafe claims must remain blocked display state",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_evidence_trust_atomicity_and_boundaries() -> None:
    doc = _doc()
    for phrase in (
        "evidence/history retention",
        "deactivation history is retained",
        "reactivation history is retained",
        "skipped-missing remains skipped-missing",
        "trust/provenance behavior",
        "trust labels are review labels, not certification",
        "atomicity/error handling design",
        "atomicity is a future implementation requirement",
        "reload boundary",
        "export-summary boundary",
        "projectschema boundary",
        "gui boundary",
        "cli boundary",
        "passive discovery boundary",
        "live optional validation issue boundary",
    ):
        assert phrase in doc, phrase


def test_design_doc_reserves_state_writer_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_STATE_WRITER_NOT_IMPLEMENTED",
        "OSPMG_STATE_WRITER_DRY_RUN_ONLY",
        "OSPMG_STATE_WRITER_ACK_REQUIRED",
        "OSPMG_STATE_WRITER_NOT_VALIDATION",
        "OSPMG_STATE_WRITER_NOT_TRUST_RESTORE",
        "OSPMG_STATE_WRITER_NOT_AUTOMATIC_ACTIVATION",
        "OSPMG_STATE_WRITER_NO_INSTALL",
        "OSPMG_STATE_WRITER_NO_SOLVER_EXECUTION",
        "OSPMG_STATE_WRITER_NOT_ISSUE_CLOSURE",
        "OSPMG_STATE_WRITER_NOT_RELEASE_MUTATION",
        "OSPMG_STATE_WRITER_NOT_CERTIFICATION",
        "OSPMG_STATE_WRITER_REDACTION_REQUIRED",
        "OSPMG_STATE_WRITER_UNREDACTED_PATH_BLOCKED",
        "OSPMG_STATE_WRITER_SECRET_LIKE_CONTENT_BLOCKED",
        "OSPMG_STATE_WRITER_SCHEMA_VERSION_REQUIRED",
        "OSPMG_STATE_WRITER_SCHEMA_UNSUPPORTED",
        "OSPMG_STATE_WRITER_SCHEMA_MIGRATION_REQUIRED",
        "OSPMG_STATE_WRITER_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_STATE_WRITER_UNTRUSTED_SOURCE",
        "OSPMG_STATE_WRITER_CONFLICT_BLOCKED",
        "OSPMG_STATE_WRITER_SHARED_STACK_WARNING",
        "OSPMG_STATE_WRITER_UNSAFE_CLAIM",
        "OSPMG_STATE_WRITER_EVIDENCE_RETAINED",
        "OSPMG_STATE_WRITER_HISTORY_RETAINED",
        "OSPMG_STATE_WRITER_NO_DISCOVERY_EXECUTION",
        "OSPMG_STATE_WRITER_NO_PLUGIN_IMPORT",
        "OSPMG_STATE_WRITER_PROJECT_SCHEMA_MUTATION_DISABLED",
        "OSPMG_STATE_WRITER_RELOAD_DISABLED",
        "OSPMG_STATE_WRITER_EXPORT_DISABLED",
        "OSPMG_STATE_WRITER_FUTURE_GATE",
    ):
        assert code in text, code


def test_design_doc_lists_future_gates() -> None:
    doc = _doc()
    assert "future gates" in doc
    for gate in (
        "osw-exp-101_optional_solver_plugin_manifest_state_writer_viewmodel_or_schema_extension",
        "osw-exp-102_optional_solver_plugin_manifest_state_writer_implementation",
        "osw-exp-103_optional_solver_plugin_manifest_persistence_cli_implementation",
        "osw-exp-104_optional_solver_plugin_manifest_export_summary_cli_design",
        "osw-exp-105_optional_solver_plugin_manifest_export_summary_cli_implementation",
        "osw-exp-106_optional_solver_plugin_manifest_reload_design",
        "osw-exp-107_optional_solver_plugin_manifest_reload_viewmodel",
        "osw-exp-108_optional_solver_plugin_manifest_reload_gui_design",
        "osw-valid-optional_prepared_machine_manifest_state_validation",
    ):
        assert gate in doc, gate


def test_meta_docs_reference_state_writer_design() -> None:
    assert "ADR-0134" in DECISION_LOG.read_text(encoding="utf-8")
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        text = path.read_text(encoding="utf-8").lower()
        assert "state writer" in text or "state-writer" in text, path.name
