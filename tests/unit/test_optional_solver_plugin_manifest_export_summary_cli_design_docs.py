from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_export_summary_cli_design.md"
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
        "no export-summary cli implementation",
        "no cli source edits",
        "no runtime behavior",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no export file creation",
        "no report file creation",
        "no reloadable bundle creation",
        "no clipboard behavior",
        "no report attachment",
        "no open-output-folder behavior",
        "no gui behavior",
        "no reload behavior",
        "no projectschema mutation",
        "no live discovery",
        "no passive refresh",
        "no plugin package import",
        "no directory scan",
        "no network fetch",
        "no validation execution",
        "no solver execution",
        "no dependency uninstall",
        "no solver uninstall",
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
    assert "no dependency installation" in doc or "no dependency install" in doc
    assert "no issue mutation" in doc or "no issue closure" in doc
    assert "no validation-fail claim" in doc or "no validation failure claim" in doc
    assert "no bundled-solver claim" in doc or "no bundled solver claim" in doc


def test_design_doc_defines_export_summary_cli_and_commands() -> None:
    doc = _doc()
    assert "definition of export-summary cli" in doc
    assert "explicit, redaction-first, stdout-first" in doc
    assert "future command vocabulary" in doc
    for command in (
        "optional-solver-plugin-manifest-export-summary explain",
        "optional-solver-plugin-manifest-export-summary preview",
        "optional-solver-plugin-manifest-export-summary sections",
        "optional-solver-plugin-manifest-export-summary sources",
        "optional-solver-plugin-manifest-export-summary candidates",
        "optional-solver-plugin-manifest-export-summary acknowledgements",
        "optional-solver-plugin-manifest-export-summary diagnostics",
        "optional-solver-plugin-manifest-export-summary redaction",
        "optional-solver-plugin-manifest-export-summary stale-sources",
        "optional-solver-plugin-manifest-export-summary conflicts",
        "optional-solver-plugin-manifest-export-summary unsafe-claims",
        "optional-solver-plugin-manifest-export-summary evidence",
        "optional-solver-plugin-manifest-export-summary limitations",
        "optional-solver-plugin-manifest-export-summary actions",
        "optional-solver-plugin-manifest-export-summary write-summary",
    ):
        assert command in doc, command


def test_design_doc_describes_source_output_and_file_policy() -> None:
    doc = _doc()
    for phrase in (
        "state source policy",
        "future cli may consume supplied export-summary view-model state",
        "deterministic sample state",
        "unavailable state",
        "output modes",
        "stable plain text",
        "diagnostics-only output",
        "section-filtered output",
        "json-like stdout output",
        "redaction-focused output",
        "stdout-first behavior",
        "stdout output is not a file export",
        "future file-output policy",
        "explicit output path required",
        "no default path",
        "no background export",
        "redaction review required",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_redaction_acknowledgements_and_diagnostics() -> None:
    doc = _doc()
    assert "redaction/privacy policy" in doc
    assert "raw absolute paths are hidden by default" in doc
    assert "fingerprints are not trust signals" in doc
    assert "acknowledgement model" in doc
    for ack in (
        "export_summary_not_validation",
        "export_summary_not_persistence",
        "export_summary_not_reloadable_bundle",
        "export_summary_not_trust_restoration",
        "export_summary_not_automatic_activation",
        "export_summary_not_issue_closure",
        "export_summary_not_release_mutation",
        "export_summary_not_certification",
        "redaction_reviewed",
        "unredacted_paths_blocked",
        "stale_source_requires_repreview",
        "untrusted_source_remains_untrusted",
        "no_discovery_execution",
        "no_plugin_package_import",
        "no_validation_execution",
        "no_solver_execution",
        "trust_label_not_certification",
    ):
        assert ack in doc, ack


def test_design_doc_reserves_export_summary_cli_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_IMPLEMENTED",
        "OSPMG_EXPORT_SUMMARY_CLI_PREVIEW_ONLY",
        "OSPMG_EXPORT_SUMMARY_CLI_STDOUT_ONLY",
        "OSPMG_EXPORT_SUMMARY_CLI_FILE_OUTPUT_DISABLED",
        "OSPMG_EXPORT_SUMMARY_CLI_RELOAD_BUNDLE_DISABLED",
        "OSPMG_EXPORT_SUMMARY_CLI_REPORT_ATTACHMENT_DISABLED",
        "OSPMG_EXPORT_SUMMARY_CLI_CLIPBOARD_DISABLED",
        "OSPMG_EXPORT_SUMMARY_CLI_OPEN_OUTPUT_FOLDER_DISABLED",
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_VALIDATION",
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_PERSISTENCE",
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_RELOADABLE_BUNDLE",
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_TRUST_RESTORE",
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_AUTOMATIC_ACTIVATION",
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_ISSUE_CLOSURE",
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_RELEASE_MUTATION",
        "OSPMG_EXPORT_SUMMARY_CLI_NOT_CERTIFICATION",
        "OSPMG_EXPORT_SUMMARY_CLI_REDACTION_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_CLI_UNREDACTED_PATH_BLOCKED",
        "OSPMG_EXPORT_SUMMARY_CLI_SECRET_LIKE_CONTENT_BLOCKED",
        "OSPMG_EXPORT_SUMMARY_CLI_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_EXPORT_SUMMARY_CLI_UNTRUSTED_SOURCE",
        "OSPMG_EXPORT_SUMMARY_CLI_CONFLICT_VISIBLE",
        "OSPMG_EXPORT_SUMMARY_CLI_SHARED_STACK_VISIBLE",
        "OSPMG_EXPORT_SUMMARY_CLI_UNSAFE_CLAIM_BLOCKED",
        "OSPMG_EXPORT_SUMMARY_CLI_EVIDENCE_RETAINED",
        "OSPMG_EXPORT_SUMMARY_CLI_HISTORY_RETAINED",
        "OSPMG_EXPORT_SUMMARY_CLI_NO_DISCOVERY_EXECUTION",
        "OSPMG_EXPORT_SUMMARY_CLI_NO_PLUGIN_IMPORT",
        "OSPMG_EXPORT_SUMMARY_CLI_NO_VALIDATION_EXECUTION",
        "OSPMG_EXPORT_SUMMARY_CLI_NO_SOLVER_EXECUTION",
        "OSPMG_EXPORT_SUMMARY_CLI_PROJECT_SCHEMA_MUTATION_DISABLED",
        "OSPMG_EXPORT_SUMMARY_CLI_FUTURE_GATE",
    ):
        assert code in text, code


