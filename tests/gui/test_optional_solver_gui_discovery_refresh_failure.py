from __future__ import annotations

import importlib.util
import os

import pytest
from tests.gui.test_optional_solver_gui_discovery_refresh import _manifests, _view_model

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


def test_failed_refresh_preserves_previous_view_model(app: object) -> None:
    from osw.experimental.optional_solvers import (
        OptionalSolverRefreshResult,
        OptionalSolverRefreshState,
    )
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    def runner(request):
        return OptionalSolverRefreshResult(
            request_id=request.request_id,
            state=OptionalSolverRefreshState.FAILED,
            generated_at="2026-06-25T00:00:00Z",
            source="failure-test",
            error_text="Injected passive refresh failure.",
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
    assert "failed" in panel.refresh_status_text().lower()
    assert "Injected passive refresh failure." in panel.refresh_error_text()
    assert "applied=False" in panel.refresh_result_summary_text()


def test_runner_exception_is_reported_without_replacing_view_model(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    def runner(_request):
        raise RuntimeError("boom")

    panel = OptionalSolverHealthPanel(
        _view_model(),
        refresh_runner=runner,
        refresh_manifests=_manifests(),
    )
    before_summary = panel.current_summary_text()

    panel.trigger_refresh_for_test()

    assert panel.current_summary_text() == before_summary
    assert "failed" in panel.refresh_status_text().lower()
    assert "RuntimeError: boom" in panel.refresh_error_text()
    assert panel.refresh_runner_call_count() == 1
