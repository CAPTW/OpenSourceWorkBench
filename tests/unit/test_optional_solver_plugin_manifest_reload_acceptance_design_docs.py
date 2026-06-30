from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_acceptance_design.md"
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
    checks = (
        "design-only",
        "no reload acceptance implementation",
        "no runtime source edits",
        "no GUI source edits",
        "no CLI source edits",
        "no file-reader source edits",
        "no reload view-model source edits",
        "no acceptance buttons",
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
    for phrase in checks:
        _assert_any(text, phrase)


def test_design_doc_defines_acceptance_semantics_and_safety_boundaries() -> None:
    text = _read(DOC)
    required = (
        "Definition Of Reload Acceptance",
        "Non-Meaning Of Reload Acceptance",
        "Future Acceptance Preconditions",
        "Future Acceptance Blockers",
        "Future User Flow",
        "Acknowledgement Model",
        "Acknowledgement Expiry Policy",
        "Accepted-State Scope Model",
        "Reader And Preview Provenance",
        "Schema/Migration Policy",
        "Redaction/Privacy Policy",
        "Candidate Lifecycle Policy",
        "Stale-Source/Re-Preview Policy",
        "Conflict/Shared-Stack Policy",
        "Unsafe-Claim Policy",
        "Evidence/History Policy",
        "Action-State Policy",
        "GUI Acceptance Design Relationship",
        "CLI Acceptance Design Relationship",
        "Persistence/State Writer Relationship",
        "ProjectSchema Relationship",
        "Live Optional Validation Issues Relationship",
        "Diagnostics Reserved",
        "Security And Privacy Review",
        "Future Implementation Test Plan",
        "Future Gates",
        "explicit user/caller action",
        "reviewed, safe, redacted, non-trusted UX state",
        "bounded in-memory/session review state",
        "OSPMG_RELOAD_ACCEPTANCE_*",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_acceptance_non_meanings() -> None:
    text = _read(DOC)
    required = (
        "Reload acceptance is not validation success",
        "Reload acceptance is not validation failure",
        "Reload acceptance is not trust restoration",
        "Reload acceptance is not automatic activation",
        "Reload acceptance is not discovery success",
        "Reload acceptance is not dependency installation",
        "Reload acceptance is not solver execution",
        "Reload acceptance is not ProjectSchema mutation",
        "Reload acceptance is not issue closure",
        "Reload acceptance is not release mutation",
        "Reload acceptance is not certification",
        "Reload acceptance is not report generation",
        "Reload acceptance is not reloadable bundle creation",
        "Reload acceptance is not persistence write",
        "User/plugin files remain untrusted by default",
        "Built-ins remain authoritative by default",
        "Skipped-missing remains skipped-missing",
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

    _assert_any(decision_log, "ADR-0152")
    _assert_any(decision_log, "Optional Solver Plugin Manifest Reload Acceptance")
    _assert_any(guardrails, "reload acceptance design")
    _assert_any(guardrails, "acceptance button implementation")
    _assert_any(risk_register, "reload acceptance design could be mistaken")
    _assert_any(risk_register, "trusted reload acceptance")
    _assert_any(validation_matrix, "reload acceptance design")
    _assert_any(validation_matrix, "docs/test design evidence only")
    _assert_any(release_checklist, "reload acceptance design")
    _assert_any(release_checklist, "does not implement reload acceptance")
