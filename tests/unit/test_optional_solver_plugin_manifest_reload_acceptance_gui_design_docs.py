from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_gui_design.md"
)
DECISION_LOG = REPO_ROOT / "docs" / "07_decision_log.md"
GUARDRAILS = REPO_ROOT / "docs" / "08_scope_guardrails.md"
RISK_REGISTER = REPO_ROOT / "docs" / "09_risk_register.md"
VALIDATION_MATRIX = REPO_ROOT / "docs" / "04_validation_matrix.md"
RELEASE_CHECKLIST = REPO_ROOT / "docs" / "10_release_checklist.md"


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
        "no reload acceptance GUI implementation",
        "no GUI source edits",
        "no runtime source edits",
        "no CLI source edits",
        "no file-reader source edits",
        "no reload view-model source edits",
        "no reload acceptance view-model source edits",
        "no acceptance buttons",
        "no acceptance callbacks",
        "no acceptance CLI commands",
        "no persistence writes",
        "no ProjectSchema mutation",
        "no runtime reload acceptance",
        "no default reload path",
        "no background reload",
        "no directory scan",
        "no network fetch",
        "no plugin package import",
        "no CLI subprocess use",
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


def test_design_doc_defines_gui_review_semantics_and_displays() -> None:
    text = _read(DOC)
    required = (
        "Definition Of Reload Acceptance GUI Review",
        "Non-Meaning Of Reload Acceptance GUI Review",
        "Future GUI User Flow",
        "Input Policy",
        "Layout Model",
        "Summary And Readiness Display",
        "Preconditions And Blockers Display",
        "Acknowledgement Display",
        "Acknowledgement Expiry Display",
        "Accepted-State Scope Display",
        "Reader And Preview Provenance Display",
        "Schema And Migration Display",
        "Redaction And Privacy Display",
        "Candidate Lifecycle Display",
        "Stale-Source And Re-Preview Display",
        "Conflict And Shared-Stack Display",
        "Unsafe-Claim Display",
        "Evidence And History Display",
        "Diagnostics Display",
        "Non-Action Flags Display",
        "Disabled And Future Action Display",
        "OSPMG_RELOAD_ACCEPTANCE_*",
        "OptionalSolverPluginManifestReloadAcceptanceViewModel",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_non_meaning_and_relationships() -> None:
    text = _read(DOC)
    required = (
        "GUI acceptance review is not reload acceptance implementation",
        "GUI acceptance review is not runtime reload acceptance",
        "GUI acceptance review is not validation success",
        "GUI acceptance review is not validation failure",
        "GUI acceptance review is not trust restoration",
        "GUI acceptance review is not automatic activation",
        "GUI acceptance review is not discovery success",
        "GUI acceptance review is not dependency installation",
        "GUI acceptance review is not solver execution",
        "GUI acceptance review is not ProjectSchema mutation",
        "GUI acceptance review is not persistence write",
        "GUI acceptance review is not issue closure",
        "GUI acceptance review is not release mutation",
        "GUI acceptance review is not report generation",
        "GUI acceptance review is not reloadable bundle creation",
        "Relationship To Reload Acceptance ViewModel",
        "Relationship To Reload GUI File-Dialog Preview",
        "Relationship To Reload Panel",
        "Relationship To Reload CLI",
        "Relationship To State Writer And Persistence",
        "Relationship To ProjectSchema",
        "Relationship To Live Optional Validation Issues",
        "Security And Privacy Review",
        "Future Implementation Test Plan",
        "Future Gates",
        "Issues `#6` through `#11` remain open",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_meta_docs_record_adr_guardrails_risk_checklist_and_validation() -> None:
    decision_log = _read(DECISION_LOG)
    guardrails = _read(GUARDRAILS)
    risk_register = _read(RISK_REGISTER)
    validation_matrix = _read(VALIDATION_MATRIX)
    release_checklist = _read(RELEASE_CHECKLIST)

    _assert_any(decision_log, "ADR-0154")
    _assert_any(
        decision_log,
        "Optional Solver Plugin Manifest Reload Acceptance GUI Starts As Design-Only",
    )
    _assert_any(guardrails, "reload acceptance GUI design")
    _assert_any(guardrails, "acceptance callback implementation")
    _assert_any(risk_register, "reload acceptance GUI design could be mistaken")
    _assert_any(risk_register, "GUI acceptance buttons")
    _assert_any(validation_matrix, "reload acceptance GUI design")
    _assert_any(validation_matrix, "docs/test design evidence only")
    _assert_any(release_checklist, "reload acceptance GUI design")
    _assert_any(release_checklist, "does not implement reload acceptance GUI")
