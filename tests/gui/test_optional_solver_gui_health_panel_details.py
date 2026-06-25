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


def test_details_render_selected_stack_capabilities_requirements_and_notes(
    app: object,
) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    text = panel.selected_stack_details_text()

    assert "Stack: CalculiX ccx (calculix)" in text
    assert "run_gate: Prepared-machine run gate." in text
    assert "Executable requirements:" in text
    assert "ccx" in text
    assert "detail=<redacted>" in text
    assert "Python package requirements:" in text
    assert "meshio" in text
    assert "Prepared-machine notes:" in text
    assert "Run only where ccx is installed." in text
    assert "Safety notes:" in text
    assert "No solver execution." in text
    assert "Documentation refs:" in text
    assert "docs/validation/calculix.md" in text


def test_details_hide_full_paths_and_environment_values(app: object) -> None:
    from osw.gui.dialogs.optional_solver_health_panel import OptionalSolverHealthPanel

    panel = OptionalSolverHealthPanel(sample_optional_solver_health_view_model())
    text = panel.selected_stack_details_text()

    assert "C:/Users/USER/tools" not in text
    assert "<redacted>" in text
