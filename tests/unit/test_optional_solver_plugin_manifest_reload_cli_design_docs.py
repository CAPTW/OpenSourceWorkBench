from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_cli_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


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
        "no reload cli implementation",
        "no cli source edits",
        "no command parser",
        "no command handler",
        "no command registration",
        "no runtime behavior",
        "no source behavior mutation",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no file dialog",
        "no file reader/parser",
        "no file reading",
        "no file parsing",
        "no runtime file reading",
        "no runtime state parsing",
        "no runtime reload",
        "no default reload path",
        "no background reload",
        "no reloadable bundle creation",
        "no export file creation",
        "no report file creation",
        "no clipboard behavior",
        "no report attachment",
        "no open-output-folder behavior",
        "no gui behavior",
        "no projectschema mutation",
        "no live discovery",
        "no passive refresh",
        "no plugin package import",
        "no directory scan",
        "no network fetch",
        "no validation execution",
        "no solver execution",
        "no dependency installation",
        "no dependency uninstall",
        "no solver uninstall",
        "no automatic activation",
        "no trust restoration",
        "no issue mutation",
        "no release mutation",
        "no tag mutation",
        "no asset mutation",
        "no version bump",
        "no validation-pass claim",
        "no validation-fail claim",
        "no issue-closure claim",
        "no bundled-solver claim",
        "no certification claim",
    )
    for phrase in required:
        assert phrase in doc, phrase


