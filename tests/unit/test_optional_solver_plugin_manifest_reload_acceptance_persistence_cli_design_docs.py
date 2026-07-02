from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_persistence_cli_design.md"
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
        "no CLI implementation",
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
        "no default reload path",
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


def test_design_doc_defines_future_cli_contract() -> None:
    text = _read(DOC)
    required = (
        "Future Command Vocabulary",
        "State Source Policy",
        "Explicit Target Path Policy",
        "Output Modes",
        "Dry-Run/Write-Plan Output",
        "Actual Write Future Gate",
        "Request/Result Rendering",
        "Acknowledgement Rendering",
        "Acknowledgement Expiry Rendering",
        "Schema/Migration Rendering",
        "Redaction/Privacy Rendering",
        "Provenance Rendering",
        "Candidate Lifecycle Rendering",
        "Stale-Source/Re-Preview Rendering",
        "Conflict/Shared-Stack Rendering",
        "Unsafe-Claim Rendering",
        "Evidence/History Rendering",
        "Diagnostics Vocabulary",
        "Exit-Code Policy",
        "Non-Action Flags",
        "Disabled/Future Actions",
        "Security/Privacy Review",
        "Future Implementation Test Plan",
        "Future Gates",
        "OptionalSolverPluginManifestReloadAcceptancePersistenceViewModel",
        "OSPMG_RELOAD_ACCEPTANCE_PERSISTENCE_CLI_*",
        "exit code `0` is command completion only",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_required_safety_vocabulary() -> None:
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
        "persisted_acknowledgements_may_expire",
        "source fingerprint change",
        "persistence schema change",
        "persistence storage-policy change",
        "runtime_reload_acceptance_performed",
        "persistence_write_performed",
        "project_schema_mutated",
        "input_state_file_read",
        "input_state_file_parsed",
        "reload_file_reader_invoked",
        "state_writer_invoked",
        "validation_pass_claimed",
        "validation_fail_claimed",
        "issue_closure_claimed",
        "certification_claimed",
        "write_acceptance_review_record",
        "persist_acceptance_record",
        "mutate_project_schema",
        "claim_validation_success",
        "claim_validation_failure",
        "claim_certification",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_relationships() -> None:
    text = _read(DOC)
    required = (
        "Relationship To OSW-EXP-126 Writer",
        "Relationship To OSW-EXP-125 Persistence View-Model",
        "Relationship To Reload Acceptance CLI/GUI",
        "Relationship To Reload File Reader And Explicit-Path Preview",
        "Relationship To State Writer/Persistence",
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

    _assert_any(decision_log, "ADR-0161")
    _assert_any(
        decision_log,
        "Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Starts As Design-Only",
    )
    _assert_any(guardrails, "reload acceptance persistence CLI design")
    _assert_any(guardrails, "writer invocation")
    _assert_any(risk_register, "reload acceptance persistence CLI design")
    _assert_any(risk_register, "actual persistence write")
    _assert_any(validation_matrix, "reload acceptance persistence CLI design")
    _assert_any(validation_matrix, "docs/test design evidence only")
    _assert_any(release_checklist, "reload acceptance persistence CLI remains design-only")
    _assert_any(release_checklist, "does not implement persistence CLI behavior")
    _assert_any(
        changelog,
        "Optional Solver Plugin Manifest Reload Acceptance Persistence CLI Design",
    )
