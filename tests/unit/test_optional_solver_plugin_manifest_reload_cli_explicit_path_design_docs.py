from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_cli_explicit_path_design.md"
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


def test_design_doc_is_design_only_and_no_source_edits() -> None:
    doc = _doc()
    for phrase in (
        "design-only",
        "no cli explicit-path implementation",
        "no cli source edits",
        "no runtime source edits",
        "no file-reader source edits",
        "no gui source edits",
        "no path argument implementation",
        "no runtime behavior",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no runtime file reading",
        "no runtime state parsing",
        "no runtime reload acceptance",
        "no default reload path",
        "no background reload",
        "no directory scan",
        "no network fetch",
        "no plugin package import",
        "no gui file dialog",
        "no reloadable bundle creation",
        "no export file creation",
        "no report file creation",
        "no clipboard behavior",
        "no report attachment",
        "no open-output-folder behavior",
        "no projectschema mutation",
        "no live discovery",
        "no passive refresh",
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
        "no bundled-solver claim",
        "no certification claim",
    )
    for phrase in required:
        assert phrase in doc, phrase


def test_design_doc_defines_preview_and_non_meaning() -> None:
    doc = _doc()
    assert "definition of cli explicit-path reload preview" in doc
    assert "non-meaning of cli explicit-path preview" in doc
    for phrase in (
        "cli explicit-path preview is not validation success",
        "cli explicit-path preview is not validation failure",
        "cli explicit-path preview is not trust restoration",
        "cli explicit-path preview is not automatic activation",
        "cli explicit-path preview is not discovery success",
        "cli explicit-path preview is not dependency installation",
        "cli explicit-path preview is not solver execution",
        "cli explicit-path preview is not projectschema mutation",
        "cli explicit-path preview is not issue closure",
        "cli explicit-path preview is not release mutation",
        "cli explicit-path preview is not certification",
        "cli explicit-path preview is not report generation",
        "cli explicit-path preview is not reloadable bundle acceptance",
    ):
        assert phrase in doc, phrase


