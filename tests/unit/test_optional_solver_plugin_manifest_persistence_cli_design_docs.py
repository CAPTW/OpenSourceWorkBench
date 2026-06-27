from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_persistence_cli_design.md"
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
        "no cli implementation",
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
        "no save command",
        "no load command",
        "no reload behavior",
        "no export behavior",
        "no clipboard behavior",
        "no open-output-folder behavior",
        "no gui behavior",
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


def test_design_doc_defines_persistence_cli_and_commands() -> None:
    doc = _doc()
    assert "definition of persistence cli" in doc
    assert "dry-run/review/explain interface" in doc
    assert "future command vocabulary" in doc
    for phrase in (
        "doctor/readiness",
        "explain/diagnostics",
        "preview/state summary",
        "redaction review",
        "schema/migration review",
        "acknowledgement review",
        "stale-source/re-preview review",
        "conflict/shared-stack review",
        "unsafe-claim review",
        "evidence/history review",
        "action-state review",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_output_modes_and_entry_points() -> None:
    doc = _doc()
    assert "cli output modes" in doc
    assert "cli entry points" in doc
    for phrase in (
        "plain text",
        "table-like text",
        "json-like dry-run summary",
        "diagnostics-only output",
        "redaction report",
        "non-action flag report",
        "no output file is written",
        "stdout output is not a reloadable bundle",
        "this gate adds no command",
        "this gate changes no parser",
        "this gate changes no cli source",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_user_flow_states() -> None:
    doc = _doc()
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


def test_design_doc_describes_dry_run_and_summary_output() -> None:
    doc = _doc()
    assert "dry-run and non-action model" in doc
    assert "summary output section" in doc
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
        "runtime state file created false",
        "projectschema mutation performed false",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_acknowledgement_output_and_expiry() -> None:
    doc = _doc()
    assert "acknowledgement output and expiry policy" in doc
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


def test_design_doc_describes_review_outputs() -> None:
    doc = _doc()
    for phrase in (
        "candidate/source output",
        "redaction/privacy output",
        "raw absolute paths are not shown by default",
        "schema/migration output",
        "stale-source/re-preview output",
        "not silently trusted",
        "conflict/shared-stack output",
        "built-ins remain authoritative by default",
        "unsafe-claim output",
        "unsafe claims are blocked display state",
        "evidence/history output",
        "historical validation evidence retained",
        "trust/provenance behavior",
        "trust label is not certification",
        "action-state output",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_exit_codes_and_relationships() -> None:
    doc = _doc()
    for phrase in (
        "exit-code policy",
        "exit code `0` is not validation success",
        "exit code `1` is not validation failure",
        "relationship to osw-exp-092 persistence view-model",
        "relationship to osw-exp-093 schema model",
        "relationship to osw-exp-095 persistence gui",
        "relationship to projectschema",
        "relationship to live optional validation issues",
    ):
        assert phrase in doc, phrase


def test_design_doc_reserves_persistence_cli_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_PERSISTENCE_CLI_NOT_IMPLEMENTED",
        "OSPMG_PERSISTENCE_CLI_STATE_UNAVAILABLE",
        "OSPMG_PERSISTENCE_CLI_EXPLICIT_REQUEST_REQUIRED",
        "OSPMG_PERSISTENCE_CLI_ACK_REQUIRED",
        "OSPMG_PERSISTENCE_CLI_NOT_VALIDATION",
        "OSPMG_PERSISTENCE_CLI_NOT_TRUST_RESTORE",
        "OSPMG_PERSISTENCE_CLI_NO_INSTALL",
        "OSPMG_PERSISTENCE_CLI_NO_SOLVER_EXECUTION",
        "OSPMG_PERSISTENCE_CLI_NOT_ISSUE_CLOSURE",
        "OSPMG_PERSISTENCE_CLI_NOT_RELEASE_MUTATION",
        "OSPMG_PERSISTENCE_CLI_REDACTION_REQUIRED",
        "OSPMG_PERSISTENCE_CLI_UNREDACTED_PATH_BLOCKED",
        "OSPMG_PERSISTENCE_CLI_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_PERSISTENCE_CLI_SCHEMA_VERSION_REQUIRED",
        "OSPMG_PERSISTENCE_CLI_SCHEMA_MIGRATION_REQUIRED",
        "OSPMG_PERSISTENCE_CLI_UNTRUSTED_SOURCE",
        "OSPMG_PERSISTENCE_CLI_CONFLICT_BLOCKED",
        "OSPMG_PERSISTENCE_CLI_UNSAFE_CLAIM",
        "OSPMG_PERSISTENCE_CLI_EVIDENCE_RETAINED",
        "OSPMG_PERSISTENCE_CLI_HISTORY_RETAINED",
        "OSPMG_PERSISTENCE_CLI_NO_DISCOVERY_EXECUTION",
        "OSPMG_PERSISTENCE_CLI_NO_PLUGIN_IMPORT",
        "OSPMG_PERSISTENCE_CLI_FUTURE_GATE",
    ):
        assert code in text, code


def test_design_doc_lists_future_gates() -> None:
    doc = _doc()
    assert "future gates" in doc
    for gate in (
        "osw-exp-097_optional_solver_plugin_manifest_export_summary_viewmodel",
        "osw-exp-098_optional_solver_plugin_manifest_export_summary_gui_design",
        "osw-exp-099_optional_solver_plugin_manifest_export_summary_gui_implementation",
        "osw-exp-100_optional_solver_plugin_manifest_state_writer_design",
        "osw-exp-101_optional_solver_plugin_manifest_state_writer_viewmodel_or_schema_extension",
        "osw-exp-102_optional_solver_plugin_manifest_state_writer_implementation",
        "osw-exp-103_optional_solver_plugin_manifest_persistence_cli_implementation",
        "osw-valid-optional_prepared_machine_manifest_state_validation",
    ):
        assert gate in doc, gate


def test_meta_docs_reference_persistence_cli_design() -> None:
    assert "ADR-0130" in DECISION_LOG.read_text(encoding="utf-8")
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        text = path.read_text(encoding="utf-8").lower()
        assert "persistence cli" in text, path.name
