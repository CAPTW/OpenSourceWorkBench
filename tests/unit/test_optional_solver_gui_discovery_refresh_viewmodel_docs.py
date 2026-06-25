from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOC = (
    REPO_ROOT
    / "docs"
    / "experimental"
    / "optional_solver_gui_discovery_refresh_viewmodel.md"
)


def _read() -> str:
    return DOC.read_text(encoding="utf-8")


def _normalized() -> str:
    return _read().lower()


def _squashed() -> str:
    return " ".join(_normalized().split())


def test_optional_solver_gui_discovery_refresh_viewmodel_doc_exists() -> None:
    assert DOC.exists()


def test_doc_records_status_and_boundaries() -> None:
    text = _normalized()

    assert "experimental pure refresh view-model implemented" in text
    assert "no gui wiring" in text
    assert "no background worker" in text
    assert "no discovery execution" in text
    assert "no solver execution" in text
    assert "no dependency installation" in text


def test_doc_lists_public_api_and_states() -> None:
    raw = _read()
    text = raw.lower()

    for name in (
        "OptionalSolverRefreshState",
        "OptionalSolverRefreshAction",
        "OptionalSolverRefreshActionState",
        "OptionalSolverRefreshRequest",
        "OptionalSolverRefreshResult",
        "OptionalSolverRefreshStatusViewModel",
        "OptionalSolverRefreshPlan",
        "OptionalSolverRefreshApplyResult",
        "OptionalSolverRefreshDiagnostic",
        "build_optional_solver_refresh_plan",
        "build_optional_solver_refresh_status_viewmodel",
        "apply_optional_solver_refresh_success",
        "apply_optional_solver_refresh_failure",
        "apply_optional_solver_refresh_canceled",
        "ignore_optional_solver_stale_refresh_result",
        "explain_optional_solver_refresh",
    ):
        assert name in raw
    for state in (
        "idle",
        "pending",
        "running",
        "completed",
        "failed",
        "canceled",
        "stale_ignored",
    ):
        assert state in text


def test_doc_defines_apply_swap_selection_and_status_behavior() -> None:
    text = _normalized()
    squashed = _squashed()

    assert "success builds a new `optionalsolverhealthpanelviewmodel`" in text
    assert "failure preserves the previous health panel view-model" in text
    assert "cancel preserves the previous health panel view-model" in text
    assert "stale results are ignored" in text
    assert "does not mutate cards or details in place" in squashed
    assert "swap the accepted view-model atomically" in text
    assert "selected stack id" in text
    assert "filter text" in text
    assert "health-state filters" in text
    assert "status text" in text
    assert "error text" in text


def test_doc_records_safety_and_export_relationship() -> None:
    text = _normalized()
    squashed = _squashed()

    assert "no subprocess" in text
    assert "no install action" in text
    assert "no issue closure action" in text
    assert "export after refresh uses the applied view-model" in text
    assert "exported summaries remain not validation evidence" in text
    assert "issues `#6` through `#11` remain open" in text
    assert "skipped-missing remains not pass evidence" in squashed


def test_doc_lists_future_gates() -> None:
    raw = _read()

    assert "OSW-EXP-068_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_IMPLEMENTATION" in raw
    assert "OSW-VALID" in raw


def test_doc_does_not_claim_forbidden_outcomes() -> None:
    text = _normalized()

    for phrase in (
        "gui refresh is wired",
        "background worker exists",
        "active smoke validation exists",
        "install command exists",
        "solvers are installed",
        "validation passed",
        "#6 through #11 passed",
        "issues can close",
        "issue closure readiness",
        "solvers are bundled",
        "industrial certification",
        "certified for production",
    ):
        assert phrase not in text
