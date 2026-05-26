"""Tests for the OSW pixel-reference main shell layout."""

from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


REQUIRED_OBJECT_NAMES = {
    "main_window": "oswMainWindow",
    "top_region": "oswTopRegion",
    "workflow_stepper": "oswWorkflowStepper",
    "project_panel": "oswProjectTreePanel",
    "viewport": "oswCentralViewportPanel",
    "run_monitor": "oswRunMonitorPanel",
    "properties_panel": "oswPropertiesPanel",
    "status_bar": "oswStatusBar",
    "menu_bar": "oswMenuBar",
    "main_toolbar": "oswMainToolBar",
}

EXPECTED_MENU_TITLES = ("File", "Import", "Plugins", "Run", "Reports", "Help")
EXPECTED_TOOLBAR_ACTIONS = (
    "New",
    "Open",
    "Save",
    "Save As",
    "Import",
    "Export",
    "Terminal",
    "Preferences",
    "Help",
    "About",
)
EXPECTED_WORKFLOW_STEPS = (
    "1 Import",
    "2 Configure",
    "3 Mesh",
    "4 Run",
    "5 Results",
    "6 Report",
)


def test_layout_contract_constants_are_import_safe_without_pyside6() -> None:
    from osw.gui.main_window import (
        LAYOUT_OBJECT_NAMES,
        MENU_TITLES,
        TOOLBAR_ACTION_TITLES,
        WORKFLOW_STEP_LABELS,
    )

    assert MENU_TITLES == EXPECTED_MENU_TITLES
    assert TOOLBAR_ACTION_TITLES == EXPECTED_TOOLBAR_ACTIONS
    assert WORKFLOW_STEP_LABELS == EXPECTED_WORKFLOW_STEPS
    assert LAYOUT_OBJECT_NAMES == REQUIRED_OBJECT_NAMES


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_main_window_instantiates_with_reference_regions(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.windowTitle() == "OpenSolver Workbench"
    assert window.objectName() == REQUIRED_OBJECT_NAMES["main_window"]
    assert window.top_region.objectName() == REQUIRED_OBJECT_NAMES["top_region"]
    assert window.workflow_stepper.objectName() == REQUIRED_OBJECT_NAMES["workflow_stepper"]
    assert window.project_tree_panel.objectName() == REQUIRED_OBJECT_NAMES["project_panel"]
    assert window.viewport_placeholder.objectName() == REQUIRED_OBJECT_NAMES["viewport"]
    assert window.run_monitor.objectName() == REQUIRED_OBJECT_NAMES["run_monitor"]
    assert window.properties_panel.objectName() == REQUIRED_OBJECT_NAMES["properties_panel"]
    assert window.statusBar().objectName() == REQUIRED_OBJECT_NAMES["status_bar"]


def test_menu_bar_contains_reference_menus(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.menuBar().objectName() == REQUIRED_OBJECT_NAMES["menu_bar"]
    assert [action.text() for action in window.menuBar().actions()] == list(
        EXPECTED_MENU_TITLES
    )


def test_plugins_menu_contains_manager_actions(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.menu_actions["Plugin Manager"].objectName() == "oswActionPluginManager"
    assert window.menu_actions["Refresh Plugins"].objectName() == "oswActionRefreshPlugins"
    assert (
        window.menu_actions["Plugin Health Check"].objectName()
        == "oswActionPluginHealthCheck"
    )


def test_toolbar_contains_reference_actions(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.main_toolbar.objectName() == REQUIRED_OBJECT_NAMES["main_toolbar"]
    assert [action.text() for action in window.main_toolbar.actions()] == list(
        EXPECTED_TOOLBAR_ACTIONS
    )


def test_workflow_stepper_marks_run_active(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.workflow_stepper.step_labels() == list(EXPECTED_WORKFLOW_STEPS)
    assert window.workflow_stepper.active_step_label() == "4 Run"


def test_preferences_action_opens_theme_ui(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    window.preferences_action.trigger()
    assert window.preferences_dialog is not None
    assert window.preferences_dialog.objectName() == "preferencesDialog"


def test_theme_manager_applies_dark_and_light_to_shell(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    window.theme_manager.set_mode("dark", save=False)
    dark_stylesheet = window.theme_manager.apply_to_app(app)
    window.theme_manager.set_mode("light", save=False)
    light_stylesheet = window.theme_manager.apply_to_app(app)

    assert dark_stylesheet
    assert light_stylesheet
    assert dark_stylesheet != light_stylesheet
