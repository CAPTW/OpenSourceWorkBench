"""PySide6 smoke tests for the OSW GUI shell."""

from __future__ import annotations

import importlib.util
import os

import pytest

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


def test_main_window_has_expected_shell_regions(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.windowTitle() == "OpenSolver Workbench"
    assert window.project_tree.objectName() == "projectTree"
    assert window.properties_panel.objectName() == "propertiesPanel"
    assert window.run_monitor.objectName() == "runMonitor"
    assert window.viewer_tabs.objectName() == "viewerTabs"

    del app


def test_main_window_has_expected_project_tree_sections(
    app: object,
) -> None:
    from osw.gui.main_window import MainWindow
    from osw.gui.project_tree import PROJECT_SECTIONS

    window = MainWindow()
    root = window.project_tree.topLevelItem(0)

    assert root.text(0) == "OSW Project"
    assert [root.child(index).text(0) for index in range(root.childCount())] == list(
        PROJECT_SECTIONS
    )

    del app


def test_main_window_has_expected_menus(app: object) -> None:
    from osw.gui.main_window import MENU_TITLES, MainWindow

    window = MainWindow()

    assert [action.text() for action in window.menuBar().actions()] == list(MENU_TITLES)

    del app
