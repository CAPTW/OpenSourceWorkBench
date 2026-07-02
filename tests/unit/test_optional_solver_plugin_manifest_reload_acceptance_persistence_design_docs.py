from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _assert_any(text: str, *phrases: str) -> None:
    normalised = _normalise(text)
    assert any(_normalise(phrase) in normalised for phrase in phrases), phrases


def test_design_doc_exists_and_records_design_only_non_actions() -> None:
    assert DOC.exists()
    text = _read(DOC)
    required = (
        "design-only",
        "no reload acceptance persistence implementation",
        "no source edits",
        "no CLI source edits",
        "no GUI source edits",
        "no runtime source edits",
        "no state-writer source edits",
        "no file-reader source edits",
        "no reload view-model source edits",
        "no reload acceptance view-model source edits",
        "no persistence writes",
        "no checked-in state files",
        "no ProjectSchema mutation",
        "no runtime reload acceptance",
        "no active acceptance mutation",
        "no file IO",
        "no file reading",
        "no file parsing",
        "no reader invocation",
        "no CLI behavior",
        "no GUI behavior",
        "no subprocess",
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
        _assert_any(text, phrase)


def test_design_doc_defines_persistence_sections() -> None:
    text = _read(DOC)
    required = (
        "Definition Of Reload Acceptance Persistence",
        "Non-Meaning Of Reload Acceptance Persistence",
        "Future Persistence User Flow",
        "Storage-Location Policy",
        "File Format Boundary",
        "Write Preconditions",
        "Dry-Run/Write-Plan Model",
        "Acknowledgement Persistence Model",
        "Acknowledgement Expiry Policy",
        "Accepted-State Scope Persistence",
        "Provenance Persistence",
        "Schema/Migration Policy",
        "Redaction/Privacy Policy",
        "Candidate Lifecycle Persistence",
        "Stale-Source/Re-Preview Persistence",
        "Conflict/Shared-Stack Persistence",
        "Unsafe-Claim Persistence",
        "Evidence/History Persistence",
        "Diagnostics Vocabulary",
        "Non-Action Flags",
        "Disabled/Future Actions",
        "Relationship To Reload Acceptance View-Model",
        "Relationship To Reload Acceptance GUI And CLI",
        "Relationship To Reload File Reader And Explicit-Path Preview",
        "Relationship To State Writer",
        "Relationship To ProjectSchema",
        "Relationship To Live Optional Validation Issues",
        "Security/Privacy Review",
        "Future Implementation Test Plan",
        "Future Gates",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_required_persistence_vocabulary() -> None:
    text = _read(DOC)
    required = (
        "OptionalSolverPluginManifestReloadAcceptanceViewModel",
        "persistence_unavailable",
        "no_acceptance_viewmodel",
        "acceptance_not_requested",
        "persistence_not_requested",
        "persistence_requested",
        "acknowledgement_required",
        "persistence_blocked",
        "stale_source_repreview_required",
        "conflict_review_required",
        "unsafe_claim_blocked",
        "persistence_ready_future_only",
        "persisted_review_record_future_only",
        "runtime_acceptance_still_required",
        "future_activation_review_required",
        "future_discovery_refresh_required",
        "persistence_error",
        "explicit user-selected path",
        "no default write path",
        "no background write",
        "no hidden persistence",
        "dry-run write plan",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_NOT_REQUESTED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_WRITER_FUTURE_ONLY",
        "persist_acceptance_record",
        "write_acceptance_state",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_acknowledgements_expiry_and_non_meaning() -> None:
    text = _read(DOC)
    required = (
        "acceptance_not_validation",
        "acceptance_not_validation_failure",
        "acceptance_not_trust_restoration",
        "acceptance_not_automatic_activation",
        "acceptance_not_discovery_success",
        "acceptance_not_dependency_install",
        "acceptance_no_solver_execution",
        "acceptance_not_issue_closure",
        "acceptance_not_release_mutation",
        "acceptance_not_certification",
        "acceptance_not_persistence_write",
        "acceptance_not_project_schema_mutation",
        "redaction_reviewed",
        "unredacted_paths_blocked",
        "stale_source_requires_repreview",
        "untrusted_source_remains_untrusted",
        "activation_review_required_after_acceptance",
        "no_discovery_execution",
        "no_plugin_package_import",
        "no_validation_execution",
        "no_solver_execution",
        "trust_label_not_certification",
        "persisted_acknowledgements_may_expire",
        "source fingerprint change",
        "persistence schema change",
        "persistence storage-policy change",
        "persistence is not runtime reload acceptance",
        "persistence is not validation success",
        "persistence is not validation failure",
        "persistence is not trust restoration",
        "persistence is not automatic activation",
        "persistence is not discovery success",
        "persistence is not dependency installation",
        "persistence is not solver execution",
        "persistence is not ProjectSchema mutation",
        "persistence is not issue closure",
        "persistence is not release mutation",
        "persistence is not certification",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_non_action_flags_and_disabled_actions() -> None:
    text = _read(DOC)
    required = (
        "runtime_reload_acceptance_performed",
        "persistence_write_performed",
        "project_schema_mutated",
        "default_reload_path_used",
        "background_reload_performed",
        "directory_scan_performed",
        "network_fetch_performed",
        "plugin_package_imported",
        "cli_subprocess_used",
        "gui_subprocess_used",
        "reloadable_bundle_created",
        "export_file_created",
        "report_file_created",
        "clipboard_used",
        "report_attached",
        "output_folder_opened",
        "live_discovery_executed",
        "passive_refresh_executed",
        "validation_executed",
        "solver_executed",
        "dependency_installed",
        "dependency_uninstalled",
        "solver_uninstalled",
        "candidate_activated",
        "trust_restored",
        "issue_mutated",
        "release_mutated",
        "tag_mutated",
        "asset_mutated",
        "version_bumped",
        "validation_pass_claimed",
        "validation_fail_claimed",
        "issue_closure_claimed",
        "bundled_solver_claimed",
        "certification_claimed",
        "accept_as_trusted",
        "activate_reloaded_candidate",
        "refresh_discovery",
        "validate_solver",
        "execute_solver",
        "mutate_project_schema",
        "create_export_summary",
        "create_report_file",
        "create_reloadable_bundle",
        "close_issue",
        "mutate_release",
        "push_tag",
        "upload_asset",
        "claim_validation_success",
        "claim_validation_failure",
        "claim_certification",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_meta_docs_record_adr_guardrails_risk_checklist_and_validation() -> None:
    decision_log = _read(DECISION_LOG)
    guardrails = _read(GUARDRAILS)
    risk_register = _read(RISK_REGISTER)
    validation_matrix = _read(VALIDATION_MATRIX)
    release_checklist = _read(RELEASE_CHECKLIST)
    changelog = _read(CHANGELOG)

    _assert_any(decision_log, "ADR-0158")
    _assert_any(
        decision_log,
        "Optional Solver Plugin Manifest Reload Acceptance Persistence Remains "
        "Explicit and Non-Authoritative",
    )
    _assert_any(guardrails, "reload acceptance persistence design")
    _assert_any(guardrails, "persistence implementation")
    _assert_any(risk_register, "Reload acceptance persistence design")
    _assert_any(risk_register, "permission to write accepted runtime state")
    _assert_any(validation_matrix, "reload acceptance persistence design")
    _assert_any(validation_matrix, "docs/test design evidence only")
    _assert_any(release_checklist, "reload acceptance persistence")
    _assert_any(release_checklist, "does not implement reload acceptance persistence")
    _assert_any(changelog, "Optional Solver Plugin Manifest Reload Acceptance Persistence Design")