def test_design_doc_defines_reload_cli_and_non_meaning() -> None:
    doc = _doc()
    assert "definition of reload cli" in doc
    assert "headless, stdout-first review surface" in doc
    assert "already-built reload view-model records" in doc
    assert "non-meaning of cli reload review" in doc
    for phrase in (
        "cli reload review is not validation success",
        "cli reload review is not validation failure",
        "cli reload review is not trust restoration",
        "cli reload review is not automatic activation",
        "cli reload review is not discovery success",
        "cli reload review is not dependency installation",
        "cli reload review is not solver execution",
        "cli reload review is not projectschema mutation",
        "cli reload review is not issue closure",
        "cli reload review is not release mutation",
        "cli reload review is not certification",
        "cli reload review is not report generation",
        "cli reload review is not export file creation",
        "cli reload review is not reloadable bundle creation",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_command_vocabulary_and_user_flow() -> None:
    doc = _doc()
    for phrase in (
        "future command vocabulary",
        "python -m osw.cli optional-solver-plugin-manifest-reload explain",
        "python -m osw.cli optional-solver-plugin-manifest-reload preview",
        "python -m osw.cli optional-solver-plugin-manifest-reload diagnostics",
        "python -m osw.cli optional-solver-plugin-manifest-reload read-file",
        "python -m osw.cli optional-solver-plugin-manifest-reload accept",
        "disabled/future-only vocabulary",
        "future user flow",
        "no_reload_request",
        "unavailable_no_payload",
        "target_missing",
        "target_not_selected",
        "schema_unsupported",
        "schema_migration_required",
        "payload_kind_mismatch",
        "redaction_review_required",
        "acknowledgement_review_required",
        "stale_source_repreview_required",
        "conflict_review_required",
        "unsafe_claim_blocked",
        "reload_preview_ready",
        "future_activation_review_required",
        "future_discovery_refresh_required",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_state_source_and_output_modes() -> None:
    doc = _doc()
    for phrase in (
        "state source policy",
        "already-built reload view-model records",
        "deterministic sample state",
        "unavailable state",
        "must not read a state file in this gate",
        "must not parse json from disk in this gate",
        "must not infer a default path",
        "any future state-file reader must be a separate file-reader/parser gate",
        "output modes",
        "stable plain text",
        "section-filtered text",
        "diagnostics-only output",
        "json-like stdout output",
        "redaction-focused output",
        "json-like output is stdout-only",
        "stdout output is not a reloadable bundle",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_sections_and_safety_specifics() -> None:
    doc = _doc()
    for phrase in (
        "summary/readiness output",
        "honesty flags must be visible and false",
        "source/provenance output",
        "user/plugin sources are untrusted by default",
        "built-ins are authoritative by default",
        "trust label is not certification",
        "fingerprints are not trust signals",
        "schema/migration output",
        "schema mismatch is not validation failure",
        "candidate lifecycle output",
        "persisted active requires future activation review",
        "acknowledgements and expiry output",
        "redaction/privacy output",
        "raw absolute paths are hidden by default",
        "stale-source/re-preview output",
        "old preview data is not silently trusted",
        "stale-source state is not validation failure",
        "conflict/shared-stack output",
        "persisted state does not override built-ins",
        "unsafe-claim output",
        "unsafe claims are visible and blocked",
        "evidence/history output",
        "skipped-missing remains skipped-missing",
        "reload is not validation evidence",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_reload_acknowledgements() -> None:
    doc = _doc()
    for ack in (
        "reload_not_validation",
        "reload_not_trust_restoration",
        "reload_not_automatic_activation",
        "reload_not_discovery_success",
        "reload_not_dependency_install",
        "reload_no_solver_execution",
        "reload_not_issue_closure",
        "reload_not_release_mutation",
        "reload_not_certification",
        "redaction_reviewed",
        "unredacted_paths_blocked",
        "stale_source_requires_repreview",
        "untrusted_source_remains_untrusted",
        "activation_review_required_after_reload",
        "no_discovery_execution",
        "no_plugin_package_import",
        "no_validation_execution",
        "no_solver_execution",
        "trust_label_not_certification",
        "persisted_acknowledgements_may_expire",
    ):
        assert ack in doc, ack
    for phrase in (
        "source fingerprint change",
        "schema version change",
        "unsafe claim appearance",
        "trust policy change",
        "future discovery-refresh result",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_viewmodel_and_cli_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_RELOAD_NOT_IMPLEMENTED",
        "OSPMG_RELOAD_DESIGN_ONLY",
        "OSPMG_RELOAD_TARGET_REQUIRED",
        "OSPMG_RELOAD_TARGET_MISSING",
        "OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH",
        "OSPMG_RELOAD_SCHEMA_UNSUPPORTED",
        "OSPMG_RELOAD_SCHEMA_MIGRATION_REQUIRED",
        "OSPMG_RELOAD_REDACTION_REQUIRED",
        "OSPMG_RELOAD_UNREDACTED_PATH_BLOCKED",
        "OSPMG_RELOAD_SECRET_LIKE_CONTENT_BLOCKED",
        "OSPMG_RELOAD_ACK_REQUIRED",
        "OSPMG_RELOAD_ACK_EXPIRED",
        "OSPMG_RELOAD_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_RELOAD_UNTRUSTED_SOURCE",
        "OSPMG_RELOAD_CONFLICT_VISIBLE",
        "OSPMG_RELOAD_SHARED_STACK_VISIBLE",
        "OSPMG_RELOAD_UNSAFE_CLAIM_BLOCKED",
        "OSPMG_RELOAD_EVIDENCE_RETAINED",
        "OSPMG_RELOAD_HISTORY_RETAINED",
        "OSPMG_RELOAD_NOT_VALIDATION",
        "OSPMG_RELOAD_NOT_TRUST_RESTORE",
        "OSPMG_RELOAD_NOT_AUTOMATIC_ACTIVATION",
        "OSPMG_RELOAD_NO_DISCOVERY_EXECUTION",
        "OSPMG_RELOAD_NO_PLUGIN_IMPORT",
        "OSPMG_RELOAD_NO_VALIDATION_EXECUTION",
        "OSPMG_RELOAD_NO_SOLVER_EXECUTION",
        "OSPMG_RELOAD_PROJECT_SCHEMA_MUTATION_DISABLED",
        "OSPMG_RELOAD_FUTURE_GATE",
        "OSPMG_RELOAD_CLI_NOT_IMPLEMENTED",
        "OSPMG_RELOAD_CLI_REVIEW_ONLY",
        "OSPMG_RELOAD_CLI_STDOUT_ONLY",
        "OSPMG_RELOAD_CLI_FILE_READER_DISABLED",
        "OSPMG_RELOAD_CLI_FILE_PARSER_DISABLED",
        "OSPMG_RELOAD_CLI_ACCEPT_DISABLED",
        "OSPMG_RELOAD_CLI_NOT_VALIDATION",
        "OSPMG_RELOAD_CLI_NO_DISCOVERY_EXECUTION",
        "OSPMG_RELOAD_CLI_NO_VALIDATION_EXECUTION",
        "OSPMG_RELOAD_CLI_NO_SOLVER_EXECUTION",
        "OSPMG_RELOAD_CLI_PROJECT_SCHEMA_MUTATION_DISABLED",
        "OSPMG_RELOAD_CLI_FUTURE_GATE",
    ):
        assert code in text, code


def test_design_doc_describes_boundaries_and_exit_codes() -> None:
    doc = _doc()
    for phrase in (
        "action-state output",
        "read reload file",
        "parse reload file",
        "accept reload as trusted",
        "file-reader boundary",
        "no file-reader implementation in this design gate",
        "future file reading requires a separate file-reader/parser design",
        "must not smuggle file reading",
        "reload acceptance boundary",
        "there is no reload acceptance behavior in this design gate",
        "exit-code policy",
        "exit code `0` is not validation success",
        "exit code `1` is not validation failure",
        "exit code `2` is not validation failure",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_relationships() -> None:
    doc = _doc()
    for phrase in (
        "relationship to reload view-model",
        "future cli consumes osw-exp-107 reload view-model records",
        "relationship to reload gui",
        "reload gui panel remains read-only/review-only",
        "relationship to persistence cli and state writer",
        "writer payload schema must be checked",
        "relationship to export summary cli/gui",
        "export summaries are not reloadable bundles",
        "relationship to projectschema",
        "reloaded state is not projectschema state",
        "relationship to live optional validation issues",
        "issues `#6` through `#11` remain open",
        "skipped-missing remains skipped-missing",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_future_test_plan_and_gates() -> None:
    doc = _doc()
    assert "future implementation test plan" in doc
    assert "future gates" in doc
    for phrase in (
        "command registration without gui/pyside dependencies",
        "deterministic sample state review",
        "redaction/privacy rows and no raw path leak",
        "read-file disabled/future-only",
        "accept disabled/future-only",
        "json-like output is stdout-only",
        "osw-exp-111_optional_solver_plugin_manifest_reload_cli_implementation",
        "osw-exp-112_optional_solver_plugin_manifest_reload_file_reader_design",
        "osw-exp-113_optional_solver_plugin_manifest_reload_file_reader_implementation",
        "osw-exp-114_optional_solver_plugin_manifest_reload_gui_file_dialog_design",
        "osw-exp-115_optional_solver_plugin_manifest_reload_gui_file_dialog_implementation",
    ):
        assert phrase in doc, phrase


def test_meta_docs_reference_reload_cli_design() -> None:
    assert "ADR-0144" in DECISION_LOG.read_text(encoding="utf-8")
    assert "reload cli" in GUARDRAILS.read_text(encoding="utf-8").lower()
    assert "reload cli design overreach" in RISK_REGISTER.read_text(
        encoding="utf-8"
    ).lower()
    assert "reload cli design" in VALIDATION_MATRIX.read_text(
        encoding="utf-8"
    ).lower()
    assert "reload cli remains design-only" in RELEASE_CHECKLIST.read_text(
        encoding="utf-8"
    ).lower()
    assert "optional solver plugin manifest reload cli design" in CHANGELOG.read_text(
        encoding="utf-8"
    ).lower()
