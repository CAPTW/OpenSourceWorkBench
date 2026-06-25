from __future__ import annotations

import importlib.util
import os

import pytest
from tests.gui.test_optional_solver_gui_health_panel import (
    sample_optional_solver_health_view_model,
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


def test_diagnostics_render_severity_code_message_and_fix(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    text = panel.diagnostics_text()

    assert "gmsh | warning | OSD_MISSING_EXECUTABLE" in text
    assert "Required executable was not discovered: gmsh" in text
    assert "path=executable_requirements.gmsh" in text
    assert "fix=Expose gmsh on PATH." in text


def test_guidance_and_validation_history_render_safe_rows(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    guidance = panel.guidance_text()
    history = panel.validation_history_text()

    assert "non_bundled_solver" in guidance
    assert "not bundled" in guidance
    assert "validation_gate" in guidance
    assert "OSW-VALID prepared-machine gate" in guidance
    assert "issue_closure" in guidance
    assert "Issue closure remains unavailable" in guidance
    assert "OSW-VALID-005: skipped-missing" in history
    assert "not pass evidence" in history
    assert "closure review required" in history
