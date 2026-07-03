from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_"
    "projectschema_boundary_design.md"
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


def _assert_all(text: str, phrases: tuple[str, ...]) -> None:
    for phrase in phrases:
        _assert_any(text, phrase)


def test_design_doc_exists_and_records_required_non_actions() -> None:
    assert DOC.exists()
    text = _read(DOC)
    required = (
        "design-only",
        "no ProjectSchema implementation",
        "no ProjectSchema mutation",
        "no ProjectSchema migration",
        "no ProjectSchema validation evidence",
        "no writer invocation",
        "no file parsing",
        "no reload file-reader invocation",
        "no CLI behavior",
        "no GUI behavior",
        "no subprocess",
        "no runtime reload acceptance",
        "no active acceptance mutation",
        "no background write",
        "no directory scan",
        "no network fetch",
        "no plugin package import",
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
        "no release mutation",
        "no tag mutation",
        "no asset mutation",
        "no version bump",
        "no validation-pass claim",
        "no validation-fail claim",
        "no issue-closure claim",
        "no certification claim",
    )
    _assert_all(text, required)
    _assert_any(text, "no ProjectSchema source edits", "no ProjectSchema source edit")
    _assert_any(text, "no ProjectSchema test edits", "no ProjectSchema test edit")
    _assert_any(text, "no ProjectSchema fields", "no ProjectSchema field")
    _assert_any(text, "no source edits", "no source edit")
    _assert_any(text, "no CLI source edits", "no CLI source edit")
    _assert_any(text, "no GUI source edits", "no GUI source edit")
    _assert_any(text, "no file writes", "no file write")
    _assert_any(text, "no file reading", "no file read")
    _assert_any(text, "no input state file reading", "no input state-file reading")
    _assert_any(text, "no input state file parsing", "no input state-file parsing")
    _assert_any(text, "no OSW-EXP-102 state-writer invocation")
    _assert_any(text, "no default target path", "no default path")
    _assert_any(text, "no reloadable bundle creation", "no reloadable bundles")
    _assert_any(text, "no export file creation", "no export files")
    _assert_any(text, "no report file creation", "no report files")
    _assert_any(text, "no issue mutation", "no issue closure")
    _assert_any(text, "no bundled-solver claim", "no bundled solver claim")


def test_design_doc_defines_projectschema_boundary_contract() -> None:
    text = _read(DOC)
    required = (
        "ProjectSchema Non-Meaning",
        "Persistence Schema Vs ProjectSchema Schema",
        "Prohibited Automatic Flows",
        "Future Integration Preconditions",
        "Future Permitted Data Candidates",
        "ProjectSchema Mutation Blockers",
        "Validation Evidence Boundary",
        "Trust/Provenance Boundary",
        "Candidate Lifecycle Boundary",
        "Built-In/Shared-Stack Boundary",
        "Issue/Release/Certification Boundary",
        "Redaction/Privacy Boundary",
        "Diagnostics Vocabulary",
        "Non-Action Flags",
        "Disabled/Future Actions",
        "Security/Privacy Review",
        "Future Implementation Test Plan",
        "Future Gates",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_*",
    )
    _assert_all(text, required)


def test_design_doc_reserves_diagnostics_flags_and_disabled_actions() -> None:
    text = _read(DOC)
    required = (
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_UNAVAILABLE",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_SEPARATE_SCHEMA",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_IMPORT_BLOCKED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_MUTATION_BLOCKED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_VALIDATION_EVIDENCE_BLOCKED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_TRUST_RESTORATION_BLOCKED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ACTIVATION_BLOCKED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ISSUE_RELEASE_BLOCKED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_CERTIFICATION_BLOCKED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_PREPARED_MACHINE_REQUIRED",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_PROJECTSCHEMA_BOUNDARY_ERROR",
        "runtime_reload_acceptance_performed",
        "project_schema_mutated",
        "project_schema_field_added",
        "project_schema_migration_performed",
        "project_schema_validation_evidence_created",
        "default_reload_path_used",
        "background_reload_performed",
        "directory_scan_performed",
        "network_fetch_performed",
        "plugin_package_imported",
        "cli_subprocess_used",
        "gui_subprocess_used",
        "validation_pass_claimed",
        "validation_fail_claimed",
        "issue_closure_claimed",
        "bundled_solver_claimed",
        "certification_claimed",
        "import_persistence_record_to_project_schema",
        "import_summary_audit_to_project_schema",
        "mutate_project_schema",
        "migrate_project_schema",
        "create_project_validation_evidence",
        "accept_for_session_review",
        "accept_as_trusted",
        "activate_reloaded_candidate",
        "refresh_discovery",
        "validate_solver",
        "execute_solver",
        "install_dependency",
        "uninstall_dependency",
        "uninstall_solver",
        "create_export_summary",
        "create_report_file",
        "create_reloadable_bundle",
        "copy_to_clipboard",
        "attach_to_report",
        "open_output_folder",
        "close_issue",
        "mutate_release",
        "push_tag",
        "upload_asset",
        "claim_validation_success",
        "claim_validation_failure",
        "claim_certification",
    )
    _assert_all(text, required)


def test_design_doc_records_relationships_and_live_issue_boundary() -> None:
    text = _read(DOC)
    required = (
        "Relationship To OSW-EXP-136 Summary Audit",
        "Relationship To OSW-EXP-134 CLI Write And OSW-EXP-132 GUI Write",
        "Relationship To OSW-EXP-126 Writer",
        "Relationship To OSW-EXP-125 Persistence View-Model",
        "Relationship To Reload Acceptance GUI/CLI",
        "Relationship To Reload File Reader And Explicit-Path Preview",
        "Relationship To Live Optional Validation Issues",
        "Issues #6 through #11 remain open",
        "not ProjectSchema state",
        "not validation evidence",
        "not validation failure",
        "not runtime reload acceptance",
        "skipped-missing remains skipped-missing",
    )
    _assert_all(text, required)


def test_meta_docs_record_adr_guardrails_risk_checklist_and_validation() -> None:
    decision_log = _read(DECISION_LOG)
    guardrails = _read(GUARDRAILS)
    risk_register = _read(RISK_REGISTER)
    validation_matrix = _read(VALIDATION_MATRIX)
    release_checklist = _read(RELEASE_CHECKLIST)
    changelog = _read(CHANGELOG)

    _assert_any(decision_log, "ADR-0171")
    _assert_any(
        decision_log,
        "Reload Acceptance Persistence Must Not Mutate ProjectSchema",
    )
    _assert_any(guardrails, "reload acceptance persistence ProjectSchema boundary")
    _assert_any(guardrails, "ProjectSchema implementation")
    _assert_any(risk_register, "ProjectSchema boundary design overreach")
    _assert_any(risk_register, "ProjectSchema validation evidence")
    _assert_any(validation_matrix, "ProjectSchema boundary design")
    _assert_any(validation_matrix, "docs/test design evidence only")
    _assert_any(
        release_checklist,
        "ProjectSchema boundary remains design-only",
    )
    _assert_any(release_checklist, "does not implement ProjectSchema behavior")
    _assert_any(
        changelog,
        "Optional Solver Plugin Manifest Reload Acceptance Persistence "
        "ProjectSchema Boundary Design",
    )
