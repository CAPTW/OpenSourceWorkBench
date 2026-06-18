from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "feaspec_human_review_gui_dialog_design.md"
)


def _read() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_doc_says_design_only() -> None:
    assert "design-only" in _normalized()


def test_doc_says_no_gui_implementation() -> None:
    assert "no gui implementation" in _normalized()


def test_doc_says_no_solver_execution() -> None:
    assert "no solver execution" in _normalized()


def test_doc_defines_dialog_entry_points() -> None:
    text = _normalized()

    assert "dialog entry points" in text
    assert "from feaspec file" in text
    assert "from no-run export preview" in text
    assert "from no-run export write summary" in text
    assert "from future project context" in text


def test_doc_defines_dialog_layout() -> None:
    text = _normalized()

    assert "dialog layout" in text
    assert "left navigation or tab model" in text


def test_doc_includes_source_evidence_panel() -> None:
    assert "source/evidence panel" in _normalized()


def test_doc_includes_diagnostics_panel() -> None:
    assert "diagnostics panel" in _normalized()


def test_doc_includes_export_preview_panel() -> None:
    assert "export preview panel" in _normalized()


def test_doc_includes_review_action_panel() -> None:
    assert "review action panel" in _normalized()


def test_doc_includes_safety_limitations_panel() -> None:
    assert "safety/limitations panel" in _normalized()


def test_doc_defines_warning_acceptance_ux() -> None:
    text = _normalized()

    assert "warning acceptance ux" in text
    assert "warning list" in text
    assert "explicit checkbox/action" in text
    assert "required reason" in text


def test_doc_says_blocker_diagnostics_cannot_be_accepted_away() -> None:
    assert "blocker diagnostics cannot be accepted away" in _normalized()


def test_doc_defines_approval_gating() -> None:
    text = _normalized()

    assert "approval gating" in text
    assert "no-run export approval requires no blockers/errors" in text
    assert "installed-only run request requires limitations/readme/run-gate acknowledgement" in text


def test_doc_requires_disabled_action_reasons() -> None:
    assert "action buttons disabled with visible reasons" in _normalized()


def test_doc_includes_record_preview() -> None:
    text = _normalized()

    assert "record preview" in text
    assert "json preview" in text
    assert "summary preview" in text
    assert "validation status" in text
    assert "save path preview" in text


def test_doc_defines_save_behavior() -> None:
    text = _normalized()

    assert "save behavior" in text
    assert "explicit save only" in text
    assert "overwrite confirmation" in text
    assert "no parent-dir creation unless future implementation explicitly chooses it" in text


def test_doc_requires_cli_gui_consistency() -> None:
    text = _normalized()

    assert "cli/gui consistency is required" in text
    assert "same review states" in text
    assert "same actions" in text
    assert "same diagnostic decision semantics" in text


def test_doc_keeps_issue_8_live_validation_separate() -> None:
    assert "issue `#8` live validation separate" in _normalized()


def test_doc_says_no_bundled_solver() -> None:
    assert "no bundled solver" in _normalized()


def test_doc_says_no_industrial_certification() -> None:
    text = _normalized()

    assert "no certification" in text
    assert "industrial certification" in text


def test_doc_proposes_future_view_model_only() -> None:
    text = _normalized()

    assert "future view-model only" in text
    assert "feaspechumanreviewdialogstate" in text
    assert "feaspechumanreviewdialogviewmodel" in text
    assert "feaspechumanreviewactionstate" in text
    assert "there is no implementation in this gate" in text


def test_doc_does_not_claim_gui_implementation_exists() -> None:
    text = _normalized()

    assert "no gui implementation" in text
    assert "gui implementation exists" not in text


def test_doc_does_not_claim_solver_execution_exists() -> None:
    text = _normalized()

    assert "no solver execution" in text
    assert "solver execution exists" not in text


def test_doc_does_not_claim_result_import_implementation_exists() -> None:
    text = _normalized()

    assert "no result import implementation" in text
    assert "result import implementation exists" not in text
