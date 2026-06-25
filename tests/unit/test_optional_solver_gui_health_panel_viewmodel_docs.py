from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_health_panel_viewmodel.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def test_optional_solver_gui_health_panel_viewmodel_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_boundaries() -> None:
    text = _normalized()

    assert "experimental pure view-model implemented" in text
    assert "no pyside implementation" in text
    assert "no qt implementation" in text
    assert "no discovery execution" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_lists_public_api_and_inputs_outputs() -> None:
    text = _read()

    for name in (
        "OptionalSolverHealthPanelViewModel",
        "OptionalSolverHealthSummaryViewModel",
        "OptionalSolverStackCardViewModel",
        "OptionalSolverStackDetailsViewModel",
        "OptionalSolverDiagnosticRowViewModel",
        "OptionalSolverRequirementRowViewModel",
        "OptionalSolverGuidanceRowViewModel",
        "OptionalSolverValidationHistoryRowViewModel",
        "OptionalSolverHealthPanelAction",
        "OptionalSolverHealthPanelActionState",
        "build_optional_solver_health_panel_viewmodel",
        "build_optional_solver_stack_card_viewmodel",
        "summarize_optional_solver_health_panel",
        "explain_optional_solver_health_panel",
    ):
        assert name in text
    assert "built-in or supplied `OptionalSolverManifest` records" in text
    assert "supplied passive `OptionalSolverDiscoveryReport`" in text
    assert "the builder does not run discovery" in text


def test_doc_defines_summary_cards_details_diagnostics_and_guidance() -> None:
    text = _normalized()

    for phrase in (
        "summary model",
        "counts by health state",
        "stack cards",
        "sorted deterministically by stack id",
        "details panel model",
        "version/help probe text marked as not executed",
        "diagnostics rows",
        "guidance rows",
        "no-bundled-solver notice",
        "validation-gate guidance",
        "issue closure guidance",
    ):
        assert phrase in text


def test_doc_defines_action_privacy_safety_and_cli_relationship() -> None:
    text = _normalized()

    assert "action-state model" in text
    assert "install solver: unavailable" in text
    assert "close issue: unavailable" in text
    assert "no clipboard access" in text
    assert "paths already redacted by discovery remain redacted" in text
    assert "environment values are never displayed" in text
    assert "no subprocess usage" in text
    assert "no optional package imports" in text
    assert "same health-state semantics" in text
    assert "gui-friendly rendering data" in text


def test_doc_lists_future_gates() -> None:
    text = _read()

    assert "OSW-EXP-062_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_IMPLEMENTATION" in text
    assert "OSW-EXP-063_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_DESIGN" in text
    assert "OSW-VALID" in text


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "pyside gui exists",
        "gui implementation exists",
        "active smoke validation exists",
        "install command exists",
        "solvers are installed",
        "solvers are bundled",
        "external solvers are bundled",
        "validation passed",
        "#6 through #11 passed",
        "#8 can close",
        "issues can close",
        "issue closure readiness",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
