from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_export_summary_gui_design.md"
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
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no file export",
        "no file writes",
        "no export file creation",
        "no report file creation",
        "no clipboard behavior",
        "no report attachment",
        "no open-output-folder behavior",
        "no reloadable bundle creation",
        "no persistence implementation",
        "no settings file creation",
        "no runtime state file creation",
        "no schema file creation",
        "no projectschema mutation",
        "no cli behavior",
        "no reload behavior",
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
    assert "no runtime persistence behavior" in doc
    assert "no file restoration" in doc or "no file restore" in doc
    assert "no dependency installation" in doc or "no dependency install" in doc
    assert "no issue mutation" in doc or "no issue closure" in doc
    assert "no validation-fail claim" in doc or "no validation failure claim" in doc


def test_design_doc_defines_export_summary_gui_and_user_flow() -> None:
    doc = _doc()
    assert "definition of export-summary gui" in doc
    assert "view-model-driven review surface" in doc
    assert "user flow states" in doc
    for state in (
        "no state supplied / export summary unavailable",
        "no explicit export-summary request",
        "summary preview",
        "source/provenance review",
        "candidate summary review",
        "acknowledgement review",
        "redaction review required",
        "unredacted path blocked",
        "stale-source/re-preview required",
        "conflict/shared-stack blocked",
        "unsafe claim blocked",
        "limitations visible",
        "ready preview only",
        "future file export required",
        "future clipboard required",
        "future report attachment required",
        "future reloadable bundle required",
        "export summary error",
    ):
        assert state in doc, state


