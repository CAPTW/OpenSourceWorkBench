from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_plugin_manifest_reload_design.md"
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
        "no reload implementation",
        "no runtime behavior",
        "no source behavior mutation",
        "no source edits",
        "no file parsing implementation",
        "no file reading implementation",
        "no runtime state loading implementation",
    ):
        assert phrase in doc, phrase


def test_design_doc_states_required_non_actions() -> None:
    doc = _doc()
    required = (
        "no default path",
        "no background reload",
        "no reloadable bundle creation",
        "no gui behavior",
        "no cli behavior",
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
    assert "no reloadable bundles" in doc or "no reloadable bundle creation" in doc
    assert "no dependency installation" in doc or "no dependency install" in doc
    assert "no issue mutation" in doc or "no issue closure" in doc
    assert "no validation-fail claim" in doc or "no validation failure claim" in doc
    assert "no bundled-solver claim" in doc or "no bundled solver claim" in doc


def test_design_doc_defines_reload_and_non_meaning() -> None:
    doc = _doc()
    assert "definition of reload" in doc
    assert "explicit user-requested transformation" in doc
    assert "caller-selected persisted ux state file" in doc
    assert "in-memory candidate review state" in doc
    assert "reload non-meaning" in doc
    for phrase in (
        "reload is not validation success",
        "reload is not validation failure",
        "reload is not trust restoration",
        "reload is not automatic activation",
        "reload is not discovery success",
        "reload is not dependency installation",
        "reload is not solver execution",
        "reload is not projectschema mutation",
        "reload is not issue closure",
        "reload is not release mutation",
        "reload is not certification",
        "reload is not export summary",
        "reload is not report generation",
        "reload is not reloadable bundle creation",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_user_flow_states() -> None:
    doc = _doc()
    assert "future user flow states" in doc
    for state in (
        "no_reload_request",
        "target_missing",
        "target_not_selected",
        "source_reference_redacted",
        "schema_review",
        "schema_unsupported",
        "schema_migration_required",
        "payload_kind_mismatch",
        "redaction_review_required",
        "acknowledgement_review_required",
        "stale_source_repreview_required",
        "conflict_review_required",
        "unsafe_claim_blocked",
        "history_evidence_review",
        "reload_preview_ready",
        "reload_blocked",
        "reload_error",
        "future_activation_review_required",
        "future_discovery_refresh_required",
    ):
        assert state in doc, state


def test_design_doc_describes_source_schema_redaction_and_acknowledgements() -> None:
    doc = _doc()
    for phrase in (
        "state source and path policy",
        "explicit caller-selected file only",
        "no plugin folder scan",
        "redacted target display",
        "payload/schema policy",
        "payload_kind",
        "payload_schema_version",
        "writer_version",
        "schema support check",
        "schema migration is a separate future gate",
        "schema mismatch is not validation failure",
        "redaction/privacy policy",
        "raw absolute paths are hidden by default",
        "fingerprints are not trust signals",
        "acknowledgement and expiry policy",
        "persisted_acknowledgements_may_expire",
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
    ):
        assert ack in doc, ack
    for phrase in (
        "expire on reload",
        "source fingerprint change",
        "schema version change",
        "unsafe claim appearance",
        "trust policy change",
        "future discovery-refresh result",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_lifecycle_stale_conflict_and_unsafe_claims() -> None:
    doc = _doc()
    for phrase in (
        "candidate lifecycle reload policy",
        "active candidate state does not mean active after reload",
        "persisted active state requires future activation review",
        "stale-source / re-preview policy",
        "old preview data is not silently trusted",
        "stale-source state is not validation failure",
        "conflict/shared-stack policy",
        "built-ins win by default",
        "persisted state does not override built-ins",
        "unsafe-claim policy",
        "unsafe claims are visible and blocked",
        "unsafe claims are not reloaded as truth",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_evidence_and_trust_boundaries() -> None:
    doc = _doc()
    for phrase in (
        "evidence/history retention",
        "deactivation history is retained",
        "reactivation history is retained",
        "skipped-missing remains skipped-missing",
        "reload is not validation evidence",
        "trust/provenance boundary",
        "user/plugin manifests are untrusted by default",
        "built-ins are authoritative by default",
        "trust label is not certification",
        "reload is not trust restoration",
    ):
        assert phrase in doc, phrase


def test_design_doc_reserves_reload_diagnostics() -> None:
    text = DOC.read_text(encoding="utf-8")
    for code in (
        "OSPMG_RELOAD_NOT_IMPLEMENTED",
        "OSPMG_RELOAD_DESIGN_ONLY",
        "OSPMG_RELOAD_TARGET_REQUIRED",
        "OSPMG_RELOAD_TARGET_MISSING",
        "OSPMG_RELOAD_TARGET_IS_DIRECTORY",
        "OSPMG_RELOAD_TARGET_SYMLINK_REVIEW_REQUIRED",
        "OSPMG_RELOAD_PAYLOAD_KIND_MISMATCH",
        "OSPMG_RELOAD_SCHEMA_VERSION_REQUIRED",
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
    ):
        assert code in text, code


def test_design_doc_describes_actions_and_future_boundaries() -> None:
    doc = _doc()
    for phrase in (
        "action-state model",
        "read reload file",
        "parse reload file",
        "migrate schema",
        "accept reload as trusted",
        "activate reloaded candidate",
        "future gui behavior boundary",
        "no gui implementation in this gate",
        "file dialog behavior requires a separate gate",
        "future cli behavior boundary",
        "no cli implementation in this gate",
        "explicit path only",
        "exit codes must not imply validation success",
    ):
        assert phrase in doc, phrase


def test_design_doc_describes_relationships() -> None:
    doc = _doc()
    for phrase in (
        "relationship to state writer",
        "writer payload schema must be checked before reload",
        "relationship to export summary",
        "export summary is human-review output",
        "export summaries are not reloadable bundles",
        "relationship to projectschema",
        "reloaded state is not projectschema state",
        "relationship to live optional validation issues",
        "issues #6 through #11 remain open",
        "skipped-missing remains skipped-missing",
    ):
        assert phrase in doc, phrase


def test_design_doc_lists_future_test_plan_and_gates() -> None:
    doc = _doc()
    assert "future implementation test plan" in doc
    assert "future gates" in doc
    for phrase in (
        "schema-supported reload view-model",
        "unsupported schema blocker",
        "migration-required blocker",
        "redaction blocker",
        "unredacted-path blocker",
        "secret-like content blocker",
        "expired acknowledgement blocker",
        "stale-source/re-preview blocker",
        "conflict/shared-stack display",
        "unsafe-claim blocker",
        "evidence/history retention",
        "no raw path leak",
        "osw-exp-107_optional_solver_plugin_manifest_reload_viewmodel",
        "osw-exp-108_optional_solver_plugin_manifest_reload_gui_design",
        "osw-exp-109_optional_solver_plugin_manifest_reload_gui_implementation",
        "osw-exp-110_optional_solver_plugin_manifest_reload_cli_design",
        "osw-exp-111_optional_solver_plugin_manifest_reload_cli_implementation",
        "osw-exp-112_optional_solver_plugin_manifest_reload_file_reader_implementation",
    ):
        assert phrase in doc, phrase


def test_meta_docs_reference_reload_design() -> None:
    assert "ADR-0140" in DECISION_LOG.read_text(encoding="utf-8")
    for path in (GUARDRAILS, RISK_REGISTER, VALIDATION_MATRIX, RELEASE_CHECKLIST):
        text = path.read_text(encoding="utf-8").lower()
        assert "reload design" in text or "manifest reload" in text, path.name
