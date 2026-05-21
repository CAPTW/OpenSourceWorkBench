"""PySide6 main window shell for OSW."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .plot_viewer import build_plot_viewer
from .project_tree import build_project_tree
from .properties_panel import build_properties_panel
from .qt_compat import PySide6UnavailableError, pyside6_missing_message
from .report_panel import build_report_panel
from .result_viewer import build_result_viewer
from .run_monitor import build_run_monitor
from .table_viewer import build_table_viewer
from .workflow_service import WorkbenchItem, WorkbenchWorkflowSession, WorkflowOperation

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

    def __init__(
        self,
        parent: object | None = None,
        *,
        session: WorkbenchWorkflowSession | None = None,
        artifact_dir: str | Path | None = None,
        report_directory: str | Path | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("mainWindow")
        self.setWindowTitle("OpenSolver Workbench")
        self.resize(1280, 820)
        self.workflow_session = session or WorkbenchWorkflowSession(artifact_dir=artifact_dir)
        self._tree_items_by_workflow_id: dict[str, object] = {}

        self.project_tree = build_project_tree(self)
        self.properties_panel = build_properties_panel(self)
        self.run_monitor = build_run_monitor(self)
        self.report_panel = build_report_panel(self)
        if report_directory is not None:
            self.report_panel.export_directory = Path(report_directory)
        self.viewer_tabs = self._build_viewer_tabs()

        self.setCentralWidget(self.viewer_tabs)
        self._build_menus()
        self._build_docks()
        self._section_items = self._project_section_items()
        self._sync_report_state()
        self.project_tree.currentItemChanged.connect(self._on_project_tree_selection_changed)
        self.project_tree.setCurrentItem(self.project_tree.topLevelItem(0))

    def _build_viewer_tabs(self) -> object:
        tabs = QtWidgets.QTabWidget(self)
        tabs.setObjectName("viewerTabs")
        self.result_viewer = build_result_viewer(tabs)
        self.plot_viewer = build_plot_viewer(tabs)
        self.table_viewer = build_table_viewer(tabs)
        tabs.addTab(self.result_viewer, VIEWER_TAB_TITLES[0])
        tabs.addTab(self.plot_viewer, VIEWER_TAB_TITLES[1])
        tabs.addTab(self.table_viewer, VIEWER_TAB_TITLES[2])
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
                elif action_title == "Report":
                    action.triggered.connect(lambda _checked=False: self.export_report())
                elif action_title == "Import":
                    action.triggered.connect(lambda _checked=False: self.open_import_dialog())
                elif action_title == "Run":
                    action.triggered.connect(lambda _checked=False: self.run_workflow())
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
        self._add_dock(
            "Report",
            self.report_panel,
            QtCore.Qt.DockWidgetArea.RightDockWidgetArea,
            "reportDock",
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
        item_id = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        workflow_item = self.workflow_session.item(str(item_id)) if item_id else None
        if workflow_item is None:
            self.properties_panel.set_node_selection(item.text(0))
            return
        self.properties_panel.set_properties(self._properties_for_workflow_item(workflow_item))
        self._load_item_previews(workflow_item)

    def open_plugin_manager(self) -> None:
        from .plugin_manager_dialog import PluginManagerDialog

        dialog = PluginManagerDialog(self)
        dialog.exec()
        self.run_monitor.append_log("Plugin Manager closed", level="info")

    def open_import_dialog(self) -> None:
        selected, _filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Import standard CAD, mesh, script, or MAT data",
            "",
            (
                "OSW inputs (*.stl *.obj *.step *.stp *.iges *.igs *.brep "
                "*.msh *.inp *.bdf *.nas *.fem *.su2 *.vtk *.vtu *.xdmf *.xmf *.cgns "
                "*.m *.mat);;All files (*)"
            ),
        )
        if selected:
            self.import_file(selected)
        else:
            self.run_monitor.append_log("Import cancelled", level="info")

    def import_file(self, path: str | Path) -> WorkflowOperation:
        operation = self.workflow_session.import_path(path)
        self._apply_operation(operation)
        return operation

    def run_workflow(self) -> WorkflowOperation:
        operation = self.workflow_session.run_generate()
        self._apply_operation(operation)
        return operation

    def export_report(self, output_path: str | Path | bool | None = None) -> Path:
        if isinstance(output_path, bool):
            output_path = None
        self._sync_report_state()
        output_path = self.report_panel.export_report(output_path)
        self.run_monitor.append_log(f"Report exported to {output_path}", level="info")
        return output_path

    def _project_section_items(self) -> dict[str, object]:
        root = self.project_tree.topLevelItem(0)
        return {root.child(index).text(0): root.child(index) for index in range(root.childCount())}

    def _apply_operation(self, operation: WorkflowOperation) -> None:
        for item in operation.items:
            self._add_or_update_tree_item(item)
            self._load_item_previews(item)
        for line in operation.logs:
            if line:
                self.run_monitor.append_log(line, level="info")
        self._sync_report_state()
        if operation.selected_item_id:
            selected = self._tree_items_by_workflow_id.get(operation.selected_item_id)
            if selected is not None:
                self.project_tree.setCurrentItem(selected)

    def _add_or_update_tree_item(self, item: WorkbenchItem) -> None:
        existing = self._tree_items_by_workflow_id.get(item.item_id)
        if existing is not None:
            existing.setText(0, item.label)
            return
        parent = self._section_items.get(item.section)
        if parent is None:
            parent = self.project_tree.topLevelItem(0)
        child = QtWidgets.QTreeWidgetItem([item.label])
        child.setData(0, QtCore.Qt.ItemDataRole.UserRole, item.item_id)
        parent.addChild(child)
        parent.setExpanded(True)
        self._tree_items_by_workflow_id[item.item_id] = child

    def _load_item_previews(self, item: WorkbenchItem) -> None:
        if item.mesh_data is not None and hasattr(self.result_viewer, "load_mesh_preview"):
            self.result_viewer.load_mesh_preview(item.mesh_data)
            self.viewer_tabs.setCurrentWidget(self.result_viewer)
        if item.figure_dataset is not None and hasattr(self.plot_viewer, "load_figure_dataset"):
            self.plot_viewer.load_figure_dataset(item.figure_dataset)
            self.viewer_tabs.setCurrentWidget(self.plot_viewer)
        if item.table is not None and hasattr(self.table_viewer, "load_table_preview"):
            self.table_viewer.load_table_preview(item.table)
            self.viewer_tabs.setCurrentWidget(self.table_viewer)

    def _sync_report_state(self) -> None:
        self.report_panel.set_report_state(
            project=self.workflow_session.project,
            figure_datasets=tuple(self.workflow_session.figure_datasets),
            mesh_infos=tuple(self.workflow_session.mesh_infos),
            result_tables=tuple(self.workflow_session.result_tables),
            warnings=tuple(self.workflow_session.warnings),
        )

    def _properties_for_workflow_item(self, item: WorkbenchItem) -> dict[str, str]:
        return item.property_rows(
            project_name=self.workflow_session.project.metadata.name,
            units_name=self.workflow_session.project.units.name,
        )


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
