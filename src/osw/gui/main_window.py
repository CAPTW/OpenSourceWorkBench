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
from .table_viewer import build_table_viewer

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

MENU_TITLES = ("File", "Import", "Plugins", "Run", "Reports", "Help")
MENU_ACTIONS = {
    "File": ("New Project", "Open Project", "Save Project"),
    "Import": ("Import",),
    "Plugins": ("Plugin Manager",),
    "Run": ("Run",),
    "Reports": ("Report",),
}
VIEWER_TAB_TITLES = ("3D Viewer", "Plot Viewer", "Table Viewer")
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
        self.project_tree.currentItemChanged.connect(self._on_project_tree_selection_changed)
        self.project_tree.setCurrentItem(self.project_tree.topLevelItem(0))

    def _build_viewer_tabs(self) -> object:
        tabs = QtWidgets.QTabWidget(self)
        tabs.setObjectName("viewerTabs")
        tabs.addTab(build_result_viewer(tabs), VIEWER_TAB_TITLES[0])
        tabs.addTab(build_plot_viewer(tabs), VIEWER_TAB_TITLES[1])
        tabs.addTab(build_table_viewer(tabs), VIEWER_TAB_TITLES[2])
        return tabs

    def _build_menus(self) -> None:
        menu_bar = self.menuBar()
        for title in MENU_TITLES:
            menu = menu_bar.addMenu(title)
            for action_title in MENU_ACTIONS.get(title, ()):
                action = menu.addAction(action_title)
                action.setObjectName(_action_object_name(action_title))
                if action_title == "Plugin Manager":
                    action.triggered.connect(self.open_plugin_manager)
                else:
                    action.triggered.connect(
                        lambda _checked=False, label=action_title: self.run_monitor.append_log(
                            f"{label} action selected",
                            level="info",
                        )
                    )

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

    def _on_project_tree_selection_changed(self, item: object | None, _previous: object) -> None:
        if item is None:
            self.properties_panel.set_node_selection("")
            return
        self.properties_panel.set_node_selection(item.text(0))

    def open_plugin_manager(self) -> None:
        from .plugin_manager_dialog import PluginManagerDialog

        dialog = PluginManagerDialog(self)
        dialog.exec()
        self.run_monitor.append_log("Plugin Manager closed", level="info")


def _action_object_name(action_title: str) -> str:
    words = "".join(part.capitalize() for part in action_title.split())
    return f"action{words}"


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