def test_design_doc_describes_entry_points_and_rendered_sections() -> None:
    doc = _doc()
    assert "gui entry points" in doc
    assert "this gate adds no menu item" in doc
    assert "rendered sections" in doc
    for phrase in (
        "header",
        "sections list",
        "summary",
        "sources/provenance",
        "candidates",
        "acknowledgements",
        "diagnostics",
        "redaction/privacy",
        "stale-source/re-preview",
        "conflicts/shared-stack",
        "unsafe claims",
        "evidence/history",
        "limitations",
        "non-action flags",
        "action states",
        "safety guidance",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_header_summary_fields() -> None:
    doc = _doc()
    for phrase in (
        "header / summary section",
        "summary kind",
        "state scope",
        "generated-by display",
        "schema version display",
        "source count",
        "candidate count",
        "acknowledgement count",
        "diagnostic count",
        "warning count",
        "error count",
        "conflict count",
        "unsafe claim count",
        "stale source count",
        "redaction required count",
        "evidence retained",
        "history retained",
        "limitations count",
        "export performed false",
        "file write performed false",
        "clipboard performed false",
        "report attachment performed false",
        "reloadable bundle created false",
        "persistence performed false",
        "validation success claimed false",
        "validation failure claimed false",
        "issue closure claimed false",
        "release mutation performed false",
        "certification claimed false",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_section_source_candidate_and_ack_rendering() -> None:
    doc = _doc()
    for phrase in (
        "section rendering",
        "section id",
        "severity",
        "source/provenance review",
        "source id",
        "source label",
        "source type",
        "source reference display",
        "trust label is not certification",
        "candidate summary review",
        "stack id",
        "display name",
        "activation state",
        "deactivation state",
        "reactivation state",
        "discovery-refresh state",
        "persistence state",
        "export-summary state",
        "required acknowledgements",
        "acknowledgement review",
        "export_not_validation",
        "export_not_persistence",
        "export_not_reloadable_bundle",
        "redaction_reviewed",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_diagnostics_redaction_and_stale_source_reviews() -> None:
    doc = _doc()
    for phrase in (
        "diagnostic rendering",
        "diagnostic code",
        "suggested fix",
        "redaction/privacy review",
        "raw reference supplied",
        "unredacted path blocked",
        "secret-like content blocked",
        "stale-source/re-preview review",
        "old preview not silently trusted",
        "no file io performed yes",
        "no file restoration performed yes",
        "no file rewrite performed yes",
        "no file deletion performed yes",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_conflict_unsafe_evidence_and_limitations() -> None:
    doc = _doc()
    for phrase in (
        "conflict/shared-stack review",
        "built-ins win by default",
        "exported state does not override built-in",
        "unsafe-claim review",
        "unsafe claims include validation success",
        "unsafe claims must remain blocked display state",
        "evidence/history review",
        "deactivation history state",
        "reactivation history state",
        "historical validation evidence retained",
        "skipped-missing remains skipped-missing",
        "limitation review",
        "limitations are first-class visible rows",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_trust_non_action_and_actions() -> None:
    doc = _doc()
    for phrase in (
        "trust/provenance behavior",
        "user-selected and plugin-provided manifests are untrusted by default",
        "built-ins remain authoritative by default",
        "trust label is not certification",
        "non-action flag rendering",
        "projectschema mutation performed false",
        "gui implementation performed false",
        "cli behavior performed false",
        "source behavior mutation performed false",
        "action-state model",
        "request file export: disabled/future-only",
        "copy to clipboard: disabled/future-only",
        "attach report: disabled/future-only",
        "create reloadable bundle: disabled/future-only",
        "persist state: disabled/future-only",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_relationships() -> None:
    doc = _doc()
    for phrase in (
        "relationship to osw-exp-091 export-summary design",
        "relationship to osw-exp-097 export-summary view-model",
        "relationship to persistence view-model, schema model, gui, and cli",
        "relationship to projectschema",
        "relationship to reports",
        "relationship to live optional validation issues",
        "#6",
        "#11",
        "an export summary gui is not live optional validation",
    ):
        assert phrase in doc, phrase


def test_design_doc_reserves_export_summary_gui_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_EXPORT_SUMMARY_GUI_NOT_IMPLEMENTED",
        "OSPMG_EXPORT_SUMMARY_GUI_STATE_UNAVAILABLE",
        "OSPMG_EXPORT_SUMMARY_GUI_EXPLICIT_REQUEST_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_GUI_ACK_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_GUI_NOT_VALIDATION",
        "OSPMG_EXPORT_SUMMARY_GUI_NOT_PERSISTENCE",
        "OSPMG_EXPORT_SUMMARY_GUI_NOT_RELOADABLE_BUNDLE",
        "OSPMG_EXPORT_SUMMARY_GUI_REDACTION_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_GUI_UNREDACTED_PATH_BLOCKED",
        "OSPMG_EXPORT_SUMMARY_GUI_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_GUI_CONFLICT_BLOCKED",
        "OSPMG_EXPORT_SUMMARY_GUI_UNSAFE_CLAIM",
        "OSPMG_EXPORT_SUMMARY_GUI_EVIDENCE_RETAINED",
        "OSPMG_EXPORT_SUMMARY_GUI_HISTORY_RETAINED",
        "OSPMG_EXPORT_SUMMARY_GUI_LIMITATION_VISIBLE",
        "OSPMG_EXPORT_SUMMARY_GUI_NO_FILE_EXPORT",
        "OSPMG_EXPORT_SUMMARY_GUI_NO_CLIPBOARD",
        "OSPMG_EXPORT_SUMMARY_GUI_NO_REPORT_ATTACHMENT",
        "OSPMG_EXPORT_SUMMARY_GUI_FUTURE_GATE",
    ):
        assert code in text, code


def test_design_doc_lists_future_gates() -> None:
    doc = _doc()
    assert "future gates" in doc
    for gate in (
        "osw-exp-099_optional_solver_plugin_manifest_export_summary_gui_implementation",
        "osw-exp-100_optional_solver_plugin_manifest_state_writer_design",
        "osw-exp-101_optional_solver_plugin_manifest_state_writer_viewmodel_or_schema_extension",
        "osw-exp-102_optional_solver_plugin_manifest_state_writer_implementation",
        "osw-exp-103_optional_solver_plugin_manifest_persistence_cli_implementation",
        "osw-exp-104_optional_solver_plugin_manifest_export_summary_cli_design",
        "osw-exp-105_optional_solver_plugin_manifest_export_summary_cli_implementation",
        "osw-valid-optional_prepared_machine_manifest_state_validation",
    ):
        assert gate in doc, gate


def test_meta_docs_reference_export_summary_gui_design() -> None:
    assert "ADR-0132" in DECISION_LOG.read_text(encoding="utf-8")
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        text = path.read_text(encoding="utf-8").lower()
        assert "export-summary gui" in text or "export summary gui" in text, path.name
