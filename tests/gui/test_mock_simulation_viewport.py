"""Tests for the UI-005 central mock simulation viewport."""

from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtCore, QtGui, QtWidgets
else:
    QtCore = None
    QtGui = None
    QtWidgets = None


def test_viewport_contract_is_import_safe_without_pyside6() -> None:
    from osw.gui.widgets.mock_simulation_viewport import (
        DEFAULT_RESULT_QUANTITY,
        DEFAULT_RESULT_UNIT,
        VIEWPORT_FEATURE_FLAGS,
    )
    from osw.gui.widgets.viewport_toolbar import VIEWPORT_TOOL_ACTIONS

    assert DEFAULT_RESULT_QUANTITY == "von Mises Stress"
    assert DEFAULT_RESULT_UNIT == "Pa"
    assert VIEWPORT_FEATURE_FLAGS == {
        "has_color_legend": True,
        "has_orientation_cube": True,
        "has_axis_triad": True,
        "has_scale_bar": True,
        "has_mesh_overlay": True,
    }
    assert VIEWPORT_TOOL_ACTIONS == (
        "Select",
        "Orbit",
        "Pan",
        "Zoom",
        "Fit",
        "Section",
        "Camera",
    )


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_central_viewport_panel_instantiates(app: object) -> None:
    from osw.gui.widgets.viewport_placeholder import CentralViewportPanel

    panel = CentralViewportPanel()

    assert panel.objectName() == "oswCentralViewportPanel"
    assert panel.toolbar.objectName() == "oswViewportToolbar"
    assert panel.viewport.objectName() == "oswMockSimulationViewport"
    assert panel.objectName() != "oswViewportPlaceholder"


def test_viewport_toolbar_contains_view_selector_and_actions(app: object) -> None:
    from osw.gui.widgets.viewport_toolbar import VIEWPORT_TOOL_ACTIONS, ViewportToolbar

    toolbar = ViewportToolbar()

    assert toolbar.objectName() == "oswViewportToolbar"
    assert toolbar.view_selector.objectName() == "oswViewportViewSelector"
    assert toolbar.view_selector.currentText() == "von Mises Stress"
    assert toolbar.action_labels() == list(VIEWPORT_TOOL_ACTIONS)


def test_mock_simulation_viewport_defaults_and_flags(app: object) -> None:
    from osw.gui.widgets.mock_simulation_viewport import MockSimulationViewport

    viewport = MockSimulationViewport()

    assert viewport.objectName() == "oswMockSimulationViewport"
    assert viewport.result_quantity() == "von Mises Stress"
    assert viewport.result_unit() == "Pa"
    assert viewport.has_color_legend is True
    assert viewport.has_orientation_cube is True
    assert viewport.has_axis_triad is True
    assert viewport.has_scale_bar is True
    assert viewport.has_mesh_overlay is True


def test_mock_simulation_viewport_setters(app: object) -> None:
    from osw.gui.widgets.mock_simulation_viewport import MockSimulationViewport

    viewport = MockSimulationViewport()

    viewport.set_show_mesh_overlay(False)
    assert viewport.has_mesh_overlay is False
    viewport.set_show_mesh_overlay(True)
    assert viewport.has_mesh_overlay is True

    viewport.set_result_quantity("Temperature", "°C")
    assert viewport.result_quantity() == "Temperature"
    assert viewport.result_unit() == "°C"


def test_mock_simulation_viewport_accepts_dark_and_light_tokens(app: object) -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.widgets.mock_simulation_viewport import MockSimulationViewport

    viewport = MockSimulationViewport()
    manager = ThemeManager(auto_load=False)

    manager.set_mode("dark", save=False)
    viewport.set_theme_tokens(manager.current_tokens)
    manager.set_mode("light", save=False)
    viewport.set_theme_tokens(manager.current_tokens)

    assert viewport.current_tokens is manager.current_tokens


def test_mock_simulation_viewport_renders_non_null_pixmap(app: object) -> None:
    assert QtCore is not None
    assert QtGui is not None
    from osw.gui.widgets.mock_simulation_viewport import MockSimulationViewport

    viewport = MockSimulationViewport()
    viewport.resize(720, 420)
    pixmap = QtGui.QPixmap(viewport.size())
    pixmap.fill(QtCore.Qt.GlobalColor.transparent)
    viewport.render(pixmap)

    assert not pixmap.isNull()


def test_main_window_uses_central_viewport_panel(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.top_region.objectName() == "oswTopRegion"
    assert window.workflow_stepper.objectName() == "oswWorkflowStepper"
    assert window.project_tree_panel.objectName() == "oswProjectTreePanel"
    assert window.viewport_placeholder.objectName() == "oswCentralViewportPanel"
    assert window.central_viewport_panel.objectName() == "oswCentralViewportPanel"
    assert window.mock_simulation_viewport.objectName() == "oswMockSimulationViewport"
    assert window.run_monitor.objectName() == "oswRunMonitorPanel"
    assert window.properties_panel.objectName() == "oswPropertiesPanel"
    assert window.statusBar().objectName() == "oswStatusBar"
