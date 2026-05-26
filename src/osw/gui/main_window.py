"""PySide6 main window shell for OSW."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme import ThemeManager
from osw.gui.widgets.top_bar import ACTION_OBJECT_NAMES, TOP_BAR_ACTION_LABELS
from osw.gui.widgets.workflow_stepper import WORKFLOW_STEP_LABELS as _WORKFLOW_STEP_LABELS

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtGui = None
    QtWidgets = None

MENU_TITLES = ("File", "Import", "Plugins", "Run", "Reports", "Help")

# Legacy import-safe contract retained for existing CLI/unit tests.
MENU_ACTIONS = {
    "File": ("New Project", "Open Project", "Save Project"),
    "Import": ("Import",),
    "Plugins": ("Plugin Manager",),
    "Run": ("Run",),
    "Reports": ("Report",),
}

SHELL_MENU_ACTIONS = {
    "File": ("New Project", "Open Project", "Save Project", "Save Project As", "Exit"),
    "Import": ("Import Geometry", "Import Mesh", "Import MATLAB/Octave Script"),
    "Plugins": ("Plugin Manager", "Preferences"),
    "Run": ("Run", "Stop", "Open Results Folder"),
    "Reports": ("Generate Report", "Export Report"),
    "Help": ("Documentation", "About"),
}

TOOLBAR_ACTION_TITLES = TOP_BAR_ACTION_LABELS
WORKFLOW_STEP_LABELS = _WORKFLOW_STEP_LABELS
VIEWER_TAB_TITLES = ("3D Viewer", "Plot Viewer", "Table Viewer")
LAYOUT_OBJECT_NAMES = {
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

_BaseMainWindow: Any = QtWidgets.QMainWindow if QtWidgets is not None else object


class MainWindow(_BaseMainWindow):
    """OSW desktop visual shell with placeholder engineering workbench regions."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        theme_manager: ThemeManager | None = None,
        **_legacy_kwargs: object,
    ) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName(LAYOUT_OBJECT_NAMES["main_window"])
        self.setWindowTitle("OpenSolver Workbench")
        self.resize(2048, 1152)
        self.setMinimumSize(1440, 810)

        self.theme_manager = theme_manager or ThemeManager()
        self.preferences_dialog: object | None = None
        self.toolbar_actions: dict[str, object] = {}
        self.menu_actions: dict[str, object] = {}

        self._build_menus()
        self._build_shell()
        self._build_toolbar_actions()
        self._build_status_bar()
        self._connect_theme()
        self.theme_manager.apply_to_app(QtWidgets.QApplication.instance())

    def _build_menus(self) -> None:
        menu_bar = self.menuBar()
        menu_bar.setObjectName(LAYOUT_OBJECT_NAMES["menu_bar"])
        for title in MENU_TITLES:
            menu = menu_bar.addMenu(title)
            for action_title in SHELL_MENU_ACTIONS[title]:
                action = menu.addAction(action_title)
                action.setObjectName(_action_object_name(action_title))
                self.menu_actions[action_title] = action
                if action_title == "Exit":
                    action.triggered.connect(self.close)
                elif action_title == "Preferences":
                    action.triggered.connect(self.open_preferences)
                else:
                    action.triggered.connect(
                        lambda _checked=False, label=action_title: self._placeholder_action(label)
                    )

    def _build_shell(self) -> None:
        from osw.gui.widgets.project_tree_panel import ProjectTreePanel
        from osw.gui.widgets.properties_panel import PropertiesPanel
        from osw.gui.widgets.run_monitor_panel import RunMonitorPanel
        from osw.gui.widgets.status_bar import OswStatusBar
        from osw.gui.widgets.top_bar import TopBar
        from osw.gui.widgets.viewport_placeholder import CentralViewportPanel

        self._status_bar_class = OswStatusBar
        container = QtWidgets.QWidget(self)
        container.setObjectName("oswCentralShell")
        container_layout = QtWidgets.QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        self.top_region = TopBar(container)
        self.top_region.actionTriggered.connect(self._on_top_bar_action_triggered)
        self.workflow_stepper = self.top_region.workflow_stepper
        self.main_toolbar = self.top_region.main_toolbar
        container_layout.addWidget(self.top_region)

        self.project_tree_panel = ProjectTreePanel(container)
        self.project_tree = self.project_tree_panel.tree
        self.central_viewport_panel = CentralViewportPanel(container)
        self.viewport_placeholder = self.central_viewport_panel
        self.mock_simulation_viewport = self.central_viewport_panel.viewport
        self.run_monitor = RunMonitorPanel(container)
        self.properties_panel = PropertiesPanel(container)
        self.project_tree.currentItemChanged.connect(self._on_project_tree_selection_changed)

        center_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical, container)
        center_splitter.setObjectName("oswCenterVerticalSplitter")
        center_splitter.addWidget(self.central_viewport_panel)
        center_splitter.addWidget(self.run_monitor)
        center_splitter.setStretchFactor(0, 3)
        center_splitter.setStretchFactor(1, 2)
        center_splitter.setSizes([690, 350])

        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, container)
        main_splitter.setObjectName("oswMainHorizontalSplitter")
        main_splitter.addWidget(self.project_tree_panel)
        main_splitter.addWidget(center_splitter)
        main_splitter.addWidget(self.properties_panel)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setStretchFactor(2, 0)
        main_splitter.setSizes([320, 1290, 438])

        container_layout.addWidget(main_splitter, 1)
        self.setCentralWidget(container)

    def _build_toolbar_actions(self) -> None:
        for title in TOOLBAR_ACTION_TITLES:
            action = QtGui.QAction(title, self)
            action.setObjectName(ACTION_OBJECT_NAMES[title])
            self.main_toolbar.addAction(action)
            self.toolbar_actions[title] = action
            if title == "Preferences":
                self.preferences_action = action
                action.triggered.connect(self.open_preferences)
            else:
                action.triggered.connect(
                    lambda _checked=False, label=title: self._placeholder_action(label)
                )

    def _build_status_bar(self) -> None:
        status_bar = self._status_bar_class(self)
        self.setStatusBar(status_bar)

    def _connect_theme(self) -> None:
        self._themed_widgets = (
            self.top_region,
            self.project_tree_panel,
            self.viewport_placeholder,
            self.run_monitor,
            self.properties_panel,
            self.statusBar(),
        )
        self.theme_manager.subscribe(self._on_theme_changed)
        self._on_theme_changed(self.theme_manager.current_tokens)

    def _on_theme_changed(self, tokens: object) -> None:
        for widget in self._themed_widgets:
            if hasattr(widget, "set_theme_tokens"):
                widget.set_theme_tokens(tokens)

    def _on_top_bar_action_triggered(self, label: str) -> None:
        if label == "Preferences":
            self.open_preferences()
            return
        self._placeholder_action(label)

    def _on_project_tree_selection_changed(self, current: object, _previous: object) -> None:
        if current is not None and hasattr(self.properties_panel, "set_node_selection"):
            self.properties_panel.set_node_selection(current.text(0))

    def open_preferences(self) -> None:
        from osw.gui.dialogs.preferences_dialog import PreferencesDialog

        if self.preferences_dialog is None:
            self.preferences_dialog = PreferencesDialog(
                theme_manager=self.theme_manager,
                parent=self,
            )
        self.preferences_dialog.show()
        self.preferences_dialog.raise_()
        self.preferences_dialog.activateWindow()

    def _placeholder_action(self, label: str) -> None:
        if hasattr(self.run_monitor, "append_log"):
            self.run_monitor.append_log(f"{label} action selected", level="info")


def _action_object_name(action_title: str) -> str:
    words = "".join(part.capitalize() for part in action_title.replace("/", " ").split())
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