def test_design_doc_reserves_future_command_and_option_vocabulary() -> None:
    doc = _doc()
    assert "future command and option vocabulary" in doc
    for phrase in (
        "load-preview --path <state-file>",
        "--json",
        "--reader-diagnostics-only",
        "--viewmodel-preview-only",
        "--max-bytes <n>",
        "--allow-symlink",
        "--allow-migration",
        "--allow-unredacted-paths",
        "--allow-secret-like-values",
        "this gate adds no command parser branch",
        "no runtime file reading",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_future_flow_and_path_policy() -> None:
    doc = _doc()
    for phrase in (
        "future user flow",
        "path option policy",
        "user explicitly supplies",
        "call the library reader",
        "renders reader diagnostics",
        "no default reload path",
        "no implicit current-project path",
        "no saved recent-path fallback",
        "no glob expansion",
        "no directory recursion",
        "path display redacted",
        "a path option does not make a state file trusted",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_reader_invocation_policy() -> None:
    doc = _doc()
    for phrase in (
        "reader invocation policy",
        "read_optional_solver_plugin_manifest_reload_file",
        "call only the osw-exp-113 library reader",
        "pass exactly the caller-supplied path",
        "render reader diagnostics before any view-model output",
        "build reload view-model output only from `safe_mapping`",
        "never treat `ready_for_viewmodel` as validation success",
        "must not bypass the reader",
        "ad hoc json loading",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_output_modes_and_reader_diagnostics() -> None:
    doc = _doc()
    assert "output modes" in doc
    assert "reader diagnostics output" in doc
    for phrase in (
        "stable plain text",
        "deterministic json to stdout",
        "reader-diagnostics-only output",
        "viewmodel-preview-only output",
        "redacted target display",
        "ready-for-viewmodel flag",
        "reader diagnostics are review diagnostics only",
        "not validation success and not validation failure",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_reader_diagnostic_codes() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_RELOAD_READER_FILE_MISSING",
        "OSPMG_RELOAD_READER_NOT_REGULAR_FILE",
        "OSPMG_RELOAD_READER_SYMLINK_BLOCKED",
        "OSPMG_RELOAD_READER_FILE_TOO_LARGE",
        "OSPMG_RELOAD_READER_EMPTY_FILE",
        "OSPMG_RELOAD_READER_ENCODING_ERROR",
        "OSPMG_RELOAD_READER_JSON_PARSE_ERROR",
        "OSPMG_RELOAD_READER_ROOT_NOT_OBJECT",
        "OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED",
        "OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH",
        "OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED",
        "OSPMG_RELOAD_READER_MIGRATION_REQUIRED",
        "OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED",
        "OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED",
        "OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED",
        "OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED",
        "OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED",
        "OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED",
        "OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY",
        "OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY",
        "OSPMG_RELOAD_READER_REVIEW_ONLY",
        "OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL",
        "OSPMG_RELOAD_READER_READ_COMPLETED",
    ):
        assert code in text, code


def test_design_doc_describes_viewmodel_schema_and_privacy_outputs() -> None:
    doc = _doc()
    for phrase in (
        "reload view-model output after reader success",
        "schema/migration output",
        "redaction/privacy output",
        "safe mapping",
        "source label passed to the view-model should be the reader's redacted",
        "schema mismatch is not validation failure",
        "migration is future-gated",
        "raw absolute paths are hidden by default",
        "fingerprints and hashes are not trust signals",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_acknowledgement_and_lifecycle_outputs() -> None:
    doc = _doc()
    assert "acknowledgement/expiry output" in doc
    assert "candidate lifecycle output" in doc
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
        "future discovery-refresh result",
        "file-reader policy change",
        "inactive preview remains review-only",
        "persisted active requires future activation review",
        "skipped-missing remains skipped-missing",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_review_blocker_outputs() -> None:
    doc = _doc()
    for phrase in (
        "stale-source/re-preview output",
        "conflict/shared-stack output",
        "unsafe-claim output",
        "evidence/history output",
        "old preview data is not silently trusted",
        "built-ins win by default",
        "persisted state does not override built-ins",
        "unsafe claims are visible and blocked",
        "unsafe claims include validation success",
        "unsafe claims include validation failure",
        "historical evidence remains reference-only",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_action_state_and_exit_codes() -> None:
    doc = _doc()
    assert "action-state output" in doc
    assert "exit-code policy" in doc
    for phrase in (
        "accept reload as trusted",
        "activate reloaded candidate",
        "refresh discovery",
        "validate solver",
        "execute solver",
        "mutate projectschema",
        "claim validation success",
        "claim validation failure",
        "`0`: the command rendered reader diagnostics",
        "this is not validation success",
        "`1`: reader or view-model review is blocked",
        "this is not validation failure",
        "no exit code closes issues",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_relationships_and_live_issues() -> None:
    doc = _doc()
    for phrase in (
        "relationship to reload file reader",
        "relationship to reload view-model",
        "relationship to current reload cli",
        "relationship to reload gui",
        "relationship to state writer",
        "relationship to projectschema",
        "relationship to live optional validation issues",
        "thin caller of the osw-exp-113 reload file reader",
        "the view-model source",
        "no path argument implementation",
        "no gui file dialog",
        "the state writer creates explicit local ux state files",
        "issues `#6` through `#11` remain open",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_security_future_tests_and_gates() -> None:
    doc = _doc()
    assert "security and privacy review" in doc
    assert "future implementation test plan" in doc
    assert "future gates" in doc
    for phrase in (
        "potentially hostile data",
        "no dynamic imports from payload content",
        "malicious payload claims are blocked as data",
        "command registration for `load-preview --path`",
        "reader blockers suppress view-model construction",
        "reader safe mapping feeds reload view-model",
        "source label remains redacted",
        "no files written",
        "osw-exp-115_optional_solver_plugin_manifest_reload_cli_explicit_path_implementation",
        "osw-exp-116_optional_solver_plugin_manifest_reload_gui_file_dialog_design",
        "osw-exp-117_optional_solver_plugin_manifest_reload_gui_file_dialog_implementation",
    ):
        assert phrase in doc, phrase


def test_meta_docs_reference_cli_explicit_path_design() -> None:
    assert "ADR-0148" in DECISION_LOG.read_text(encoding="utf-8")
    assert "reload cli explicit-path design" in GUARDRAILS.read_text(
        encoding="utf-8"
    ).lower()
    assert "reload cli explicit-path design overreach" in RISK_REGISTER.read_text(
        encoding="utf-8"
    ).lower()
    assert "reload cli explicit-path design" in VALIDATION_MATRIX.read_text(
        encoding="utf-8"
    ).lower()
    assert "reload cli explicit-path design remains design-only" in (
        RELEASE_CHECKLIST.read_text(encoding="utf-8").lower()
    )
    assert (
        "optional solver plugin manifest reload cli explicit-path"
        in CHANGELOG.read_text(encoding="utf-8").lower()
    )
