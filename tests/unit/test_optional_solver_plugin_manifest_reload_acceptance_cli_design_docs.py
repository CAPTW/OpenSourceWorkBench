from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_cli_design.md"
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
        "no reload acceptance CLI implementation",
        "no CLI source edits",
        "no GUI source edits",
        "no runtime source edits",
        "no file-reader source edits",
        "no reload view-model source edits",
        "no reload acceptance view-model source edits",
        "no acceptance CLI commands",
        "no acceptance flags",
        "no acceptance callbacks",
        "no persistence writes",
        "no ProjectSchema mutation",
        "no runtime reload acceptance",
        "no file IO",
        "no file reading",
        "no file parsing",
        "no reader invocation",
        "no GUI behavior",
        "no GUI subprocess use",
        "no CLI subprocess use",
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
        "no issue-closure claim",
        "no bundled-solver claim",
        "no certification claim",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_defines_cli_review_outputs_and_exit_policy() -> None:
    text = _read(DOC)
    required = (
        "Definition Of Reload Acceptance CLI Review",
        "Non-Meaning Of Reload Acceptance CLI Review",
        "Future Command Vocabulary",
        "Future CLI User Flow",
        "Input Policy",
        "Output Modes",
        "Summary And Readiness Output",
        "Preconditions And Blockers Output",
        "Acknowledgement Output",
        "Acknowledgement Expiry Output",
        "Accepted-State Scope Output",
        "Reader And Preview Provenance Output",
        "Schema And Migration Output",
        "Redaction And Privacy Output",
        "Candidate Lifecycle Output",
        "Stale-Source And Re-Preview Output",
        "Conflict And Shared-Stack Output",
        "Unsafe-Claim Output",
        "Evidence And History Output",
        "Diagnostics Output",
        "Non-Action Flags Output",
        "Disabled And Future Action Output",
        "Exit-Code Policy",
        "OSPMG_RELOAD_ACCEPTANCE_*",
        "OptionalSolverPluginManifestReloadAcceptanceViewModel",
        "stdout-first",
        "Text output",
        "JSON output",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_non_meaning_and_relationships() -> None:
    text = _read(DOC)
    required = (
        "CLI acceptance review is not reload acceptance implementation",
        "CLI acceptance review is not runtime reload acceptance",
        "CLI acceptance review is not validation success",
        "CLI acceptance review is not validation failure",
        "CLI acceptance review is not trust restoration",
        "CLI acceptance review is not automatic activation",
        "CLI acceptance review is not discovery success",
        "CLI acceptance review is not dependency installation",
        "CLI acceptance review is not solver execution",
        "CLI acceptance review is not ProjectSchema mutation",
        "CLI acceptance review is not persistence write",
        "CLI acceptance review is not file IO",
        "CLI acceptance review is not reader invocation",
        "CLI acceptance review is not GUI behavior",
        "CLI acceptance review is not GUI subprocess use",
        "CLI acceptance review is not issue closure",
        "CLI acceptance review is not release mutation",
        "Relationship To Reload Acceptance ViewModel",
        "Relationship To Reload Acceptance GUI Panel",
        "Relationship To Reload CLI Explicit-Path Preview",
        "Relationship To State Writer And Persistence",
        "Relationship To ProjectSchema",
        "Relationship To Live Optional Validation Issues",
        "Security And Privacy Review",
        "Future Implementation Test Plan",
        "Future Gates",
        "Issues `#6` through `#11` remain open",
        "OSW-EXP-123 may implement",
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

    _assert_any(decision_log, "ADR-0156")
    _assert_any(
        decision_log,
        "Optional Solver Plugin Manifest Reload Acceptance CLI Starts As "
        "Design-Only",
    )
    _assert_any(guardrails, "reload acceptance CLI design")
    _assert_any(guardrails, "acceptance flag implementation")
    _assert_any(risk_register, "reload acceptance CLI design could be mistaken")
    _assert_any(risk_register, "acceptance CLI commands")
    _assert_any(validation_matrix, "reload acceptance CLI design")
    _assert_any(validation_matrix, "docs/test design evidence only")
    _assert_any(release_checklist, "reload acceptance CLI design")
    _assert_any(release_checklist, "does not implement reload acceptance CLI")
    _assert_any(changelog, "Optional Solver Plugin Manifest Reload Acceptance CLI Design")
