from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = REPO_ROOT / "docs" / "experimental" / (
    "optional_solver_plugin_manifest_reload_gui_file_dialog_design.md"
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
        "no GUI file-dialog implementation",
        "no GUI source edits",
        "no CLI source edits",
        "no runtime source edits",
        "no file-reader source edits",
        "no reload view-model source edits",
        "no file dialog widgets",
        "no file opening behavior",
        "no runtime file reading",
        "no runtime state parsing",
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
        "no ProjectSchema mutation",
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
    for phrase in checks:
        _assert_any(text, phrase)


def test_design_doc_defines_required_gui_file_dialog_sections() -> None:
    text = _read(DOC)
    required = (
        "Definition Of GUI File-Dialog Reload Preview",
        "Non-Meaning Of GUI File-Dialog Preview",
        "Future User Flow",
        "File-Dialog Option Policy",
        "Reader Invocation Policy",
        "GUI Layout Model",
        "Reader Diagnostics Display",
        "Reload View-Model Display After Reader Success",
        "Schema/Migration Display",
        "Redaction/Privacy Display",
        "Acknowledgement/Expiry Display",
        "Candidate Lifecycle Display",
        "Stale-Source/Re-Preview Display",
        "Conflict/Shared-Stack Display",
        "Unsafe-Claim Display",
        "Evidence/History Display",
        "Action-State Display",
        "Dialog Cancellation And Error Policy",
        "Relationship To Reload File Reader",
        "Relationship To Reload View-Model",
        "Relationship To Existing Reload Panel",
        "Relationship To Reload CLI",
        "Relationship To State Writer",
        "Relationship To ProjectSchema",
        "Relationship To Live Optional Validation Issues",
        "Security And Privacy Review",
        "Future Implementation Test Plan",
        "Future Gates",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_design_doc_records_review_only_reader_and_panel_boundaries() -> None:
    text = _read(DOC)
    required = (
        "explicit user action",
        "selects one local state file",
        "invokes the OSW-EXP-113 library reader",
        "displays reader diagnostics",
        "only if the reader returns a safe mapping",
        "displays reload view-model review",
        "OptionalSolverPluginManifestReloadPanel",
        "pure view-model rendering",
        "reader diagnostics render before view-model preview",
        "reader blockers suppress view-model construction",
        "route only reader `safe_mapping` output into the reload view-model",
        "Issues `#6` through `#11` remain open",
        "User/plugin files remain untrusted by default",
        "Built-ins remain authoritative by default",
        "Skipped-missing remains skipped-missing",
    )
    for phrase in required:
        _assert_any(text, phrase)


def test_meta_docs_record_adr_guardrails_risk_checklist_and_validation() -> None:
    decision_log = _read(DECISION_LOG)
    guardrails = _read(GUARDRAILS)
    risk_register = _read(RISK_REGISTER)
    validation_matrix = _read(VALIDATION_MATRIX)
    release_checklist = _read(RELEASE_CHECKLIST)

    _assert_any(decision_log, "ADR-0150")
    _assert_any(decision_log, "Optional Solver Plugin Manifest Reload GUI File Dialog")
    _assert_any(guardrails, "reload GUI file-dialog design")
    _assert_any(guardrails, "GUI file-dialog implementation")
    _assert_any(risk_register, "reload GUI file-dialog design could be mistaken")
    _assert_any(validation_matrix, "reload GUI file-dialog design")
    _assert_any(validation_matrix, "docs/test design evidence only")
    _assert_any(release_checklist, "reload GUI file dialog design")
    _assert_any(release_checklist, "does not implement GUI file-dialog behavior")
