from __future__ import annotations

import importlib.util
import os

import pytest
from tests.gui.test_optional_solver_gui_discovery_refresh import (
    _manifests,
    _report,
    _stack,
    _view_model,
)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_cancelled_refresh_preserves_previous_summary_and_cards(app: object) -> None:
    from osw.experimental.optional_solvers import (
        OptionalSolverRefreshResult,
        OptionalSolverRefreshState,
    )
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    def runner(request):
        return OptionalSolverRefreshResult(
            request_id=request.request_id,
            state=OptionalSolverRefreshState.CANCELED,
            generated_at="2026-06-25T00:00:00Z",
            source="cancel-test",
        )

    panel = OptionalSolverHealthPanel(
        _view_model(),
        refresh_runner=runner,
        refresh_manifests=_manifests(),
    )
    before_summary = panel.current_summary_text()
    before_cards = panel.current_stack_card_texts()

    panel.trigger_refresh_for_test()

    assert panel.current_summary_text() == before_summary
    assert panel.current_stack_card_texts() == before_cards
    assert "canceled" in panel.refresh_status_text().lower()
    assert panel.refresh_error_text() == ""
    assert "applied=False" in panel.refresh_result_summary_text()


def test_stale_refresh_result_is_ignored(app: object) -> None:
    from osw.experimental.optional_solvers import OptionalSolverRefreshResult
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    def runner(_request):
        return OptionalSolverRefreshResult(
            request_id="older-request",
            discovery_reports=_report(
                _stack("alpha", "discovered", 6),
                _stack("beta", "discovered", 7),
            ),
            generated_at="2026-06-25T00:00:00Z",
            source="stale-test",
        )

    panel = OptionalSolverHealthPanel(
        _view_model(),
        refresh_runner=runner,
        refresh_manifests=_manifests(),
    )
    before_summary = panel.current_summary_text()

    panel.trigger_refresh_for_test()

    assert panel.current_summary_text() == before_summary
    assert "stale" in panel.refresh_status_text().lower()
    assert "ignored=True" in panel.refresh_result_summary_text()


def test_disabled_refresh_without_any_runner_shows_reason(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(
        _view_model(),
        allow_default_refresh_runner=False,
    )

    assert panel.refresh_action_enabled() is False
    assert "default built-in passive discovery runner is disabled" in panel.refresh_action_reason()
    panel.trigger_refresh_for_test()
    assert "unavailable" in panel.refresh_status_text().lower()
    assert "runner is not configured" in panel.refresh_error_text()
