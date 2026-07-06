"""PySide6 main window shell for OSW."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.executables import ExecutablePathRegistry
from osw.core.project_schema import Project
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme import ThemeManager
from osw.gui.widgets.top_bar import ACTION_OBJECT_NAMES, TOP_BAR_ACTION_LABELS
from osw.gui.widgets.workflow_stepper import WORKFLOW_STEP_LABELS as _WORKFLOW_STEP_LABELS
from osw.plugins.registry import PluginRegistry
from osw.plugins.state import PluginStateStore

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtGui = None
    QtWidgets = None

MENU_TITLES = ("File", "Import", "Plugins", "Run", "CHM", "Reports", "Help")

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
    "Import": (
        "Import Geometry",
        "Import Mesh",
        "Generate Mesh with Gmsh...",
        "Import MATLAB/Octave Script",
        "Import MATLAB MAT Data",
        "3D Mesh Preview",
    ),
    "Plugins": ("Plugin Manager", "Refresh Plugins", "Plugin Health Check", "Preferences"),
    "Run": (
        "Run",
        "Stop",
        "Generate CalculiX Input Deck...",
        "Generate OpenFOAM Template Case...",
        "Open Results Folder",
    ),
    "CHM": ("CoolProp Property Calculator...", "Cantera 0D Reactor..."),
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
        project: Project | None = None,
        plugin_paths: Sequence[str | Path] = (),
        plugin_registry: PluginRegistry | None = None,
        plugin_state_store: PluginStateStore | None = None,
        executable_registry: ExecutablePathRegistry | None = None,
        mesh_scene_adapter_factory: Callable[[], Any] | None = None,
        **legacy_kwargs: object,
    ) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName(LAYOUT_OBJECT_NAMES["main_window"])
        self.setWindowTitle("OpenSolver Workbench")
        self.resize(2048, 1152)
        self.setMinimumSize(1440, 810)

        self.theme_manager = theme_manager or ThemeManager()
        self.current_project = project or create_heatsink_flow_demo_project()
        self.plugin_paths = tuple(Path(path) for path in plugin_paths)
        self.plugin_registry = plugin_registry or PluginRegistry()
        self.plugin_state_store = plugin_state_store or PluginStateStore()
        self.executable_registry = executable_registry or ExecutablePathRegistry()
        report_directory = legacy_kwargs.get("report_directory")
        self.report_directory = (
            Path(report_directory)
            if report_directory is not None
            else Path("artifacts") / "report"
        )
        from osw.gui.workflow_service import WorkbenchWorkflowSession

        self.workflow_session = WorkbenchWorkflowSession(
            project=self.current_project,
            artifact_dir=legacy_kwargs.get("artifact_dir"),
            registry=self.executable_registry,
        )
        self.plugin_health_map: dict[str, object] = {}
        self.plugin_discovery_result: object | None = None
        self.plugin_manager_dialog: object | None = None
        self.script_preview_dialog: object | None = None
        self.mat_preview_dialog: object | None = None
        self.boundary_curve_dialog: object | None = None
        self.gmsh_mesh_dialog: object | None = None
        self.calculix_deck_dialog: object | None = None
        self.openfoam_template_dialog: object | None = None
        self.chm_property_dialog: object | None = None
        self.chm_reactor_dialog: object | None = None
        self.result_viewer_dialog: object | None = None
        self.result_viewer: object | None = None
        self.plot_viewer_dialog: object | None = None
        self.plot_viewer: object | None = None
        self.mesh_viewer_dialog: object | None = None
        self.mesh_viewer: object | None = None
        self._mesh_scene_adapter_factory = mesh_scene_adapter_factory
        self.last_imported_mesh_data: object | None = None
        self.last_imported_mesh_ref: str | None = None
        self.result_catalog: object | None = None
        self.last_figure_dataset: object | None = None
        self.last_result_datasets: tuple[object, ...] = ()
        self.preferences_dialog: object | None = None
        self.toolbar_actions: dict[str, object] = {}
        self.menu_actions: dict[str, object] = {}

        self._build_menus()
        self._build_shell()
        self.refresh_plugins(log=False)
        self.set_project(self.current_project)
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
                elif action_title == "New Project":
                    action.triggered.connect(self.new_project)
                elif action_title == "Preferences":
                    action.triggered.connect(self.open_preferences)
                elif action_title == "Plugin Manager":
                    action.triggered.connect(self.open_plugin_manager)
                elif action_title == "Refresh Plugins":
                    action.triggered.connect(self.refresh_plugins)
                elif action_title == "Plugin Health Check":
                    action.triggered.connect(self.run_plugin_health_check)
                elif action_title == "Generate Report":
                    action.triggered.connect(self.generate_report_preview)
                elif action_title == "Export Report":
                    action.triggered.connect(self.export_current_report)
                elif action_title == "Generate Mesh with Gmsh...":
                    action.triggered.connect(self.open_gmsh_mesh_dialog)
                elif action_title == "Generate CalculiX Input Deck...":
                    action.triggered.connect(self.open_calculix_deck_dialog)
                elif action_title == "Generate OpenFOAM Template Case...":
                    action.triggered.connect(self.open_openfoam_template_dialog)
                elif action_title == "CoolProp Property Calculator...":
                    action.triggered.connect(self.open_chm_property_dialog)
                elif action_title == "Cantera 0D Reactor...":
                    action.triggered.connect(self.open_chm_reactor_dialog)
                elif action_title == "3D Mesh Preview":
                    action.setObjectName("oswActionOpenMeshViewer")
                    action.triggered.connect(self.open_mesh_viewer)
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
        self.properties_panel.plugins_section.manage_plugins_requested.connect(
            self.open_plugin_manager
        )
        self.properties_panel.report_preview_panel.exportRequested.connect(
            self.export_current_report
        )
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
        if self.plugin_manager_dialog is not None and hasattr(
            self.plugin_manager_dialog,
            "set_theme_tokens",
        ):
            self.plugin_manager_dialog.set_theme_tokens(tokens)
        if self.script_preview_dialog is not None and hasattr(
            self.script_preview_dialog,
            "set_theme_tokens",
        ):
            self.script_preview_dialog.set_theme_tokens(tokens)
        if self.mat_preview_dialog is not None and hasattr(
            self.mat_preview_dialog,
            "set_theme_tokens",
        ):
            self.mat_preview_dialog.set_theme_tokens(tokens)
        if self.boundary_curve_dialog is not None and hasattr(
            self.boundary_curve_dialog,
            "set_theme_tokens",
        ):
            self.boundary_curve_dialog.set_theme_tokens(tokens)
        if self.gmsh_mesh_dialog is not None and hasattr(
            self.gmsh_mesh_dialog,
            "set_theme_tokens",
        ):
            self.gmsh_mesh_dialog.set_theme_tokens(tokens)
        if self.calculix_deck_dialog is not None and hasattr(
            self.calculix_deck_dialog,
            "set_theme_tokens",
        ):
            self.calculix_deck_dialog.set_theme_tokens(tokens)
        if self.openfoam_template_dialog is not None and hasattr(
            self.openfoam_template_dialog,
            "set_theme_tokens",
        ):
            self.openfoam_template_dialog.set_theme_tokens(tokens)
        if self.chm_property_dialog is not None and hasattr(
            self.chm_property_dialog,
            "set_theme_tokens",
        ):
            self.chm_property_dialog.set_theme_tokens(tokens)
        if self.chm_reactor_dialog is not None and hasattr(
            self.chm_reactor_dialog,
            "set_theme_tokens",
        ):
            self.chm_reactor_dialog.set_theme_tokens(tokens)
        if self.result_viewer is not None and hasattr(
            self.result_viewer,
            "set_theme_tokens",
        ):
            self.result_viewer.set_theme_tokens(tokens)

    def _on_top_bar_action_triggered(self, label: str) -> None:
        if label == "New":
            self.new_project()
            return
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

    def open_plugin_manager(self) -> None:
        from osw.gui.dialogs.plugin_manager_dialog import PluginManagerDialog

        if self.plugin_manager_dialog is None:
            self.plugin_manager_dialog = PluginManagerDialog(
                parent=self,
                plugin_paths=self.plugin_paths,
                state_store=self.plugin_state_store,
                executable_registry=self.executable_registry,
                include_entry_points=True,
                theme_tokens=self.theme_manager.current_tokens,
            )
            self.plugin_manager_dialog.pluginStateChanged.connect(
                self._on_plugin_state_changed
            )
            self.plugin_manager_dialog.executablePathsChanged.connect(
                self._on_executable_paths_changed
            )
        else:
            self.plugin_manager_dialog.refresh_plugins()
            self.plugin_manager_dialog.set_theme_tokens(self.theme_manager.current_tokens)
        self.plugin_manager_dialog.show()
        self.plugin_manager_dialog.raise_()
        self.plugin_manager_dialog.activateWindow()

    def refresh_plugins(self, _checked: bool = False, *, log: bool = True) -> object:
        from osw.plugins.discovery import (
            discover_local_plugin_manifests,
            discover_plugin_search_paths,
        )

        plugin_paths = self.plugin_paths or discover_plugin_search_paths(
            include_project_plugins=True,
            include_user_plugins=False,
        )
        self.plugin_discovery_result = discover_local_plugin_manifests(plugin_paths)
        self.plugin_registry = self.plugin_discovery_result.to_registry()
        self.run_plugin_health_check(log=False)
        if hasattr(self.properties_panel, "set_plugin_registry"):
            self.properties_panel.set_plugin_registry(self.plugin_registry)
            self.properties_panel.set_plugin_health_map(self.plugin_health_map)
        if log:
            self._placeholder_action("Refresh Plugins")
        return self.plugin_discovery_result

    def run_plugin_health_check(
        self,
        _checked: bool = False,
        *,
        log: bool = True,
    ) -> dict[str, object]:
        from osw.plugins.health import build_plugin_health_record

        health_map = {
            manifest.id: build_plugin_health_record(
                manifest,
                enabled=self.plugin_state_store.is_enabled(manifest.id),
                executable_paths=self.plugin_state_store.executable_paths(),
            )
            for manifest in self.plugin_registry.values()
        }
        self.plugin_health_map = health_map
        if hasattr(self.properties_panel, "set_plugin_health_map"):
            self.properties_panel.set_plugin_health_map(health_map)
        if log:
            self._placeholder_action("Plugin Health Check")
        return health_map

    def import_file(self, path: str | Path) -> object:
        """Import or preview a file through the prepare-only workflow service."""

        operation = self.workflow_session.import_path(path)
        self._apply_workflow_operation(operation)
        self._store_workflow_mesh_for_viewer(operation)
        return operation

    def run_workflow(self, _checked: bool = False) -> object:
        """Prepare bounded workflow artifacts without executing external solvers."""

        operation = self.workflow_session.run_generate()
        self._apply_workflow_operation(operation)
        return operation

    def export_report(self, output_path: str | Path | None = None) -> Path:
        """Compatibility wrapper for solver-free GUI report export smoke tests."""

        target = (
            Path(output_path)
            if output_path is not None
            else self.report_directory / "gui_workflow_report.html"
        )
        return self.export_current_report(output_path=target)

    def _apply_workflow_operation(self, operation: object) -> None:
        self.set_project(self.workflow_session.project, sync_workflow=False)
        self._append_workflow_items_to_tree(getattr(operation, "items", ()) or ())
        for line in getattr(operation, "logs", ()) or ():
            if hasattr(self.run_monitor, "append_log"):
                self.run_monitor.append_log(str(line), level="info")
        self.generate_report_preview(log=False)

    def _append_workflow_items_to_tree(self, items: Sequence[object]) -> None:
        if not items or self.project_tree.topLevelItemCount() == 0:
            return

        root = self.project_tree.topLevelItem(0)
        sections = {
            root.child(index).text(0): root.child(index)
            for index in range(root.childCount())
        }
        for item in items:
            section_name = str(getattr(item, "section", "") or "Results")
            section = sections.get(section_name)
            if section is None:
                section = QtWidgets.QTreeWidgetItem([section_name, ""])
                root.addChild(section)
                sections[section_name] = section
            status = str(getattr(item, "status", "") or "")
            marker = "✓" if status.lower().startswith(
                ("imported", "prepared", "previewed", "calculated")
            ) else ""
            child = QtWidgets.QTreeWidgetItem([str(getattr(item, "label", "")), marker])
            child.setData(0, QtCore.Qt.ItemDataRole.UserRole, "workflow")
            section.addChild(child)
            section.setExpanded(True)
        root.setExpanded(True)

    def set_project(self, project: Project, *, sync_workflow: bool = True) -> None:
        self.current_project = project
        if sync_workflow and hasattr(self, "workflow_session"):
            self.workflow_session.project = project
        if hasattr(self.project_tree_panel, "set_project"):
            self.project_tree_panel.set_project(project)
        if hasattr(self.properties_panel, "set_project"):
            self.properties_panel.set_project(project)
        self.refresh_results_from_project(update_report=False)
        self.generate_report_preview(log=False)

    def build_current_report_summary(self) -> object:
        """Build report summary data without executing tools."""

        from osw.post.report_sections import build_report_summary

        figure_datasets = (
            (self.last_figure_dataset,)
            if self.last_figure_dataset is not None
            else ()
        )
        return build_report_summary(
            self.current_project,
            figure_datasets=(
                *figure_datasets,
                *tuple(getattr(self.workflow_session, "figure_datasets", ())),
            ),
            mesh_infos=tuple(getattr(self.workflow_session, "mesh_infos", ())),
            plugin_health=self.plugin_health_map,
            result_tables=(
                *_result_tables_from_datasets(self._result_datasets_for_report()),
                *tuple(getattr(self.workflow_session, "result_tables", ())),
            ),
            warnings=tuple(getattr(self.workflow_session, "warnings", ())),
        )

    def generate_report_preview(self, _checked: bool = False, *, log: bool = True) -> object:
        """Refresh the right-panel report preview from current project data."""

        summary = self.build_current_report_summary()
        report_panel = self.properties_panel.report_preview_panel
        if hasattr(report_panel, "set_report_summary"):
            report_panel.set_report_summary(summary)
        if log:
            self._placeholder_action("Generate Report")
        return summary

    def export_current_report(
        self,
        _checked: bool = False,
        *,
        output_path: str | Path | None = None,
    ) -> Path:
        """Export the current report through post/report services only."""

        from osw.post.report_generator import build_report
        from osw.post.report_model import ReportBuildRequest

        target = Path(output_path) if output_path is not None else _default_report_export_path(
            self.current_project
        )
        figure_datasets = (
            (self.last_figure_dataset,)
            if self.last_figure_dataset is not None
            else ()
        )
        result = build_report(
            ReportBuildRequest(project=self.current_project, output_path=target, format="html"),
            figure_datasets=(
                *figure_datasets,
                *tuple(getattr(self.workflow_session, "figure_datasets", ())),
            ),
            mesh_infos=tuple(getattr(self.workflow_session, "mesh_infos", ())),
            plugin_health=self.plugin_health_map,
            result_tables=(
                *_result_tables_from_datasets(self._result_datasets_for_report()),
                *tuple(getattr(self.workflow_session, "result_tables", ())),
            ),
            warnings=tuple(getattr(self.workflow_session, "warnings", ())),
        )
        if hasattr(self.properties_panel.report_preview_panel, "set_report_summary"):
            self.properties_panel.report_preview_panel.set_report_summary(result.summary)
        self._placeholder_action(f"Exported report: {result.output_path}")
        return Path(result.output_path)

    def new_project(self) -> None:
        """Reset to the curated demo project until full project creation is designed."""

        self.set_project(create_heatsink_flow_demo_project())
        self._placeholder_action("New Project")

    def import_mesh_file(self, path: str | Path) -> bool:
        """Preview-import mesh metadata and attach it to the current project.

        This method uses the meshio bridge only. It does not run external tools or
        solver processes.
        """

        from osw.mesh.meshio_bridge import read_mesh

        return self.attach_mesh_to_project(read_mesh(path))

    def attach_mesh_to_project(self, mesh_result: object) -> bool:
        from osw.mesh.meshio_bridge import mesh_to_project_ref

        mesh = getattr(mesh_result, "mesh", None)
        diagnostics = getattr(mesh_result, "diagnostics", None)
        if mesh is None:
            if diagnostics is not None and hasattr(diagnostics, "summary"):
                self._placeholder_action(diagnostics.summary())
            return False

        mesh_ref = mesh_to_project_ref(mesh)
        self.set_project(_project_with_mesh_ref(self.current_project, mesh_ref))
        self._placeholder_action(f"Imported mesh metadata: {mesh_ref.name}")
        self._store_imported_mesh_for_viewer(mesh)
        return True

    def _store_imported_mesh_for_viewer(self, mesh: object, *, mesh_ref: str | None = None) -> None:
        """Record the latest imported mesh for the 3D preview (latest wins).

        Stores an already-built ``MeshData`` and a stable ``mesh_ref`` and, if the
        preview panel already exists, refreshes its content in place. When
        ``mesh_ref`` is not supplied it is derived from the mesh object's id/name
        (the meshio ``MeshModel`` path); callers with a bare ``MeshData`` pass an
        explicit ``mesh_ref`` (e.g. the workflow item id). It does not open/raise
        the dialog on import (populate-on-open handles the first user open) and it
        runs no rendering, generation, parsing, or conversion.
        """

        mesh_data = mesh.to_mesh_data() if hasattr(mesh, "to_mesh_data") else mesh
        resolved_ref = (
            mesh_ref
            if mesh_ref is not None
            else (getattr(mesh, "id", "") or getattr(mesh, "name", ""))
        )
        self.last_imported_mesh_data = mesh_data
        self.last_imported_mesh_ref = resolved_ref or None
        if self.mesh_viewer is not None and hasattr(self.mesh_viewer, "set_mesh"):
            self.mesh_viewer.set_mesh(mesh_data, mesh_ref=self.last_imported_mesh_ref or "")

    def _store_workflow_mesh_for_viewer(self, operation: object) -> None:
        """Feed the latest imported mesh item into the 3D preview (general import).

        For a general file-import operation, the last item carrying an already-built
        ``MeshData`` is handed to the preview using its stable ``item_id`` as the
        mesh reference. Non-mesh items (``mesh_data`` is ``None`` -- geometry,
        script, data) are ignored, so those imports never feed or clobber the
        viewer. This does not open/raise the dialog and runs no rendering,
        generation, parsing, or conversion.
        """

        latest = None
        for item in getattr(operation, "items", ()) or ():
            if getattr(item, "mesh_data", None) is not None:
                latest = item
        if latest is not None:
            self._store_imported_mesh_for_viewer(
                latest.mesh_data, mesh_ref=getattr(latest, "item_id", None)
            )

    def preview_script_file(self, path: str | Path, *, show_dialog: bool = False) -> bool:
        """Preview a MATLAB/Octave script and attach its ScriptRef metadata.

        The preview path is text-only. It records metadata and safety findings
        without launching MATLAB, Octave, or any script content.
        """

        from osw.gui.dialogs.script_preview_dialog import ScriptPreviewDialog
        from osw.scripts.mscript.importer import create_script_ref, preview_mscript

        result = preview_mscript(path)
        if result.preview is None:
            self._placeholder_action(result.diagnostics.summary())
            return False

        preview = result.preview
        if show_dialog:
            self.script_preview_dialog = ScriptPreviewDialog(
                preview=preview,
                parent=self,
                theme_tokens=self.theme_manager.current_tokens,
            )
            accepted = self.script_preview_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
            if not accepted:
                return False

        script_ref = create_script_ref(preview)
        self.set_project(_project_with_script_ref(self.current_project, script_ref))
        self._placeholder_action(f"Previewed script metadata: {script_ref.name}")
        return True

    def open_script_preview_dialog(self, path: str | Path) -> object | None:
        """Open the script preview dialog without mutating the project until accepted."""

        from osw.gui.dialogs.script_preview_dialog import ScriptPreviewDialog
        from osw.scripts.mscript.importer import create_script_ref, preview_mscript

        result = preview_mscript(path)
        if result.preview is None:
            self._placeholder_action(result.diagnostics.summary())
            return None

        dialog = ScriptPreviewDialog(
            preview=result.preview,
            parent=self,
            theme_tokens=self.theme_manager.current_tokens,
        )

        def _attach(preview: object) -> None:
            self.set_project(
                _project_with_script_ref(self.current_project, create_script_ref(preview))
            )
            self._placeholder_action(f"Previewed script metadata: {getattr(preview, 'name', '')}")

        dialog.previewAccepted.connect(_attach)
        dialog.scriptRunCompleted.connect(self._on_script_run_completed)
        dialog.figureDatasetReady.connect(self._on_figure_dataset_ready)
        self.script_preview_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    def preview_mat_file(self, path: str | Path, *, show_dialog: bool = False) -> bool:
        """Preview MATLAB MAT data and attach metadata without executing code."""

        from osw.gui.dialogs.mat_preview_dialog import MatPreviewDialog
        from osw.scripts.mscript.mat_reader import create_mat_script_ref, read_mat_file

        result = read_mat_file(path)
        if show_dialog:
            self.mat_preview_dialog = MatPreviewDialog(
                result=result,
                parent=self,
                theme_tokens=self.theme_manager.current_tokens,
            )
            accepted = self.mat_preview_dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted
            if not accepted:
                return False
        if result.diagnostics.has_errors:
            self._placeholder_action(result.diagnostics.summary())
            return False
        mat_ref = create_mat_script_ref(result)
        self.set_project(_project_with_script_ref(self.current_project, mat_ref))
        self._placeholder_action(f"Previewed MAT metadata: {mat_ref.name}")
        return True

    def open_mat_preview_dialog(self, path: str | Path) -> object | None:
        """Open the MAT preview dialog without running MATLAB, Octave, or scripts."""

        from osw.gui.dialogs.mat_preview_dialog import MatPreviewDialog
        from osw.scripts.mscript.mat_reader import create_mat_script_ref, read_mat_file

        result = read_mat_file(path)
        dialog = MatPreviewDialog(
            result=result,
            parent=self,
            theme_tokens=self.theme_manager.current_tokens,
        )

        def _attach(mat_result: object) -> None:
            diagnostics = getattr(mat_result, "diagnostics", None)
            if diagnostics is not None and diagnostics.has_errors:
                self._placeholder_action(mat_result.diagnostics.summary())
                return
            self.set_project(
                _project_with_script_ref(self.current_project, create_mat_script_ref(mat_result))
            )
            self._placeholder_action(
                f"Previewed MAT metadata: {Path(getattr(mat_result, 'source_path', '')).name}"
            )

        dialog.matPreviewAccepted.connect(_attach)
        self.mat_preview_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    def attach_boundary_curve_to_project(self, curve: object) -> bool:
        """Attach a validated BoundaryCurve to the current project without solver binding."""

        validate = getattr(curve, "validate", None)
        if callable(validate):
            report = validate()
            if getattr(report, "has_errors", False):
                self._placeholder_action(report.friendly_summary())
                return False
        self.set_project(_project_with_boundary_curve(self.current_project, curve))
        self._placeholder_action(
            f"Attached boundary curve: {getattr(curve, 'name', getattr(curve, 'curve_id', ''))}"
        )
        return True

    def open_boundary_curve_dialog(self, curve: object) -> object:
        """Open a safe BoundaryCurve preview dialog without executing external tools."""

        from osw.gui.dialogs.boundary_curve_dialog import BoundaryCurveDialog

        dialog = BoundaryCurveDialog(
            curve=curve,
            parent=self,
            theme_tokens=self.theme_manager.current_tokens,
        )
        dialog.boundaryCurveAccepted.connect(self.attach_boundary_curve_to_project)
        self.boundary_curve_dialog = dialog
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        return dialog

    def open_gmsh_mesh_dialog(self, _checked: bool = False) -> object:
        """Open the safe Gmsh request preview dialog."""

        from osw.gui.dialogs.gmsh_mesh_dialog import GmshMeshDialog

        if self.gmsh_mesh_dialog is None:
            self.gmsh_mesh_dialog = GmshMeshDialog(
                parent=self,
                theme_tokens=self.theme_manager.current_tokens,
            )
        else:
            self.gmsh_mesh_dialog.set_theme_tokens(self.theme_manager.current_tokens)
        self.gmsh_mesh_dialog.show()
        self.gmsh_mesh_dialog.raise_()
        self.gmsh_mesh_dialog.activateWindow()
        return self.gmsh_mesh_dialog

    def generate_gmsh_mesh_from_request(self, request: object) -> object:
        """Prepare an explicit Gmsh request without launching Gmsh from the GUI."""

        self._placeholder_action(
            "Prepared Gmsh mesh request; external Gmsh execution is unavailable from GUI."
        )
        return request

    def attach_gmsh_mesh_result(self, result: object) -> bool:
        """Attach generated mesh metadata when a Gmsh result produced an artifact."""

        from osw.mesh.gmsh_adapter import convert_result_to_mesh_ref

        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        msh_path = getattr(result, "msh_path", None)
        converted = getattr(result, "converted_mesh_path", None)
        if converted is None and (msh_path is None or not Path(msh_path).exists()):
            diagnostics = getattr(result, "diagnostics", None)
            if diagnostics is not None and hasattr(diagnostics, "summary"):
                self._placeholder_action(diagnostics.summary())
            return False
        mesh_ref = convert_result_to_mesh_ref(result)
        self.set_project(_project_with_mesh_ref(self.current_project, mesh_ref))
        self._placeholder_action(f"Gmsh mesh generation: {status}")
        return True

    def open_calculix_deck_dialog(self, _checked: bool = False) -> object:
        """Open a safe CalculiX deck preview dialog without running ccx."""

        from importlib import import_module

        from osw.gui.dialogs.calculix_deck_dialog import CalculixDeckDialog

        adapter = import_module("osw.solvers.calculix.adapter")
        result = adapter.project_to_calculix_deck(self.current_project)
        self.calculix_deck_dialog = CalculixDeckDialog(
            parent=self,
            result=result,
            theme_tokens=self.theme_manager.current_tokens,
        )
        self.calculix_deck_dialog.deckWritten.connect(self._on_calculix_deck_written)
        if hasattr(self.calculix_deck_dialog, "calculixRunCompleted"):
            self.calculix_deck_dialog.calculixRunCompleted.connect(
                self._on_calculix_run_completed
            )
        if hasattr(self.calculix_deck_dialog, "calculixResultsParsed"):
            self.calculix_deck_dialog.calculixResultsParsed.connect(
                self._on_calculix_results_parsed
            )
        self.calculix_deck_dialog.show()
        self.calculix_deck_dialog.raise_()
        self.calculix_deck_dialog.activateWindow()
        return self.calculix_deck_dialog

    def _on_calculix_deck_written(self, path: str) -> None:
        if hasattr(self.run_monitor, "append_log"):
            self.run_monitor.append_log(f"Generated CalculiX input deck: {path}", level="info")

    def _on_calculix_run_completed(self, result: object) -> None:
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        if not hasattr(self.run_monitor, "append_log"):
            return
        self.run_monitor.append_log(f"CalculiX run: {status}", level="info")
        case_dir = getattr(result, "case_dir", "")
        if case_dir:
            self.run_monitor.append_log(f"CalculiX case directory: {case_dir}", level="info")
        combined = str(getattr(result, "combined_log", "") or "").strip()
        if combined:
            self.run_monitor.append_log(combined.splitlines()[-1], level="info")
        artifact_count = len(getattr(result, "artifacts", ()) or ())
        self.run_monitor.append_log(
            f"Collected {artifact_count} CalculiX artifact(s).",
            level="info",
        )

    def _on_calculix_results_parsed(self, parsed: object) -> None:
        if not hasattr(self.run_monitor, "append_log"):
            return
        displacement = getattr(parsed, "displacement_summary", None)
        stress = getattr(parsed, "stress_summary", None)
        max_displacement = getattr(displacement, "max_magnitude", None)
        max_stress = getattr(stress, "max_von_mises", None)
        parts = []
        if max_displacement is not None:
            parts.append(f"max displacement {float(max_displacement):.6g}")
        if max_stress is not None:
            parts.append(f"max stress {float(max_stress):.6g}")
        summary = ", ".join(parts) if parts else "no scalar summaries found"
        self.run_monitor.append_log(f"Parsed CalculiX results: {summary}.", level="info")
        try:
            parser_module = __import__(
                "osw.solvers.calculix.result_parser",
                fromlist=["calculix_results_to_result_dataset"],
            )
            self.add_result_dataset(parser_module.calculix_results_to_result_dataset(parsed))
        except Exception:
            return

    def open_openfoam_template_dialog(self, _checked: bool = False) -> object:
        """Open the safe OpenFOAM template dialog."""

        from osw.gui.dialogs.openfoam_template_dialog import OpenFOAMTemplateDialog

        if self.openfoam_template_dialog is None:
            self.openfoam_template_dialog = OpenFOAMTemplateDialog(
                parent=self,
                theme_tokens=self.theme_manager.current_tokens,
            )
            self.openfoam_template_dialog.caseGenerated.connect(
                self._on_openfoam_case_generated
            )
            self.openfoam_template_dialog.openfoamRunCompleted.connect(
                self._on_openfoam_run_completed
            )
        else:
            self.openfoam_template_dialog.set_theme_tokens(self.theme_manager.current_tokens)
        self.openfoam_template_dialog.show()
        self.openfoam_template_dialog.raise_()
        self.openfoam_template_dialog.activateWindow()
        return self.openfoam_template_dialog

    def _on_openfoam_case_generated(self, result: object) -> None:
        if hasattr(self.run_monitor, "append_log"):
            self.run_monitor.append_log(
                f"Generated OpenFOAM template case: {getattr(result, 'case_dir', '')}",
                level="info",
            )

    def _on_openfoam_run_completed(self, result: object) -> None:
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        if hasattr(self.run_monitor, "append_log"):
            self.run_monitor.append_log(f"OpenFOAM run: {status}", level="info")
            summary = getattr(result, "residual_summary", None)
            if summary is not None and getattr(summary, "final_residuals", None):
                residuals = ", ".join(
                    f"{field} {float(value):.3g}"
                    for field, value in sorted(summary.final_residuals.items())
                )
                self.run_monitor.append_log(
                    f"OpenFOAM residuals: {residuals}",
                    level="info",
                )
        try:
            result_module = __import__(
                "osw.solvers.openfoam.results",
                fromlist=["result_dataset_from_openfoam_run"],
            )
            dataset = result_module.result_dataset_from_openfoam_run(result)
        except Exception:
            return
        self.add_result_dataset(dataset)

    def open_chm_property_dialog(self, _checked: bool = False) -> object:
        """Open the bounded CoolProp property dialog without running external tools."""

        from osw.gui.dialogs.chm_property_dialog import ChmPropertyDialog

        if self.chm_property_dialog is None:
            self.chm_property_dialog = ChmPropertyDialog(
                parent=self,
                theme_tokens=self.theme_manager.current_tokens,
            )
            self.chm_property_dialog.resultDatasetReady.connect(self._on_chm_dataset_ready)
            self.chm_property_dialog.propertyCalculated.connect(self._on_chm_property_result)
        else:
            self.chm_property_dialog.set_theme_tokens(self.theme_manager.current_tokens)
        self.chm_property_dialog.show()
        self.chm_property_dialog.raise_()
        self.chm_property_dialog.activateWindow()
        return self.chm_property_dialog

    def open_chm_reactor_dialog(self, _checked: bool = False) -> object:
        """Open the bounded Cantera 0D reactor dialog without external processes."""

        from osw.gui.dialogs.chm_reactor_dialog import ChmReactorDialog

        if self.chm_reactor_dialog is None:
            self.chm_reactor_dialog = ChmReactorDialog(
                parent=self,
                theme_tokens=self.theme_manager.current_tokens,
            )
            self.chm_reactor_dialog.resultDatasetReady.connect(self._on_chm_dataset_ready)
            self.chm_reactor_dialog.reactorRunCompleted.connect(self._on_chm_reactor_result)
        else:
            self.chm_reactor_dialog.set_theme_tokens(self.theme_manager.current_tokens)
        self.chm_reactor_dialog.show()
        self.chm_reactor_dialog.raise_()
        self.chm_reactor_dialog.activateWindow()
        return self.chm_reactor_dialog

    def _on_chm_dataset_ready(self, dataset: object) -> None:
        self.add_result_dataset(dataset)
        if hasattr(self.run_monitor, "append_log"):
            dataset_id = str(getattr(dataset, "dataset_id", "chm-result"))
            self.run_monitor.append_log(f"CHM ResultDataset ready: {dataset_id}", level="info")

    def _on_chm_property_result(self, result: object) -> None:
        if not hasattr(self.run_monitor, "append_log"):
            return
        status = str(getattr(result, "status", ""))
        value_count = len(getattr(result, "values", ()) or ())
        self.run_monitor.append_log(
            f"CoolProp property calculation: {status}, {value_count} value(s).",
            level="info",
        )

    def _on_chm_reactor_result(self, result: object) -> None:
        if not hasattr(self.run_monitor, "append_log"):
            return
        status = str(getattr(result, "status", ""))
        samples = len(getattr(result, "times", ()) or ())
        self.run_monitor.append_log(
            f"Cantera reactor calculation: {status}, {samples} sample(s).",
            level="info",
        )

    def _on_script_run_completed(self, result: object) -> None:
        status = getattr(getattr(result, "status", ""), "value", getattr(result, "status", ""))
        from osw.scripts.mscript.figure_capture import figure_dataset_from_octave_result

        figure_dataset = figure_dataset_from_octave_result(result)
        self._on_figure_dataset_ready(figure_dataset)
        if hasattr(self.run_monitor, "append_log"):
            self.run_monitor.append_log(f"Octave script result: {status}", level="info")
            combined = str(getattr(result, "combined_log", "") or "").strip()
            if combined:
                self.run_monitor.append_log(combined.splitlines()[-1], level="info")
            figure_count = len(getattr(figure_dataset, "figures", ()))
            if figure_count:
                self.run_monitor.append_log(
                    f"Captured {figure_count} figure artifact(s).",
                    level="info",
                )

    def _on_figure_dataset_ready(self, dataset: object) -> None:
        self.last_figure_dataset = dataset
        if self.plot_viewer is not None and hasattr(self.plot_viewer, "set_figure_dataset"):
            self.plot_viewer.set_figure_dataset(dataset)
        self.refresh_results_from_project(update_report=False)
        self.generate_report_preview(log=False)

    def set_result_catalog(self, catalog: object) -> None:
        """Set the current result catalog without executing solvers or scripts."""

        self.result_catalog = catalog
        if self.result_viewer is not None and hasattr(self.result_viewer, "set_result_catalog"):
            self.result_viewer.set_result_catalog(catalog)
        self.generate_report_preview(log=False)

    def current_result_catalog(self) -> object | None:
        return self.result_catalog

    def add_result_dataset(self, dataset: object) -> None:
        """Append a structured ResultDataset and refresh safe viewer/report state."""

        self.last_result_datasets = (*self.last_result_datasets, dataset)
        catalog = self.refresh_results_from_project(update_report=False)
        if hasattr(catalog, "to_dict"):
            from osw.core.result_dataset import ResultCatalog

            catalog = ResultCatalog(
                catalog_id=getattr(catalog, "catalog_id", ""),
                project_name=getattr(catalog, "project_name", ""),
                datasets=getattr(catalog, "datasets", ()),
                selected_dataset_id=str(getattr(dataset, "dataset_id", "")),
                diagnostics=getattr(catalog, "diagnostics", ()),
                metadata=getattr(catalog, "metadata", {}),
            )
        self.set_result_catalog(catalog)

    def refresh_results_from_project(self, *, update_report: bool = True) -> object:
        """Refresh the result catalog from project summaries and cached datasets."""

        from osw.post.result_view_model import result_catalog_from_project

        figure_datasets = (
            (self.last_figure_dataset,)
            if self.last_figure_dataset is not None
            else ()
        )
        catalog = result_catalog_from_project(
            self.current_project,
            extra_datasets=self.last_result_datasets,
            figure_datasets=figure_datasets,
        )
        self.result_catalog = catalog
        if self.result_viewer is not None and hasattr(self.result_viewer, "set_result_catalog"):
            self.result_viewer.set_result_catalog(catalog)
        if update_report:
            self.generate_report_preview(log=False)
        return catalog

    def open_result_viewer(self, _checked: bool = False) -> object:
        """Open the unified result viewer without executing external tools."""

        from osw.gui.result_viewer import ResultViewer

        if self.result_catalog is None:
            self.refresh_results_from_project(update_report=False)
        if self.result_viewer_dialog is None:
            self.result_viewer_dialog = QtWidgets.QDialog(self)
            self.result_viewer_dialog.setObjectName("oswResultViewerDialog")
            self.result_viewer_dialog.setWindowTitle("Result Viewer")
            layout = QtWidgets.QVBoxLayout(self.result_viewer_dialog)
            self.result_viewer = ResultViewer(self.result_viewer_dialog)
            layout.addWidget(self.result_viewer)
            if hasattr(self.result_viewer, "set_theme_tokens"):
                self.result_viewer.set_theme_tokens(self.theme_manager.current_tokens)
        if self.result_catalog is not None and hasattr(self.result_viewer, "set_result_catalog"):
            self.result_viewer.set_result_catalog(self.result_catalog)
        self.result_viewer_dialog.show()
        self.result_viewer_dialog.raise_()
        self.result_viewer_dialog.activateWindow()
        return self.result_viewer_dialog

    def open_plot_viewer(self, dataset: object | None = None) -> object:
        """Open a lightweight FigureDataset viewer without running scripts."""

        from osw.gui.plot_viewer import PlotViewer

        active_dataset = dataset or self.last_figure_dataset
        if self.plot_viewer_dialog is None:
            self.plot_viewer_dialog = QtWidgets.QDialog(self)
            self.plot_viewer_dialog.setObjectName("oswPlotViewerDialog")
            self.plot_viewer_dialog.setWindowTitle("Plot Viewer")
            layout = QtWidgets.QVBoxLayout(self.plot_viewer_dialog)
            self.plot_viewer = PlotViewer(self.plot_viewer_dialog)
            layout.addWidget(self.plot_viewer)
        if active_dataset is not None and hasattr(self.plot_viewer, "set_figure_dataset"):
            self.plot_viewer.set_figure_dataset(active_dataset)
        self.plot_viewer_dialog.show()
        self.plot_viewer_dialog.raise_()
        self.plot_viewer_dialog.activateWindow()
        return self.plot_viewer_dialog

    def open_mesh_viewer(self, _checked: bool = False) -> object:
        """Open the 3D mesh preview dialog without executing external tools.

        The panel renders only through its injected scene adapter (a fake in
        tests, the panel's lazy PyVista-backed default in production), so this
        seam introduces no solver execution and no import-time PyVista.
        """

        from osw.gui.widgets.mesh_viewer_panel import build_mesh_viewer_panel

        if self.mesh_viewer_dialog is None:
            self.mesh_viewer_dialog = QtWidgets.QDialog(self)
            self.mesh_viewer_dialog.setObjectName("oswMeshViewerDialog")
            self.mesh_viewer_dialog.setWindowTitle("3D Mesh Preview")
            layout = QtWidgets.QVBoxLayout(self.mesh_viewer_dialog)
            adapter = (
                self._mesh_scene_adapter_factory()
                if self._mesh_scene_adapter_factory is not None
                else None
            )
            self.mesh_viewer = build_mesh_viewer_panel(
                self.mesh_viewer_dialog, scene_adapter=adapter
            )
            layout.addWidget(self.mesh_viewer)
            if hasattr(self.mesh_viewer, "set_theme_tokens"):
                self.mesh_viewer.set_theme_tokens(self.theme_manager.current_tokens)
        self._populate_mesh_viewer_from_latest()
        self.mesh_viewer_dialog.show()
        self.mesh_viewer_dialog.raise_()
        self.mesh_viewer_dialog.activateWindow()
        return self.mesh_viewer_dialog

    def _populate_mesh_viewer_from_latest(self) -> None:
        """Show the latest imported mesh when the preview panel has none yet.

        Runs on open so the first open after an import displays that mesh, but it
        never clobbers a mesh the panel already holds (a manual load or a prior
        refresh), keeping ``latest wins`` idempotent.
        """

        if (
            self.mesh_viewer is not None
            and self.last_imported_mesh_data is not None
            and hasattr(self.mesh_viewer, "set_mesh")
            and hasattr(self.mesh_viewer, "current_state")
            and self.mesh_viewer.current_state().mesh is None
        ):
            self.mesh_viewer.set_mesh(
                self.last_imported_mesh_data,
                mesh_ref=self.last_imported_mesh_ref or "",
            )

    def load_mesh_into_viewer(self, mesh: object, *, mesh_ref: str = "") -> object:
        """Show the mesh preview dialog and hand it an already-built mesh.

        This receives MeshData that existing import/workflow state already
        produced; it neither generates, parses, nor converts meshes.
        """

        self.open_mesh_viewer()
        if self.mesh_viewer is not None and hasattr(self.mesh_viewer, "set_mesh"):
            self.mesh_viewer.set_mesh(mesh, mesh_ref=mesh_ref)
        return self.mesh_viewer_dialog

    def _on_plugin_state_changed(self, _plugin_id: str, _enabled: bool) -> None:
        self.run_plugin_health_check(log=False)

    def _on_executable_paths_changed(self) -> None:
        self.run_plugin_health_check(log=False)

    def _placeholder_action(self, label: str) -> None:
        if hasattr(self.run_monitor, "append_log"):
            self.run_monitor.append_log(f"{label} action selected", level="info")

    def _result_datasets_for_report(self) -> tuple[object, ...]:
        if self.result_catalog is not None:
            datasets = getattr(self.result_catalog, "datasets", ())
            if datasets:
                return tuple(datasets)
        return tuple(self.last_result_datasets)


def _action_object_name(action_title: str) -> str:
    plugin_action_names = {
        "Plugin Manager": "oswActionPluginManager",
        "Refresh Plugins": "oswActionRefreshPlugins",
        "Plugin Health Check": "oswActionPluginHealthCheck",
        "Import MATLAB MAT Data": "oswActionImportMatData",
        "Generate Mesh with Gmsh...": "oswActionGenerateGmshMesh",
        "Generate CalculiX Input Deck...": "oswActionGenerateCalculixDeck",
        "Generate OpenFOAM Template Case...": "oswActionGenerateOpenFOAMTemplate",
        "CoolProp Property Calculator...": "oswActionCoolPropPropertyCalculator",
        "Cantera 0D Reactor...": "oswActionCanteraReactor",
    }
    if action_title in plugin_action_names:
        return plugin_action_names[action_title]
    words = "".join(part.capitalize() for part in action_title.replace("/", " ").split())
    return f"action{words}"


def _project_with_mesh_ref(project: Project, mesh_ref: object) -> Project:
    meshes = [
        mesh
        for mesh in project.mesh_refs
        if getattr(mesh, "id", "") != getattr(mesh_ref, "id", "")
        and getattr(mesh, "path", "") != getattr(mesh_ref, "path", "")
    ]
    meshes.append(mesh_ref)
    return Project(
        metadata=project.metadata,
        units=project.units,
        materials=project.materials,
        geometry=project.geometry,
        meshes=meshes,
        scripts=project.scripts,
        boundary_curves=project.boundary_curves,
        physics=project.physics,
        solvers=project.solvers,
        results=project.results,
        report=project.report,
        schema_version=project.schema_version,
        plugins=project.plugins,
        warnings=project.warnings,
    )


def _project_with_script_ref(project: Project, script_ref: object) -> Project:
    scripts = [
        script
        for script in project.script_refs
        if getattr(script, "id", "") != getattr(script_ref, "id", "")
        and getattr(script, "path", "") != getattr(script_ref, "path", "")
    ]
    scripts.append(script_ref)
    return Project(
        metadata=project.metadata,
        units=project.units,
        materials=project.materials,
        geometry=project.geometry,
        meshes=project.meshes,
        scripts=scripts,
        boundary_curves=project.boundary_curves,
        physics=project.physics,
        solvers=project.solvers,
        results=project.results,
        report=project.report,
        schema_version=project.schema_version,
        plugins=project.plugins,
        warnings=project.warnings,
    )


def _project_with_boundary_curve(project: Project, curve: object) -> Project:
    curves = [
        item
        for item in project.boundary_curves
        if getattr(item, "curve_id", "") != getattr(curve, "curve_id", "")
    ]
    curves.append(curve)
    return Project(
        metadata=project.metadata,
        units=project.units,
        materials=project.materials,
        geometry=project.geometry,
        meshes=project.meshes,
        scripts=project.scripts,
        boundary_curves=curves,
        physics=project.physics,
        solvers=project.solvers,
        results=project.results,
        report=project.report,
        schema_version=project.schema_version,
        plugins=project.plugins,
        warnings=project.warnings,
    )


def _result_tables_from_datasets(datasets: Sequence[object]) -> tuple[object, ...]:
    tables: list[object] = []
    for dataset in datasets:
        to_report_tables = getattr(dataset, "to_report_tables", None)
        if callable(to_report_tables):
            tables.extend(to_report_tables())
    return tuple(tables)


def _default_report_export_path(project: Project) -> Path:
    name = project.metadata.name or "osw_project"
    safe_name = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in name)
    return Path("artifacts") / "report" / f"{safe_name}_report.html"


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
