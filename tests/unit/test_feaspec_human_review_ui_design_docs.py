from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DOC = (
    REPO_ROOT / "docs" / "experimental" / "feaspec_human_review_ui_design.md"
)
RECORD_MODEL_DOC = (
    REPO_ROOT / "docs" / "experimental" / "feaspec_human_review_record_model.md"
)


def _read() -> str:
    return DESIGN_DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return " ".join(_read().lower().split())


def test_human_review_ui_design_doc_exists() -> None:
    assert DESIGN_DOC.exists()


def test_human_review_record_model_doc_exists() -> None:
    assert RECORD_MODEL_DOC.exists()


def test_design_scope_is_docs_only() -> None:
    text = _normalized()

    assert "design-only" in text


def test_explicit_no_gui_scope() -> None:
    text = _normalized()

    assert "no gui implementation" in text


def test_explicit_no_solver_execution_scope() -> None:
    text = _normalized()

    assert "no solver execution" in text


def test_gates_are_separate() -> None:
    text = _normalized()

    assert "review, export, run, and import are separate gates" in text


def test_review_workflow_defined() -> None:
    text = _normalized()

    assert "load feaspec candidate or approved spec" in text
    assert "inspect source data and evidence confidence" in text
    assert "inspect validator diagnostics" in text
    assert "inspect bridge diagnostics" in text
    assert "inspect case-plan diagnostics" in text
    assert "inspect no-run export preview output" in text
    assert "inspect" in text


def test_review_states_defined() -> None:
    text = _normalized()

    assert "review states" in text


def test_review_state_unreviewed() -> None:
    text = _normalized()

    assert "unreviewed" in text


def test_review_state_needs_changes() -> None:
    text = _normalized()

    assert "needs changes" in text


def test_review_state_rejected() -> None:
    text = _normalized()

    assert "rejected" in text


def test_review_state_approved_for_no_run_export() -> None:
    text = _normalized()

    assert "approved for no-run export" in text


def test_review_state_approved_for_installed_only_run_request() -> None:
    text = _normalized()

    assert "approved for installed-only run request" in text


def test_panel_layout_defined() -> None:
    text = _normalized()

    assert "source/evidence panel" in text
    assert "geometry graph summary panel" in text
    assert "materials/sections panel" in text
    assert "boundary/load panel" in text
    assert "diagnostics panel" in text
    assert "provenance and human-review panel" in text
    assert "export preview panel" in text
    assert "safety and limitations panel" in text


def test_required_review_record_fields_defined() -> None:
    text = _normalized()

    assert "reviewer identity" in text
    assert "timestamp" in text
    assert "action" in text
    assert "accepted warnings" in text
    assert "rejected diagnostics" in text
    assert "review notes" in text
    assert "source feaspec identifier" in text
    assert "validator report hash or summary" in text
    assert "bridge/case/export summary" in text


def test_review_record_model_evidence_is_linked() -> None:
    text = _normalized()

    assert "feaspec human review record model" in text
    assert "experimental data boundary" in text
    assert "the record model is not a gui implementation" in text


def test_approval_blockers_defined() -> None:
    text = _normalized()

    assert "approval blockers" in text
    assert "candidate spec not reviewed" in text
    assert "validator blockers" in text


def test_blocker_diagnostics_cannot_be_accepted() -> None:
    text = _normalized()

    assert "blocker diagnostics cannot be accepted away" in text


def test_warning_acceptance_is_explicit() -> None:
    text = _normalized()

    assert "warnings can be accepted only with explicit user action" in text
    assert "accepted warnings" in text
    assert "record a reason" in text


def test_cli_gui_consistency_required() -> None:
    text = _normalized()

    assert (
        "cli preview/write and gui workflows must present matching states and "
        "diagnostics"
    ) in text


def test_issue_8_open_until_run_validation() -> None:
    text = _normalized()

    assert "issue `#8` remains open until installed-only validation passes" in text


def test_no_hidden_solver_install() -> None:
    text = _normalized()

    assert "no hidden solver installation" in text


def test_no_industrial_certification_claim() -> None:
    text = _normalized()

    assert "no certification" in text
    assert "no certification claim" in text


def test_no_bundled_external_solvers() -> None:
    text = _normalized()

    assert "no bundled external solver claims" in text


def test_doc_does_not_claim_gui_exists() -> None:
    text = _normalized()

    assert "no gui implementation" in text


def test_doc_does_not_claim_solver_execution_exists() -> None:
    text = _normalized()

    assert "no solver execution" in text
    assert "no solver execution is tied to" in text


def test_doc_does_not_claim_result_import_implemented() -> None:
    text = _normalized()

    assert "no result import implementation" in text
