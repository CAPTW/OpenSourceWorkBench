from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_cli_write_design.md"
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
        "no CLI write implementation",
        "no CLI source edits",
        "no source edits",
        "no writer invocation",
        "no file writes",
        "no file reading",
        "no file parsing",
        "no input state file reading",
        "no input state file parsing",
        "no reload file-reader invocation",
        "no OSW-EXP-102 state-writer invocation",
        "no GUI behavior",
        "no GUI subprocess",
        "no runtime reload acceptance",
        "no active acceptance mutation",
        "no ProjectSchema mutation",
        "no default target path",
        "no background write",
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
        "no issue-closure claim",
        "no bundled-solver claim",
        "no certification claim",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_defines_future_cli_write_contract() -> None:
    text = _read(DOC)
    required = (
        "Future CLI Write Workflow Definition",
        "Future CLI Command Vocabulary",
        "Future CLI User Flow",
        "Input Policy",
        "Target Policy",
        "Dry-Run Policy",
        "Write Preconditions",
        "Write Confirmation Policy",
        "Replacement Policy",
        "Writer Invocation Boundary",
        "Writer Result Output",
        "Acknowledgement Output",
        "Expiry / Invalidation Policy",
        "Schema/Migration Policy",
        "Redaction/Privacy Policy",
        "Provenance Output",
        "Candidate Lifecycle Output",
        "Stale-Source/Re-Preview Output",
        "Conflict/Shared-Stack Output",
        "Unsafe-Claim Output",
        "Evidence/History Output",
        "Diagnostics Vocabulary",
        "Exit-Code Policy",
        "Non-Action Flags",
        "Disabled/Future Actions",
        "Security/Privacy Review",
        "Future Implementation Test Plan",
        "Future Gates",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_WRITE_*",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_acknowledgements_expiry_flags_and_actions() -> None:
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
        "persistence CLI policy change",
        "persistence GUI policy change",
        "writer policy change",
        "CLI write policy change",
        "dry-run payload hash change",
        "runtime_reload_acceptance_performed",
        "project_schema_mutated",
        "input_state_file_read",
        "input_state_file_parsed",
        "cli_subprocess_used",
        "gui_subprocess_used",
        "validation_pass_claimed",
        "validation_fail_claimed",
        "issue_closure_claimed",
        "bundled_solver_claimed",
        "certification_claimed",
        "request_dry_run_plan",
        "write_persistence_record",
        "persist_acceptance_record",
        "write_acceptance_state",
        "mutate_project_schema",
        "claim_validation_success",
        "claim_validation_failure",
        "claim_certification",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_relationships_and_live_issue_boundary() -> None:
    text = _read(DOC)
    required = (
        "Relationship To OSW-EXP-128 CLI",
        "Relationship To OSW-EXP-132 GUI Write Panel",
        "Relationship To OSW-EXP-126 Writer",
        "Relationship To OSW-EXP-125 Persistence View-Model",
        "Relationship To Reload Acceptance GUI/CLI",
        "Relationship To Reload File Reader And Explicit-Path Preview",
        "Relationship To ProjectSchema",
        "Relationship To Live Optional Validation Issues",
        "Issues `#6` through `#11` remain open",
        "not validation success",
        "not validation failure",
        "not runtime acceptance",
        "not ProjectSchema mutation",
        "not issue closure",
        "not release mutation",
        "not certification",
        "skipped-missing remains skipped-missing",
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

    _assert_any(decision_log, "ADR-0167")
    _assert_any(
        decision_log,
        "Optional Solver Plugin Manifest Reload Acceptance Persistence CLI "
        "Write Is Explicit, Dry-Run-First, And Non-Authoritative",
    )
    _assert_any(guardrails, "reload acceptance persistence CLI write design")
    _assert_any(guardrails, "CLI write implementation")
    _assert_any(risk_register, "reload acceptance persistence CLI write design")
    _assert_any(risk_register, "authorization to expose actual CLI writes")
    _assert_any(validation_matrix, "reload acceptance persistence CLI write design")
    _assert_any(validation_matrix, "docs/test design evidence only")
    _assert_any(
        release_checklist,
        "reload acceptance persistence CLI write remains design-only",
    )
    _assert_any(release_checklist, "does not implement CLI write behavior")
    _assert_any(
        changelog,
        "Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Write Design",
    )