def test_design_doc_describes_review_behaviors() -> None:
    doc = _doc()
    for phrase in (
        "stale-source / re-preview behavior",
        "stale sources are visible",
        "stale sources are not silently trusted",
        "conflict/shared-stack behavior",
        "built-ins win by default",
        "shared-stack warnings are visible",
        "unsafe-claim behavior",
        "unsafe claims are visible and blocked",
        "unsafe claims are not exported as truth",
        "evidence/history retention",
        "deactivation history is retained",
        "reactivation history is retained",
        "skipped-missing remains skipped-missing",
        "trust/provenance boundary",
        "user/plugin manifests are untrusted by default",
        "built-ins are authoritative by default",
        "trust label is not certification",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_actions_exit_policy_and_relationships() -> None:
    doc = _doc()
    for phrase in (
        "action-state model",
        "write export-summary file",
        "create report file",
        "attach to report",
        "copy to clipboard",
        "open output folder",
        "create reloadable bundle",
        "exit-code policy",
        "exit code `0` is not validation success",
        "exit code `1` is not validation failure",
        "relationship to osw-exp-097 export-summary view-model",
        "relationship to osw-exp-099 export-summary gui",
        "relationship to osw-exp-103 persistence cli",
        "relationship to projectschema",
        "relationship to live optional validation issues",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_future_gates() -> None:
    doc = _doc()
    assert "future gates" in doc
    for gate in (
        "osw-exp-105_optional_solver_plugin_manifest_export_summary_cli_implementation",
        "osw-exp-106_optional_solver_plugin_manifest_reload_design",
        "osw-exp-107_optional_solver_plugin_manifest_reload_viewmodel",
        "osw-exp-108_optional_solver_plugin_manifest_reload_gui_design",
        "osw-exp-109_optional_solver_plugin_manifest_reload_gui_implementation",
        "osw-exp-110_optional_solver_plugin_manifest_reload_cli_design",
        "osw-exp-111_optional_solver_plugin_manifest_reload_cli_implementation",
        "osw-valid-optional_prepared_machine_manifest_state_validation",
    ):
        assert gate in doc, gate


def test_meta_docs_reference_export_summary_cli_design() -> None:
    assert "ADR-0138" in DECISION_LOG.read_text(encoding="utf-8")
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        text = path.read_text(encoding="utf-8").lower()
        assert "export-summary cli" in text, path.name
