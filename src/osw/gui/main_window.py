"""PySide6 main window shell for OSW."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from .plot_viewer import build_plot_viewer
from .project_tree import build_project_tree
from .properties_panel import build_properties_panel
from .qt_compat import PySide6UnavailableError, pyside6_missing_message
from .result_viewer import build_result_viewer
from .run_monitor import build_run_monitor

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

MENU_TITLES = ("File", "Import", "Plugins", "Run", "Reports", "Help")
_BaseMainWindow: Any = QtWidgets.QMainWindow if QtWidgets is not None else object


class MainWindow(_BaseMainWindow):
    """OSW desktop shell with project, viewer, properties, and monitor regions."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("mainWindow")
        self.setWindowTitle("OpenSolver Workbench")
        self.resize(1280, 820)

        self.project_tree = build_project_tree(self)
        self.properties_panel = build_properties_panel(self)
        self.run_monitor = build_run_monitor(self)
        self.viewer_tabs = self._build_viewer_tabs()

        self.setCentralWidget(self.viewer_tabs)
        self._build_menus()
        self._build_docks()

    def _build_viewer_tabs(self) -> object:
        tabs = QtWidgets.QTabWidget(self)
        tabs.setObjectName("viewerTabs")
        tabs.addTab(build_result_viewer(tabs), "Viewer")
        tabs.addTab(build_plot_viewer(tabs), "Plots")
        return tabs

    def _build_menus(self) -> None:
        menu_bar = self.menuBar()
        for title in MENU_TITLES:
            menu_bar.addMenu(title)

    def _build_docks(self) -> None:
        self._add_dock(
            "Project Tree",
            self.project_tree,
            QtCore.Qt.DockWidgetArea.LeftDockWidgetArea,
            "projectTreeDock",
        )
        self._add_dock(
            "Properties",
            self.properties_panel,
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea,
            "propertiesDock",
        )
        self._add_dock(
            "Run Monitor",
            self.run_monitor,
            QtCore.Qt.DockWidgetArea.BottomDockWidgetArea,
            "runMonitorDock",
        )

    def _add_dock(self, title: str, widget: object, area: object, object_name: str) -> None:
        dock = QtWidgets.QDockWidget(title, self)
        dock.setObjectName(object_name)
        dock.setWidget(widget)
        self.addDockWidget(area, dock)


def create_app(argv: Sequence[str] | None = None) -> QApplication:
    if QtWidgets is None:
        raise PySide6UnavailableError(pyside6_missing_message())

    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(list(argv or []))
    app.setApplicationName("OpenSolver Workbench")
    return app


def run_gui(argv: Sequence[str] | None = None) -> int:
    app = create_app(argv)
    window = MainWindow()
    window.show()
    return app.exec()
