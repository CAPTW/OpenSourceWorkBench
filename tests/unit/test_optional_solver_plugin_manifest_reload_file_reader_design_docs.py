from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_file_reader_design.md"
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


def test_design_doc_is_design_only() -> None:
    doc = _doc()
    for phrase in (
        "design-only",
        "no file reader implementation",
        "no parser implementation",
        "no runtime file reading",
        "no runtime state parsing",
        "no runtime reload",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_no_source_edits() -> None:
    doc = _doc()
    for phrase in (
        "no source edits",
        "no cli source edits",
        "no gui source edits",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no default reload path",
        "no background reload",
        "no directory scan",
        "no network fetch",
        "no plugin package import",
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


def test_design_doc_defines_reader_and_non_meaning() -> None:
    doc = _doc()
    assert "definition of reload file reader" in doc
    assert "non-meaning of reading a reload file" in doc
    for phrase in (
        "reading a reload file is not validation success",
        "reading a reload file is not validation failure",
        "reading a reload file is not trust restoration",
        "reading a reload file is not automatic activation",
        "reading a reload file is not discovery success",
        "reading a reload file is not dependency installation",
        "reading a reload file is not solver execution",
        "reading a reload file is not projectschema mutation",
        "reading a reload file is not issue closure",
        "reading a reload file is not release mutation",
        "reading a reload file is not certification",
        "reading a reload file is not report generation",
        "reading a reload file is not reloadable bundle acceptance",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_required_policies() -> None:
    doc = _doc()
    for phrase in (
        "explicit path policy",
        "file eligibility policy",
        "encoding and json policy",
        "payload kind and schema policy",
        "writer metadata and provenance policy",
        "non-action flag verification",
        "redaction/privacy policy",
        "acknowledgement and expiry policy",
        "candidate lifecycle policy",
        "stale-source/re-preview policy",
        "conflict/shared-stack policy",
        "unsafe-claim policy",
        "evidence/history policy",
        "reader report model",
        "security and privacy review",
    ):
        assert phrase in doc, phrase


def test_design_doc_explicit_path_and_eligibility_specifics() -> None:
    doc = _doc()
    for phrase in (
        "no default path",
        "no glob",
        "no directory recursion",
        "a missing file is a diagnostic, not hidden success",
        "regular file only",
        "reject directories",
        "reject symlinks unless a future explicit policy allows them",
        "reject empty file",
        "extension is only a hint, not trust",
        "content validation is authoritative",
        "a json object root is required",
        "no script execution from loaded data",
        "no dynamic import from loaded data",
        "schema mismatch is not validation failure",
        "trust label is not certification",
        "fingerprints are not trust signals",
        "built-ins remain authoritative by default",
        "built-ins win by default",
        "persisted state does not override built-ins",
        "skipped-missing remains skipped-missing",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_reader_acknowledgements_and_expiry() -> None:
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
        "file reader policy change",
    ):
        assert phrase in doc, phrase


def test_design_doc_reserves_reader_diagnostics() -> None:
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
    ):
        assert code in text, code


def test_design_doc_describes_relationships() -> None:
    doc = _doc()
    for phrase in (
        "relationship to state writer",
        "relationship to reload view-model",
        "relationship to reload cli",
        "relationship to reload gui",
        "relationship to projectschema",
        "relationship to live optional validation issues",
        "the reader is not the writer",
        "the view-model remains pure and path-free",
        "exit codes must not imply validation pass/fail",
        "loaded state is not projectschema state",
        "issues `#6` through `#11` remain open",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_future_test_plan_and_gates() -> None:
    doc = _doc()
    assert "future implementation test plan" in doc
    assert "future gates" in doc
    for phrase in (
        "explicit path only",
        "missing file diagnostic",
        "payload kind mismatch rejected",
        "unsupported schema blocked",
        "unredacted path blocked",
        "unsafe claims blocked",
        "safe mapping feeds reload view-model",
        "no raw path leak",
        "no files written",
        "osw-exp-113_optional_solver_plugin_manifest_reload_file_reader_implementation",
        "osw-exp-114_optional_solver_plugin_manifest_reload_cli_explicit_path_design",
        "osw-exp-115_optional_solver_plugin_manifest_reload_cli_explicit_path_implementation",
        "osw-exp-116_optional_solver_plugin_manifest_reload_gui_file_dialog_design",
        "osw-exp-117_optional_solver_plugin_manifest_reload_gui_file_dialog_implementation",
    ):
        assert phrase in doc, phrase


def test_meta_docs_reference_reload_file_reader_design() -> None:
    assert "ADR-0146" in DECISION_LOG.read_text(encoding="utf-8")
    assert "reload file reader" in GUARDRAILS.read_text(encoding="utf-8").lower()
    assert "reload file reader design overreach" in RISK_REGISTER.read_text(
        encoding="utf-8"
    ).lower()
    assert "reload file reader design" in VALIDATION_MATRIX.read_text(
        encoding="utf-8"
    ).lower()
    assert "reload file reader remains design-only" in RELEASE_CHECKLIST.read_text(
        encoding="utf-8"
    ).lower()
    assert (
        "optional solver plugin manifest reload file reader"
        in CHANGELOG.read_text(encoding="utf-8").lower()
    )
