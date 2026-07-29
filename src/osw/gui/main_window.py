"""PySide6 main window shell for OSW."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.executables import ExecutablePathRegistry
from osw.core.project_schema import Project, project_with
from osw.core.report_asset import ReportAssetPathKind
from osw.gui.project_document_context import (
    ProjectDocumentContext,
    ProjectDocumentOrigin,
)
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme import ThemeManager
from osw.gui.widgets.top_bar import ACTION_OBJECT_NAMES, TOP_BAR_ACTION_LABELS
from osw.gui.widgets.workflow_stepper import WORKFLOW_STEP_LABELS as _WORKFLOW_STEP_LABELS
from osw.plugins.registry import PluginRegistry
from osw.plugins.state import PluginStateStore

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication

    from osw.post.scene_model import SceneScreenshotRecord

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
        "Load mesh data for selected mesh...",
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
_PERSISTED_CAPTION_NOT_SUPPLIED = object()
_PERSISTED_SCREENSHOT_STALE_TEXT = (
    "The selected persisted screenshot is stale or no longer available."
)
_PERSISTED_SCREENSHOT_FILE_FILTER = (
    "Image Files (*.png *.jpg *.jpeg *.webp *.gif)"
)
_PERSISTED_SCREENSHOT_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})


def _relinked_report_screenshot_path_kind(
    current: ReportAssetPathKind | None,
) -> ReportAssetPathKind | None:
    if current is ReportAssetPathKind.PROJECT_RELATIVE:
        return ReportAssetPathKind.EXTERNAL_ABSOLUTE
    return current


def _relinked_report_screenshot_path_kind_confirmation(
    current: ReportAssetPathKind | None,
) -> str:
    if current is None:
        return "Path reference kind remains unmarked."
    if current is ReportAssetPathKind.PROJECT_RELATIVE:
        return (
            "Path reference kind will change from project_relative to "
            "external_absolute.\n"
            "The selected file will be stored as an external absolute reference."
        )
    return f"Path reference kind remains {current.value}."


@dataclass(frozen=True)
class ResultMeshBindingTargetCandidate:
    """A non-mutating persisted ResultRef target option for result/mesh binding."""

    index: int
    result_ref: object
    reason: str
    label: str
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class SelectedMeshContext:
    """Transient GUI-only active mesh context selected from project navigation."""

    mesh_ref: str
    label: str
    source: str
    mesh: object | None = None
    diagnostics: tuple[str, ...] = ()
    payload: Mapping[str, str] | None = None


@dataclass(frozen=True)
class MetadataMeshLoadState:
    """Transient GUI-only state for an explicit metadata MeshRef load."""

    operation_id: int
    mesh_ref: str
    label: str
    selected_path: Path
    payload: Mapping[str, str]
    status: str
    message: str
    diagnostics: tuple[str, ...] = ()
    cancel_requested: bool = False


ResultMeshBindingTargetSelector = Callable[
    [Sequence[ResultMeshBindingTargetCandidate]], object | None
]
MeshRefLoadReader = Callable[[str | Path], object]
MeshRefLoadFilePicker = Callable[[], str | Path | None]
ProjectFilePathPicker = Callable[[], str | Path | None]
ProjectLoader = Callable[[str], Project]
ProjectSaver = Callable[[Project, str], None]
ProjectFileErrorReporter = Callable[[str], None]

_DOCUMENT_DIALOG_ATTRIBUTES = (
    "script_preview_dialog",
    "mat_preview_dialog",
    "boundary_curve_dialog",
    "gmsh_mesh_dialog",
    "calculix_deck_dialog",
    "openfoam_template_dialog",
    "chm_property_dialog",
    "chm_reactor_dialog",
    "result_viewer_dialog",
    "plot_viewer_dialog",
    "mesh_viewer_dialog",
)
_DOCUMENT_VIEWER_ATTRIBUTES = (
    "result_viewer",
    "plot_viewer",
    "mesh_viewer",
)
_DOCUMENT_SURFACE_ATTRIBUTES = (
    *_DOCUMENT_DIALOG_ATTRIBUTES,
    *_DOCUMENT_VIEWER_ATTRIBUTES,
)


@dataclass(frozen=True)
class _ProjectDocumentStateSnapshot:
    project: Project
    context: ProjectDocumentContext
    document_binding_epoch: int
    workflow_project: Project
    workflow_items: object
    workflow_mesh_infos: object
    workflow_result_tables: object
    workflow_figure_datasets: object
    workflow_warnings: object
    last_imported_mesh_data: object | None
    last_imported_mesh_ref: str | None
    selected_mesh_context: object | None
    mesh_data_by_ref: object
    result_catalog: object | None
    last_figure_dataset: object | None
    last_result_datasets: tuple[object, ...]
    scene_screenshot_candidates: tuple[object, ...]
    metadata_mesh_load_state: object | None
    last_persisted_screenshot_status: str
    run_log: str
    monitor_warnings: tuple[str, ...]
    monitor_progress: int
    report_summary: object | None
    document_surfaces: tuple[tuple[str, object | None], ...]


if QtCore is not None:

    class _MetadataMeshLoadWorker(QtCore.QObject):  # type: ignore[misc]
        """Run the injected mesh reader away from the GUI thread."""

        finished = QtCore.Signal(int, object)

        def __init__(
            self,
            operation_id: int,
            path: Path,
            reader: MeshRefLoadReader,
        ) -> None:
            super().__init__()
            self._operation_id = operation_id
            self._path = path
            self._reader = reader

        @QtCore.Slot()
        def run(self) -> None:
            try:
                result = self._reader(self._path)
            except Exception as exc:  # pragma: no cover - defensive seam
                result = SimpleNamespace(
                    mesh=None,
                    diagnostics=(f"MeshData load failed: {exc}",),
                    format="",
                )
            self.finished.emit(self._operation_id, result)

else:
    _MetadataMeshLoadWorker = None


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
        scene_renderer_factory: Any | None = None,
        result_mesh_binding_confirmation: Callable[[str], bool] | None = None,
        result_mesh_binding_target_selector: ResultMeshBindingTargetSelector | None = None,
        metadata_mesh_reader: MeshRefLoadReader | None = None,
        metadata_mesh_file_picker: MeshRefLoadFilePicker | None = None,
        metadata_mesh_load_async: bool | None = None,
        project_open_path_picker: ProjectFilePathPicker | None = None,
        project_save_path_picker: ProjectFilePathPicker | None = None,
        project_loader: ProjectLoader | None = None,
        project_saver: ProjectSaver | None = None,
        project_error_reporter: ProjectFileErrorReporter | None = None,
        setup_preview_provider: Callable[[Project, object, str], object] | None = None,
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
        self._project_document_context = ProjectDocumentContext()
        self._document_binding_epoch = 0
        self._project_open_path_picker = (
            project_open_path_picker or self._choose_project_open_path
        )
        self._project_save_path_picker = (
            project_save_path_picker or self._choose_project_save_path
        )
        self._project_loader = project_loader or self._load_project_file
        self._project_saver = project_saver or self._save_project_file
        self._project_error_reporter = (
            project_error_reporter or self._show_project_file_error
        )
        self._setup_preview_provider = setup_preview_provider
        self._project_dirty = False
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
        self.persisted_report_screenshot_manager: object | None = None
        self._last_persisted_report_screenshot_status = ""
        self._mesh_scene_adapter_factory = mesh_scene_adapter_factory
        self._scene_renderer_factory = scene_renderer_factory
        self.active_scene_controller = self._create_active_scene_controller()
        self._result_mesh_binding_confirmation = result_mesh_binding_confirmation
        self._result_mesh_binding_target_selector = result_mesh_binding_target_selector
        self._metadata_mesh_reader = metadata_mesh_reader or self._read_metadata_mesh
        self._metadata_mesh_file_picker = (
            metadata_mesh_file_picker or self._choose_metadata_mesh_file
        )
        self._metadata_mesh_load_async = (
            metadata_mesh_reader is None
            if metadata_mesh_load_async is None
            else bool(metadata_mesh_load_async)
        )
        self._metadata_mesh_load_next_id = 0
        self._metadata_mesh_load_state: MetadataMeshLoadState | None = None
        self._metadata_mesh_load_thread: object | None = None
        self._metadata_mesh_load_worker: object | None = None
        self.last_imported_mesh_data: object | None = None
        self.last_imported_mesh_ref: str | None = None
        self.selected_mesh_context: SelectedMeshContext | None = None
        self._mesh_data_by_ref: dict[str, object] = {}
        self.result_catalog: object | None = None
        self.last_figure_dataset: object | None = None
        self.last_result_datasets: tuple[object, ...] = ()
        self._scene_screenshot_candidates: tuple[SceneScreenshotRecord, ...] = ()
        self._scene_screenshot_counter: int = 0
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
                elif action_title == "Open Project":
                    action.triggered.connect(self.open_project)
                elif action_title == "Save Project":
                    action.triggered.connect(self.save_project)
                elif action_title == "Save Project As":
                    action.triggered.connect(self.save_project_as)
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
                elif action_title == "Load mesh data for selected mesh...":
                    action.setObjectName("oswActionLoadSelectedMeshData")
                    action.triggered.connect(self.load_selected_project_tree_mesh_data)
                else:
                    action.triggered.connect(
                        lambda _checked=False, label=action_title: self._placeholder_action(label)
                    )

    def _build_shell(self) -> None:
        from osw.gui.widgets.mesh_diagnostics_panel import MeshDiagnosticsPanel
        from osw.gui.widgets.named_selection_panel import NamedSelectionPanel
        from osw.gui.widgets.project_tree_panel import ProjectTreePanel
        from osw.gui.widgets.properties_panel import PropertiesPanel
        from osw.gui.widgets.run_monitor_panel import RunMonitorPanel
        from osw.gui.widgets.setup_overlay_panel import SetupOverlayPanel
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
        self.named_selection_panel = NamedSelectionPanel(container)
        self.setup_overlay_panel = SetupOverlayPanel(container)
        self.mesh_diagnostics_panel = MeshDiagnosticsPanel(container)
        self.central_viewport_panel = CentralViewportPanel(
            container,
            scene_controller=self.active_scene_controller,
        )
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
        self.named_selection_panel.pickModeChanged.connect(
            self._on_entity_pick_mode_changed
        )
        self.named_selection_panel.clearRequested.connect(
            self._on_clear_current_selection
        )
        self.named_selection_panel.createRequested.connect(
            self._on_create_named_selection
        )
        self.named_selection_panel.renameRequested.connect(
            self._on_rename_named_selection
        )
        self.named_selection_panel.replaceRequested.connect(
            self._on_replace_named_selection_targets
        )
        self.named_selection_panel.deleteRequested.connect(
            self._on_delete_named_selection
        )
        self.named_selection_panel.selectionActivated.connect(
            self._on_named_selection_activated
        )
        self.setup_overlay_panel.createRequested.connect(
            self._on_create_setup_record
        )
        self.setup_overlay_panel.editRequested.connect(
            self._on_edit_setup_record
        )
        self.setup_overlay_panel.deleteRequested.connect(
            self._on_delete_setup_record
        )
        self.setup_overlay_panel.recordSelected.connect(
            self._on_setup_record_selected
        )
        self.setup_overlay_panel.categoryVisibilityChanged.connect(
            self._on_setup_category_visibility_changed
        )
        self.setup_overlay_panel.preparePreviewRequested.connect(
            self._on_prepare_setup_preview
        )
        self.mesh_diagnostics_panel.analyzeRequested.connect(
            self._on_mesh_diagnostics_analyze
        )
        self.mesh_diagnostics_panel.thresholdChanged.connect(
            self._on_mesh_diagnostics_threshold_changed
        )
        self.mesh_diagnostics_panel.highlightToggled.connect(
            self._on_mesh_diagnostics_highlight_toggled
        )
        self.mesh_diagnostics_panel.isolateToggled.connect(
            self._on_mesh_diagnostics_isolate_toggled
        )
        self.mesh_diagnostics_panel.restoreRequested.connect(
            self._on_mesh_diagnostics_restore
        )
        self.mesh_diagnostics_panel.clearRequested.connect(
            self._on_mesh_diagnostics_clear
        )
        self.active_scene_controller.set_selection_listener(
            self._refresh_named_selection_panel
        )
        picking_available = bool(
            getattr(self.central_viewport_panel, "interactive_available", False)
            and "picking" in self.active_scene_controller.capabilities
        )
        self.named_selection_panel.set_backend_available(
            picking_available,
            getattr(self.active_scene_controller, "fallback_reason", ""),
        )
        if picking_available:
            self.active_scene_controller.set_pick_mode(
                self.named_selection_panel.mode_selector.currentText().lower()
            )

        center_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical, container)
        center_splitter.setObjectName("oswCenterVerticalSplitter")
        center_splitter.addWidget(self.central_viewport_panel)
        center_splitter.addWidget(self.run_monitor)
        center_splitter.setStretchFactor(0, 3)
        center_splitter.setStretchFactor(1, 2)
        center_splitter.setSizes([690, 350])

        main_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, container)
        main_splitter.setObjectName("oswMainHorizontalSplitter")
        left_splitter = QtWidgets.QSplitter(
            QtCore.Qt.Orientation.Vertical,
            container,
        )
        left_splitter.setObjectName("oswProjectSelectionVerticalSplitter")
        left_splitter.addWidget(self.project_tree_panel)
        left_splitter.addWidget(self.named_selection_panel)
        left_splitter.addWidget(self.setup_overlay_panel)
        left_splitter.addWidget(self.mesh_diagnostics_panel)
        left_splitter.setStretchFactor(0, 2)
        left_splitter.setStretchFactor(1, 1)
        left_splitter.setStretchFactor(2, 1)
        left_splitter.setStretchFactor(3, 1)
        left_splitter.setSizes([420, 220, 260, 340])
        main_splitter.addWidget(left_splitter)
        main_splitter.addWidget(center_splitter)
        main_splitter.addWidget(self.properties_panel)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)
        main_splitter.setStretchFactor(2, 0)
        main_splitter.setSizes([320, 1290, 438])

        container_layout.addWidget(main_splitter, 1)
        self.setCentralWidget(container)

    def _build_toolbar_actions(self) -> None:
        lifecycle_handlers = {
            "New": self.new_project,
            "Open": self.open_project,
            "Save": self.save_project,
            "Save As": self.save_project_as,
        }
        for title in TOOLBAR_ACTION_TITLES:
            action = QtGui.QAction(title, self)
            action.setObjectName(ACTION_OBJECT_NAMES[title])
            self.main_toolbar.addAction(action)
            self.toolbar_actions[title] = action
            if title in lifecycle_handlers:
                action.triggered.connect(lifecycle_handlers[title])
            elif title == "Preferences":
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
        if label == "Open":
            self.open_project()
            return
        if label == "Save":
            self.save_project()
            return
        if label == "Save As":
            self.save_project_as()
            return
        if label == "Preferences":
            self.open_preferences()
            return
        self._placeholder_action(label)

    def _on_project_tree_selection_changed(self, current: object, _previous: object) -> None:
        if current is not None and hasattr(self.properties_panel, "set_node_selection"):
            self.properties_panel.set_node_selection(current.text(0))
        self._handle_project_tree_mesh_selection(current)

    def _handle_project_tree_mesh_selection(self, current: object | None) -> None:
        if current is None:
            return
        kind = str(current.data(0, QtCore.Qt.ItemDataRole.UserRole) or "")
        icon_key = str(current.data(0, QtCore.Qt.ItemDataRole.UserRole + 1) or "")
        payload = self._project_tree_item_payload(current)
        if not _is_project_tree_mesh_item(kind, icon_key, payload):
            return

        label = str(current.text(0) or "")
        mesh_ref = _selected_mesh_ref(payload, label)
        mesh = self._mesh_data_for_project_tree_payload(payload, label)
        if mesh is None:
            diagnostic = (
                f"Project tree mesh '{label or mesh_ref}' is registered but no "
                "in-memory MeshData is available for 3D preview."
            )
            context = SelectedMeshContext(
                mesh_ref=mesh_ref,
                label=label,
                source="project_tree",
                diagnostics=(diagnostic,),
                payload=payload,
            )
            self.selected_mesh_context = context
            self._show_selected_mesh_context_status(context)
            return

        context = SelectedMeshContext(
            mesh_ref=mesh_ref,
            label=label,
            source="project_tree",
            mesh=mesh,
            payload=payload,
        )
        self.selected_mesh_context = context
        self._apply_selected_mesh_context_to_viewer(context)

    def _project_tree_item_payload(self, item: object) -> dict[str, str]:
        if hasattr(self.project_tree_panel, "item_payload"):
            return self.project_tree_panel.item_payload(item)
        payload = item.data(0, QtCore.Qt.ItemDataRole.UserRole + 2)
        if not isinstance(payload, dict):
            return {}
        return {str(key): str(value) for key, value in payload.items()}

    def _mesh_data_for_project_tree_payload(
        self,
        payload: Mapping[str, str],
        label: str,
    ) -> object | None:
        for alias in _mesh_ref_aliases((*payload.values(), label)):
            mesh = self._mesh_data_by_ref.get(alias)
            if mesh is not None:
                return mesh
        return None

    def _register_mesh_data_for_viewer(
        self,
        mesh_data: object,
        aliases: Sequence[str],
    ) -> None:
        for alias in _mesh_ref_aliases(aliases):
            self._mesh_data_by_ref[alias] = mesh_data

    def _refresh_selected_mesh_context_from_aliases(
        self,
        mesh_data: object,
        aliases: Sequence[str],
    ) -> SelectedMeshContext | None:
        context = self.selected_mesh_context
        if context is None:
            return None
        alias_set = set(_mesh_ref_aliases(aliases))
        context_aliases = set(
            _mesh_ref_aliases(
                (
                    context.mesh_ref,
                    context.label,
                    *(context.payload or {}).values(),
                )
            )
        )
        if not alias_set.intersection(context_aliases):
            return context
        refreshed = SelectedMeshContext(
            mesh_ref=context.mesh_ref,
            label=context.label,
            source=context.source,
            mesh=mesh_data,
            payload=context.payload,
        )
        self.selected_mesh_context = refreshed
        return refreshed

    def _apply_selected_mesh_context_to_viewer(self, context: SelectedMeshContext) -> None:
        if (
            context.mesh is not None
            and getattr(self.central_viewport_panel, "interactive_available", False)
            and hasattr(self.central_viewport_panel, "set_mesh")
        ):
            self.central_viewport_panel.set_mesh(
                context.mesh,
                mesh_ref=context.mesh_ref,
            )
        if context.mesh is not None and self.mesh_viewer is not None and hasattr(
            self.mesh_viewer, "set_mesh"
        ):
            self.mesh_viewer.set_mesh(context.mesh, mesh_ref=context.mesh_ref)
            self._sync_mesh_viewer_result_datasets()
        self._refresh_mesh_diagnostics_panel()
        self._show_selected_mesh_context_status(context)

    def _show_selected_mesh_context_status(self, context: SelectedMeshContext) -> None:
        if context.mesh is None:
            message = (
                context.diagnostics[0]
                if context.diagnostics
                else f"Project tree mesh '{context.label}' is metadata-only."
            )
            diagnostics = context.diagnostics
        else:
            if context.source == "project_tree_load":
                message = (
                    f"Loaded project tree mesh '{context.label or context.mesh_ref}' "
                    "for 3D preview."
                )
            else:
                message = (
                    f"Selected project tree mesh '{context.label or context.mesh_ref}' "
                    "for 3D preview."
                )
            diagnostics = context.diagnostics
        if self.mesh_viewer is not None and hasattr(
            self.mesh_viewer, "show_active_mesh_status"
        ):
            self.mesh_viewer.show_active_mesh_status(message, diagnostics)
        self._placeholder_action(message)

    def load_selected_project_tree_mesh_data(
        self,
        path: str | Path | None = None,
    ) -> bool:
        """Explicitly load MeshData for the selected project-tree MeshRef.

        Passive project-tree selection stays diagnostic-only. This route reads a
        user-selected or payload-provided neutral mesh file through a non-throwing
        reader seam and updates only transient GUI preview state.
        """

        if self._metadata_mesh_load_in_flight():
            state = self._metadata_mesh_load_state
            target = ""
            if state is not None:
                target = state.label or state.mesh_ref
            return self._show_metadata_mesh_load_status(
                f"MeshData load is already in progress for '{target or 'selected mesh'}'.",
                (
                    "Wait for the current load to finish or request cancellation "
                    "before starting another mesh load.",
                ),
            )

        current = self.project_tree.currentItem()
        if current is None:
            return self._show_metadata_mesh_load_status(
                "Select a project-tree mesh before loading mesh data."
            )

        kind = str(current.data(0, QtCore.Qt.ItemDataRole.UserRole) or "")
        icon_key = str(current.data(0, QtCore.Qt.ItemDataRole.UserRole + 1) or "")
        payload = self._project_tree_item_payload(current)
        if not _is_project_tree_mesh_item(kind, icon_key, payload):
            return self._show_metadata_mesh_load_status(
                "Select a mesh row before loading MeshData for 3D preview."
            )

        label = str(current.text(0) or "")
        mesh_ref = _selected_mesh_ref(payload, label)
        if not mesh_ref:
            return self._show_metadata_mesh_load_status(
                "Selected mesh row has no stable mesh ref; MeshData was not loaded."
            )

        source_path = _metadata_mesh_source_path(payload)
        selected_path = self._metadata_mesh_load_path(
            explicit_path=path,
            source_path=source_path,
        )
        if selected_path is None:
            diagnostics = _metadata_mesh_missing_path_diagnostics(source_path)
            context = SelectedMeshContext(
                mesh_ref=mesh_ref,
                label=label,
                source="project_tree",
                diagnostics=diagnostics,
                payload=payload,
            )
            self.selected_mesh_context = context
            self._show_selected_mesh_context_status(context)
            return False

        state = self._begin_metadata_mesh_load(
            mesh_ref=mesh_ref,
            label=label,
            payload=payload,
            selected_path=selected_path,
        )
        if self._metadata_mesh_load_async:
            self._start_metadata_mesh_load_worker(state)
            return True

        result = self._read_metadata_mesh_for_operation(selected_path)
        return self._finish_metadata_mesh_load(state.operation_id, result)

    def cancel_selected_project_tree_mesh_load(self) -> bool:
        """Request cooperative cancellation before committing loaded MeshData."""

        state = self._metadata_mesh_load_state
        if state is None or not self._metadata_mesh_load_in_flight():
            return self._show_metadata_mesh_load_status(
                "No metadata mesh load is in progress."
            )
        if state.cancel_requested:
            target = state.label or state.mesh_ref
            return self._show_metadata_mesh_load_status(
                f"MeshData load cancellation is already requested for '{target}'.",
                state.diagnostics,
            )

        canceled = replace(
            state,
            status="cancel_requested",
            cancel_requested=True,
            message=(
                f"Cancel requested for mesh data load '{state.label or state.mesh_ref}'."
            ),
            diagnostics=(
                "The active mesh will remain unchanged when the current read returns.",
            ),
        )
        self._metadata_mesh_load_state = canceled
        self._show_metadata_mesh_load_status(canceled.message, canceled.diagnostics)
        return True

    def _begin_metadata_mesh_load(
        self,
        *,
        mesh_ref: str,
        label: str,
        payload: Mapping[str, str],
        selected_path: Path,
    ) -> MetadataMeshLoadState:
        self._metadata_mesh_load_next_id += 1
        operation_id = self._metadata_mesh_load_next_id
        state = MetadataMeshLoadState(
            operation_id=operation_id,
            mesh_ref=mesh_ref,
            label=label,
            selected_path=selected_path,
            payload=dict(payload),
            status="loading",
            message=f"Loading mesh data for project tree mesh '{label or mesh_ref}'...",
            diagnostics=("Progress is indeterminate; large mesh reads may take time.",),
        )
        self._metadata_mesh_load_state = state
        self._set_metadata_mesh_load_action_enabled(False)
        self._show_metadata_mesh_load_status(state.message, state.diagnostics)
        return state

    def _start_metadata_mesh_load_worker(self, state: MetadataMeshLoadState) -> None:
        if QtCore is None or _MetadataMeshLoadWorker is None:
            result = self._read_metadata_mesh_for_operation(state.selected_path)
            self._finish_metadata_mesh_load(state.operation_id, result)
            return

        thread = QtCore.QThread(self)
        worker = _MetadataMeshLoadWorker(
            state.operation_id,
            state.selected_path,
            self._metadata_mesh_reader,
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._finish_metadata_mesh_load)
        worker.finished.connect(lambda *_args: thread.quit())
        worker.finished.connect(lambda *_args: worker.deleteLater())
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(
            lambda _op=state.operation_id: self._clear_metadata_mesh_worker(_op)
        )
        self._metadata_mesh_load_thread = thread
        self._metadata_mesh_load_worker = worker
        thread.start()

    def _read_metadata_mesh_for_operation(self, selected_path: Path) -> object:
        try:
            return self._metadata_mesh_reader(selected_path)
        except Exception as exc:  # pragma: no cover - defensive GUI seam
            return SimpleNamespace(
                mesh=None,
                diagnostics=(f"MeshData load failed: {exc}",),
                format="",
            )

    def _finish_metadata_mesh_load(self, operation_id: int, result: object) -> bool:
        state = self._metadata_mesh_load_state
        if state is None or state.operation_id != operation_id:
            return False

        if state.cancel_requested:
            return self._complete_canceled_metadata_mesh_load(state)

        if self._current_project_tree_mesh_ref() != state.mesh_ref:
            stale = replace(
                state,
                status="stale",
                message=(
                    "Loaded mesh was not made active because selected project-tree "
                    "mesh changed."
                ),
                diagnostics=(
                    f"Original MeshRef: {state.mesh_ref}",
                    "The active mesh was left unchanged.",
                ),
            )
            self._metadata_mesh_load_state = stale
            self._set_metadata_mesh_load_action_enabled(True)
            return self._show_metadata_mesh_load_status(
                stale.message,
                stale.diagnostics,
            )

        self._set_metadata_mesh_load_action_enabled(True)
        mesh_ref = state.mesh_ref
        label = state.label
        payload = state.payload
        selected_path = state.selected_path
        mesh = getattr(result, "mesh", None)
        if mesh is None:
            diagnostics = _mesh_import_diagnostics(result)
            context = SelectedMeshContext(
                mesh_ref=mesh_ref,
                label=label,
                source="project_tree",
                diagnostics=(
                    f"Could not load MeshData for project tree mesh '{label or mesh_ref}'.",
                    *diagnostics,
                ),
                payload=payload,
            )
            self.selected_mesh_context = context
            self._metadata_mesh_load_state = replace(
                state,
                status="failed",
                message=context.diagnostics[0],
                diagnostics=context.diagnostics,
            )
            self._show_selected_mesh_context_status(context)
            return False

        mismatch_diagnostics = _metadata_mesh_mismatch_diagnostics(
            payload,
            selected_path,
            result,
        )
        if mismatch_diagnostics:
            context = SelectedMeshContext(
                mesh_ref=mesh_ref,
                label=label,
                source="project_tree",
                diagnostics=mismatch_diagnostics,
                payload=payload,
            )
            self.selected_mesh_context = context
            self._metadata_mesh_load_state = replace(
                state,
                status="failed",
                message=mismatch_diagnostics[0],
                diagnostics=mismatch_diagnostics,
            )
            self._show_selected_mesh_context_status(context)
            return False

        mesh_data = mesh.to_mesh_data() if hasattr(mesh, "to_mesh_data") else mesh
        loaded_payload = {**payload, "loaded_path": str(selected_path)}
        aliases = (
            mesh_ref,
            label,
            str(selected_path),
            *payload.values(),
        )
        self._register_mesh_data_for_viewer(mesh_data, aliases)
        context = SelectedMeshContext(
            mesh_ref=mesh_ref,
            label=label,
            source="project_tree_load",
            mesh=mesh_data,
            diagnostics=_mesh_import_diagnostics(result),
            payload=loaded_payload,
        )
        self.selected_mesh_context = context
        self._metadata_mesh_load_state = replace(
            state,
            status="succeeded",
            message=f"Loaded project tree mesh '{label or mesh_ref}' for 3D preview.",
            diagnostics=context.diagnostics,
        )
        self._apply_selected_mesh_context_to_viewer(context)
        return True

    def _complete_canceled_metadata_mesh_load(
        self,
        state: MetadataMeshLoadState,
    ) -> bool:
        canceled = replace(
            state,
            status="canceled",
            message="MeshData load was canceled; the active mesh was not changed.",
            diagnostics=(
                "Cancel was requested before the loaded MeshData could be committed.",
            ),
        )
        self._metadata_mesh_load_state = canceled
        self._set_metadata_mesh_load_action_enabled(True)
        return self._show_metadata_mesh_load_status(
            canceled.message,
            canceled.diagnostics,
        )

    def _metadata_mesh_load_in_flight(self) -> bool:
        state = self._metadata_mesh_load_state
        return state is not None and state.status in {"loading", "cancel_requested"}

    def _clear_metadata_mesh_worker(self, operation_id: int) -> None:
        state = self._metadata_mesh_load_state
        if state is None or state.operation_id == operation_id:
            self._metadata_mesh_load_thread = None
            self._metadata_mesh_load_worker = None

    def _set_metadata_mesh_load_action_enabled(self, enabled: bool) -> None:
        action = self.menu_actions.get("Load mesh data for selected mesh...")
        if action is not None and hasattr(action, "setEnabled"):
            action.setEnabled(enabled)

    def _current_project_tree_mesh_ref(self) -> str:
        current = self.project_tree.currentItem()
        if current is None:
            return ""
        kind = str(current.data(0, QtCore.Qt.ItemDataRole.UserRole) or "")
        icon_key = str(current.data(0, QtCore.Qt.ItemDataRole.UserRole + 1) or "")
        payload = self._project_tree_item_payload(current)
        if not _is_project_tree_mesh_item(kind, icon_key, payload):
            return ""
        label = str(current.text(0) or "")
        return _selected_mesh_ref(payload, label)

    def _metadata_mesh_load_path(
        self,
        *,
        explicit_path: str | Path | None,
        source_path: str,
    ) -> Path | None:
        if explicit_path not in (None, ""):
            return Path(explicit_path)
        if source_path:
            candidate = Path(source_path)
            if candidate.is_absolute():
                return candidate
        picked = self._metadata_mesh_file_picker()
        if picked in (None, ""):
            return None
        return Path(picked)

    def _choose_metadata_mesh_file(self) -> str | None:
        selected, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Load mesh data for selected mesh",
            "",
            "Mesh files (*.msh *.inp *.bdf *.nas *.fem *.su2 *.vtk *.vtu "
            "*.xdmf *.xmf *.cgns *.med);;All files (*)",
        )
        text = str(selected or "").strip()
        return text or None

    def _read_metadata_mesh(self, path: str | Path) -> object:
        from osw.mesh.meshio_bridge import read_mesh

        return read_mesh(path)

    def _show_metadata_mesh_load_status(
        self,
        message: str,
        diagnostics: Sequence[str] = (),
    ) -> bool:
        if self.mesh_viewer is not None and hasattr(
            self.mesh_viewer,
            "show_active_mesh_status",
        ):
            self.mesh_viewer.show_active_mesh_status(message, diagnostics)
        self._placeholder_action(message)
        return False

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

    def project_document_context(self) -> ProjectDocumentContext:
        """Return the immutable file context for this MainWindow document."""

        return self._project_document_context

    def current_project_file_path(self) -> str | None:
        return self._project_document_context.project_file_path

    def current_project_root(self) -> Path | None:
        return self._project_document_context.project_root

    def has_bound_project_file(self) -> bool:
        return self._project_document_context.is_bound

    def _capture_project_document_state(self) -> _ProjectDocumentStateSnapshot:
        monitor = self.run_monitor.warnings_progress_panel
        return _ProjectDocumentStateSnapshot(
            project=self.current_project,
            context=self._project_document_context,
            document_binding_epoch=self._document_binding_epoch,
            workflow_project=self.workflow_session.project,
            workflow_items=self.workflow_session.items,
            workflow_mesh_infos=self.workflow_session.mesh_infos,
            workflow_result_tables=self.workflow_session.result_tables,
            workflow_figure_datasets=self.workflow_session.figure_datasets,
            workflow_warnings=self.workflow_session.warnings,
            last_imported_mesh_data=self.last_imported_mesh_data,
            last_imported_mesh_ref=self.last_imported_mesh_ref,
            selected_mesh_context=self.selected_mesh_context,
            mesh_data_by_ref=self._mesh_data_by_ref,
            result_catalog=self.result_catalog,
            last_figure_dataset=self.last_figure_dataset,
            last_result_datasets=self.last_result_datasets,
            scene_screenshot_candidates=tuple(self._scene_screenshot_candidates),
            metadata_mesh_load_state=self._metadata_mesh_load_state,
            last_persisted_screenshot_status=(
                self._last_persisted_report_screenshot_status
            ),
            run_log=self.run_monitor.toPlainText(),
            monitor_warnings=tuple(monitor.warning_messages()),
            monitor_progress=monitor.progress_percent(),
            report_summary=(
                self.properties_panel.report_preview_panel.last_report_summary
            ),
            document_surfaces=tuple(
                (name, getattr(self, name)) for name in _DOCUMENT_SURFACE_ATTRIBUTES
            ),
        )

    def _reset_document_scoped_state(self) -> None:
        """Clear state derived from the previous document before a replacement."""

        self.workflow_session.items = {}
        self.workflow_session.mesh_infos = []
        self.workflow_session.result_tables = []
        self.workflow_session.figure_datasets = []
        self.workflow_session.warnings = []
        self.last_imported_mesh_data = None
        self.last_imported_mesh_ref = None
        self.selected_mesh_context = None
        self._mesh_data_by_ref = {}
        self.result_catalog = None
        self.last_figure_dataset = None
        self.last_result_datasets = ()
        self._scene_screenshot_candidates = ()
        # Keep the session-monotonic screenshot counter so a document swap never
        # reuses a transient record id within the same MainWindow.
        self._metadata_mesh_load_state = None
        self._last_persisted_report_screenshot_status = ""
        self._set_metadata_mesh_load_action_enabled(True)
        self.run_monitor.clear_log()
        self.run_monitor.warnings_progress_panel.set_warnings([])
        self.run_monitor.warnings_progress_panel.set_progress(0)

    def _restore_project_document_state(
        self,
        snapshot: _ProjectDocumentStateSnapshot,
    ) -> None:
        """Restore the exact in-memory document snapshot after a failed commit."""

        self.current_project = snapshot.project
        self._project_document_context = snapshot.context
        self._document_binding_epoch = snapshot.document_binding_epoch
        self.workflow_session.project = snapshot.workflow_project
        self.workflow_session.items = snapshot.workflow_items
        self.workflow_session.mesh_infos = snapshot.workflow_mesh_infos
        self.workflow_session.result_tables = snapshot.workflow_result_tables
        self.workflow_session.figure_datasets = snapshot.workflow_figure_datasets
        self.workflow_session.warnings = snapshot.workflow_warnings
        self.last_imported_mesh_data = snapshot.last_imported_mesh_data
        self.last_imported_mesh_ref = snapshot.last_imported_mesh_ref
        self.selected_mesh_context = snapshot.selected_mesh_context
        self._mesh_data_by_ref = snapshot.mesh_data_by_ref
        self.result_catalog = snapshot.result_catalog
        self.last_figure_dataset = snapshot.last_figure_dataset
        self.last_result_datasets = snapshot.last_result_datasets
        self._scene_screenshot_candidates = snapshot.scene_screenshot_candidates
        self._metadata_mesh_load_state = snapshot.metadata_mesh_load_state
        self._last_persisted_report_screenshot_status = (
            snapshot.last_persisted_screenshot_status
        )
        for name, surface in snapshot.document_surfaces:
            setattr(self, name, surface)
        self.run_monitor.set_log_lines(snapshot.run_log.splitlines())
        monitor = self.run_monitor.warnings_progress_panel
        monitor.set_warnings(list(snapshot.monitor_warnings))
        monitor.set_progress(snapshot.monitor_progress)
        state = snapshot.metadata_mesh_load_state
        in_flight = state is not None and getattr(state, "status", "") in {
            "loading",
            "cancel_requested",
        }
        self._set_metadata_mesh_load_action_enabled(not in_flight)

        if hasattr(self.project_tree_panel, "set_project"):
            self._attempt_document_surface_restore(
                lambda: self.project_tree_panel.set_project(snapshot.project)
            )
        if hasattr(self.properties_panel, "set_project"):
            self._attempt_document_surface_restore(
                lambda: self.properties_panel.set_project(snapshot.project)
            )
        if self.result_viewer is not None and hasattr(
            self.result_viewer, "set_result_catalog"
        ):
            self._attempt_document_surface_restore(
                lambda: self.result_viewer.set_result_catalog(snapshot.result_catalog)
            )
        report_panel = self.properties_panel.report_preview_panel
        if snapshot.report_summary is not None and hasattr(
            report_panel, "set_report_summary"
        ):
            self._attempt_document_surface_restore(
                lambda: report_panel.set_report_summary(snapshot.report_summary)
            )
        self._attempt_document_surface_restore(
            self._refresh_persisted_report_screenshot_surfaces
        )

    def _attempt_document_surface_restore(self, callback: Callable[[], None]) -> None:
        try:
            callback()
        except Exception:
            # The authoritative Project/context/workflow snapshot is already
            # restored. A persistently failing presentation surface must not
            # turn the original operation into a second state mutation.
            return

    def _guard_document_callback(
        self,
        callback: Callable[..., object],
        *,
        stale_result: object | None = None,
    ) -> Callable[..., object]:
        """Ignore a document-bound callback after a successful New/Open."""

        document_binding_epoch = self._document_binding_epoch

        def guarded(*args: object, **kwargs: object) -> object | None:
            if self._document_binding_epoch != document_binding_epoch:
                return stale_result
            return callback(*args, **kwargs)

        return guarded

    def _retire_document_bound_surfaces(self) -> None:
        """Best-effort close document surfaces after an otherwise complete commit."""

        self._replace_active_scene_controller()
        for dialog_name in _DOCUMENT_DIALOG_ATTRIBUTES:
            dialog = getattr(self, dialog_name)
            if dialog is not None:
                for method_name in ("hide", "close", "deleteLater"):
                    method = getattr(dialog, method_name, None)
                    if callable(method):
                        try:
                            method()
                        except Exception:
                            continue
            setattr(self, dialog_name, None)
        for viewer_name in _DOCUMENT_VIEWER_ATTRIBUTES:
            setattr(self, viewer_name, None)

    def _replace_project_document(
        self,
        project: Project,
        *,
        project_file_path: str | None,
        origin: ProjectDocumentOrigin,
        success_message: str,
        failure_message: str,
    ) -> bool:
        snapshot = self._capture_project_document_state()
        next_context = ProjectDocumentContext(
            project_file_path=project_file_path,
            origin=origin,
            generation=snapshot.context.generation + 1,
        )
        try:
            self._reset_document_scoped_state()
            self._document_binding_epoch = snapshot.document_binding_epoch + 1
            self._project_document_context = next_context
            self.set_project(project)
            self._placeholder_action(success_message)
        except Exception:
            self._restore_project_document_state(snapshot)
            self._project_error_reporter(failure_message)
            return False
        # No failure-producing document mutation follows this best-effort final
        # retirement step. Generation guards make late queued callbacks inert.
        self._retire_document_bound_surfaces()
        self._project_dirty = False
        return True

    def _choose_project_open_path(self) -> str | None:
        selected, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Open OSW Project",
            "",
            (
                "OSW Project Files (*.osw.json *.json *.osw.yaml *.yaml *.yml);;"
                "All Files (*)"
            ),
        )
        return str(selected) if selected else None

    def _choose_project_save_path(self) -> str | None:
        selected, _selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save OSW Project As",
            "",
            (
                "OSW Project Files (*.osw.json *.json *.osw.yaml *.yaml *.yml);;"
                "All Files (*)"
            ),
        )
        return str(selected) if selected else None

    def _load_project_file(self, path: str) -> Project:
        from osw.core.project_io import load_project

        return load_project(path)

    def _save_project_file(self, project: Project, path: str) -> None:
        from osw.core.project_io import save_project

        save_project(project, path)

    def _show_project_file_error(self, message: str) -> None:
        QtWidgets.QMessageBox.critical(self, "OSW Project", str(message))

    def open_project(self, _checked: bool = False) -> bool:
        selected = self._project_open_path_picker()
        if selected in (None, ""):
            return False
        selected_path = str(selected)
        try:
            project = self._project_loader(selected_path)
            if not isinstance(project, Project):
                raise TypeError("Project loader did not return a Project")
            validation = project.validate()
            if validation.has_errors:
                raise ValueError("Project validation failed")
        except Exception:
            self._project_error_reporter(
                "Could not open the selected project. The current document was not changed."
            )
            return False

        replaced = self._replace_project_document(
            project,
            project_file_path=selected_path,
            origin=ProjectDocumentOrigin.OPENED,
            success_message="Opened Project",
            failure_message=(
                "Could not display the selected project. "
                "The current document was restored."
            ),
        )
        return replaced

    def save_project(self, _checked: bool = False) -> bool:
        path = self.current_project_file_path()
        if path is None:
            return self.save_project_as()
        try:
            project_to_save = self._project_for_explicit_save()
            self._project_saver(project_to_save, path)
        except Exception:
            self._project_error_reporter(
                "Could not save the current project. The document binding was not changed."
            )
            return False
        self.set_project(project_to_save)
        self._placeholder_action("Saved Project")
        self._project_dirty = False
        return True

    def save_project_as(self, _checked: bool = False) -> bool:
        selected = self._project_save_path_picker()
        if selected in (None, ""):
            return False
        selected_path = str(selected)
        try:
            project_to_save = self._project_for_explicit_save()
            self._project_saver(project_to_save, selected_path)
        except Exception:
            self._project_error_reporter(
                "Could not save the current project. The document binding was not changed."
            )
            return False

        prior_context = self._project_document_context
        try:
            self._project_document_context = ProjectDocumentContext(
                project_file_path=selected_path,
                origin=ProjectDocumentOrigin.SAVED_AS,
                generation=prior_context.generation + 1,
            )
            self.set_project(project_to_save)
            self._placeholder_action("Saved Project As")
        except Exception:
            self._project_document_context = prior_context
            self._project_error_reporter(
                "The project was written, but its document binding could not be updated."
            )
            return False
        self._project_dirty = False
        return True

    def _project_for_explicit_save(self) -> Project:
        """Capture valid current scene metadata without reading any external file."""

        snapshot = self.active_scene_controller.snapshot_active_scene_state()
        if snapshot is None:
            return self.current_project
        return project_with(self.current_project, active_scene=snapshot)

    def set_project(self, project: Project, *, sync_workflow: bool = True) -> None:
        self.current_project = project
        if sync_workflow and hasattr(self, "workflow_session"):
            self.workflow_session.project = project
        if hasattr(self.project_tree_panel, "set_project"):
            self.project_tree_panel.set_project(project)
        if hasattr(self.properties_panel, "set_project"):
            self.properties_panel.set_project(project)
        self.active_scene_controller.set_named_selections(project.selections)
        self.active_scene_controller.set_solver_setup(
            project.primary_physics,
            materials=project.materials,
        )
        if self.active_scene_controller.current_mesh_fingerprint is None:
            self.active_scene_controller.set_pending_active_scene_state(
                project.active_scene
            )
        self._refresh_named_selection_panel()
        self._refresh_setup_overlay_panel()
        self._refresh_mesh_diagnostics_panel()
        self.refresh_results_from_project(update_report=False)
        self.generate_report_preview(log=False)
        self._refresh_persisted_report_screenshot_surfaces()
        self._refresh_saved_active_scene_status()

    def _create_active_scene_controller(self) -> object:
        """Create the one lazy active-scene owner for the current document."""

        from osw.gui.workspace_scene_controller import (
            ActiveSceneController,
            SceneAdapterRendererFactory,
        )

        factory = self._scene_renderer_factory
        if factory is None:
            if self._mesh_scene_adapter_factory is not None:
                factory = SceneAdapterRendererFactory(self._mesh_scene_adapter_factory)
            else:
                from osw.gui.workspace_scene_pyvistaqt import (
                    PyVistaQtRendererFactory,
                )

                factory = PyVistaQtRendererFactory()
        return ActiveSceneController(factory)

    def _replace_active_scene_controller(self) -> None:
        """Close the previous document scene before installing a fresh owner."""

        controller = self.active_scene_controller
        controller.close()
        self.active_scene_controller = self._create_active_scene_controller()
        panel = getattr(self, "central_viewport_panel", None)
        bind_controller = getattr(panel, "set_scene_controller", None)
        if callable(bind_controller):
            bind_controller(self.active_scene_controller)
        self.active_scene_controller.set_selection_listener(
            self._refresh_named_selection_panel
        )
        self.active_scene_controller.set_named_selections(
            self.current_project.selections
        )
        self.active_scene_controller.set_solver_setup(
            self.current_project.primary_physics,
            materials=self.current_project.materials,
        )
        self.active_scene_controller.set_pending_active_scene_state(
            self.current_project.active_scene
        )
        self._apply_setup_visibility_to_current_controller()
        self._refresh_mesh_diagnostics_panel()
        self._refresh_saved_active_scene_status()
        named_panel = getattr(self, "named_selection_panel", None)
        if named_panel is not None:
            picking_available = bool(
                getattr(panel, "interactive_available", False)
                and "picking" in self.active_scene_controller.capabilities
            )
            named_panel.set_backend_available(
                picking_available,
                getattr(self.active_scene_controller, "fallback_reason", ""),
            )
            if picking_available:
                self.active_scene_controller.set_pick_mode(
                    named_panel.mode_selector.currentText().lower()
                )
            self._refresh_named_selection_panel()

    def _on_entity_pick_mode_changed(self, mode: str) -> None:
        if self.active_scene_controller.set_pick_mode(mode):
            self.named_selection_panel.set_status(
                f"{mode.title()} picking is active."
            )
            return
        if self.active_scene_controller.current_mesh_fingerprint is None:
            self.named_selection_panel.set_status(
                "Load an in-memory mesh before picking entities.",
                error=True,
            )
        else:
            self.named_selection_panel.set_status(
                "The active renderer does not provide entity picking.",
                error=True,
            )

    def _on_clear_current_selection(self) -> None:
        self.active_scene_controller.clear_current_selection()
        self.named_selection_panel.set_status(
            "Current transient selection cleared."
        )

    def _on_create_named_selection(
        self,
        name: str,
        description: str,
    ) -> None:
        from osw.core.selection_resolution import (
            NamedSelectionLifecycleError,
            create_named_selection,
        )

        selection_id = f"selection-{uuid4().hex[:12]}"
        try:
            selections = create_named_selection(
                self.current_project.selections,
                self.active_scene_controller.current_selection_target,
                self.active_scene_controller.current_selection_resolution,
                selection_id=selection_id,
                name=name,
                description=description,
            )
            self.set_project(
                _project_replacing_named_selections(
                    self.current_project,
                    selections,
                )
            )
        except NamedSelectionLifecycleError as exc:
            self.named_selection_panel.set_status(str(exc), error=True)
            return
        self.named_selection_panel.select_named_selection(selection_id)
        self.named_selection_panel.set_status(
            f"Created NamedSelection '{name}'."
        )

    def _on_rename_named_selection(
        self,
        selection_id: str,
        name: str,
    ) -> None:
        from osw.core.selection_resolution import (
            NamedSelectionLifecycleError,
            rename_named_selection,
        )

        try:
            selections = rename_named_selection(
                self.current_project.selections,
                selection_id,
                name,
            )
            self.set_project(
                _project_replacing_named_selections(
                    self.current_project,
                    selections,
                )
            )
        except NamedSelectionLifecycleError as exc:
            self.named_selection_panel.set_status(str(exc), error=True)
            return
        self.named_selection_panel.select_named_selection(selection_id)
        self.named_selection_panel.set_status(
            f"Renamed NamedSelection to '{name}'."
        )

    def _on_replace_named_selection_targets(
        self,
        selection_id: str,
    ) -> None:
        from osw.core.selection_resolution import (
            NamedSelectionLifecycleError,
            replace_named_selection_targets,
        )

        try:
            selections = replace_named_selection_targets(
                self.current_project.selections,
                selection_id,
                self.active_scene_controller.current_selection_target,
                self.active_scene_controller.current_selection_resolution,
            )
            self.set_project(
                _project_replacing_named_selections(
                    self.current_project,
                    selections,
                )
            )
        except NamedSelectionLifecycleError as exc:
            self.named_selection_panel.set_status(str(exc), error=True)
            return
        self.named_selection_panel.select_named_selection(selection_id)
        self.named_selection_panel.set_status(
            "Replaced NamedSelection targets from the resolved current selection."
        )

    def _on_delete_named_selection(self, selection_id: str) -> None:
        from osw.core.selection_resolution import (
            NamedSelectionLifecycleError,
            delete_named_selection,
            find_named_selection_references,
        )

        references = find_named_selection_references(
            self.current_project,
            selection_id,
        )
        try:
            selections = delete_named_selection(
                self.current_project.selections,
                selection_id,
                references=references,
            )
            self.set_project(
                _project_replacing_named_selections(
                    self.current_project,
                    selections,
                )
            )
        except NamedSelectionLifecycleError as exc:
            self.named_selection_panel.set_status(str(exc), error=True)
            return
        self.named_selection_panel.set_status(
            f"Deleted NamedSelection '{selection_id}'."
        )

    def _on_named_selection_activated(self, selection_id: str) -> None:
        resolution = self.active_scene_controller.named_selection_resolutions.get(
            selection_id
        )
        if resolution is not None:
            self.named_selection_panel.set_status(resolution.message)
        panel = getattr(self, "setup_overlay_panel", None)
        if panel is not None:
            panel.set_selection_filter(selection_id)

    def _refresh_named_selection_panel(self) -> None:
        panel = getattr(self, "named_selection_panel", None)
        if panel is None:
            return
        target = self.active_scene_controller.current_selection_target
        resolution = self.active_scene_controller.current_selection_resolution
        count = (
            len(target.locator.entity_ids)
            if target is not None and target.locator is not None
            else 0
        )
        panel.set_current_selection(
            count=count,
            resolution_state=resolution.state.value,
            status=resolution.message,
        )
        panel.set_named_selections(
            self.current_project.selections,
            self.active_scene_controller.named_selection_resolutions,
        )
        self._refresh_setup_overlay_panel()

    @property
    def project_dirty(self) -> bool:
        return self._project_dirty

    def _refresh_setup_overlay_panel(self) -> None:
        panel = getattr(self, "setup_overlay_panel", None)
        if panel is None:
            return
        from osw.core.project_schema import PhysicsSetup

        panel.set_context(
            setup=self.current_project.primary_physics or PhysicsSetup(),
            selections=self.current_project.selections,
            materials=self.current_project.materials,
            statuses=self.active_scene_controller.setup_statuses,
        )

    def _on_setup_category_visibility_changed(
        self,
        category: str,
        visible: bool,
    ) -> None:
        self.active_scene_controller.set_setup_category_visible(
            category,
            visible,
        )

    def _apply_setup_visibility_to_current_controller(self) -> None:
        panel = getattr(self, "setup_overlay_panel", None)
        if panel is None:
            return
        for category in ("material", "fixed_support", "force"):
            checkbox = panel.visibility_checks[category]
            self.active_scene_controller.set_setup_category_visible(
                category,
                checkbox.isChecked(),
            )

    def _show_unsupported_setup_kind(self, kind: str) -> None:
        self.setup_overlay_panel.set_preview(
            f"Unsupported setup kind: {kind or '<empty>'}."
        )

    def _on_create_setup_record(self, payload: object) -> None:
        if not isinstance(payload, Mapping):
            return
        kind = str(payload.get("kind", ""))
        record_id = f"setup-{kind.casefold().replace(' ', '-')}-{uuid4().hex[:12]}"
        try:
            record = _setup_record_from_payload(record_id, payload)
            setup = _setup_with_record(
                self.current_project.primary_physics,
                kind,
                record,
            )
        except ValueError:
            self._show_unsupported_setup_kind(kind)
            return
        self.set_project(_project_replacing_primary_physics(self.current_project, setup))
        self._project_dirty = True

    def _on_edit_setup_record(
        self,
        kind: str,
        record_id: str,
        payload: object,
    ) -> None:
        if not isinstance(payload, Mapping):
            return
        record_payload = dict(payload)
        record_payload["kind"] = kind
        try:
            record = _setup_record_from_payload(record_id, record_payload)
            setup = _setup_with_record(
                self.current_project.primary_physics,
                kind,
                record,
                replace_existing=True,
            )
        except ValueError:
            self._show_unsupported_setup_kind(kind)
            return
        self.set_project(_project_replacing_primary_physics(self.current_project, setup))
        self._project_dirty = True

    def _on_delete_setup_record(self, kind: str, record_id: str) -> None:
        try:
            setup = _setup_without_record(
                self.current_project.primary_physics,
                kind,
                record_id,
            )
        except ValueError:
            self._show_unsupported_setup_kind(kind)
            return
        self.set_project(_project_replacing_primary_physics(self.current_project, setup))
        self._project_dirty = True

    def _on_setup_record_selected(
        self,
        _kind: str,
        _record_id: str,
        target_selection_id: str,
    ) -> None:
        self.named_selection_panel.select_named_selection(target_selection_id)

    def _on_prepare_setup_preview(self) -> None:
        provider = self._setup_preview_provider
        if provider is None or self.last_imported_mesh_data is None:
            self.setup_overlay_panel.set_preview(
                "Prepare-only preview requires an injected service and an active in-memory mesh."
            )
            return
        result = provider(
            self.current_project,
            self.last_imported_mesh_data,
            str(self.last_imported_mesh_ref or ""),
        )
        self.setup_overlay_panel.set_preview(
            str(getattr(result, "input_preview", result))
        )

    def _refresh_mesh_diagnostics_panel(self) -> None:
        panel = getattr(self, "mesh_diagnostics_panel", None)
        if panel is None:
            return
        panel.set_view_model(self.active_scene_controller.mesh_quality_view_model)

    def _on_mesh_diagnostics_analyze(self) -> None:
        panel = self.mesh_diagnostics_panel
        try:
            analysis = self.active_scene_controller.analyze_mesh_quality()
        except ValueError as exc:
            panel.set_status(str(exc))
            return
        self._refresh_mesh_diagnostics_panel()
        if analysis is None:
            panel.set_status(
                "Load an in-memory mesh before running Mesh Diagnostics."
            )

    def _on_mesh_diagnostics_threshold_changed(self, threshold: float) -> None:
        if not self.active_scene_controller.set_mesh_quality_threshold(threshold):
            self.mesh_diagnostics_panel.set_status(
                "Bad-cell threshold must be finite and positive."
            )
            return
        self._refresh_mesh_diagnostics_panel()

    def _on_mesh_diagnostics_highlight_toggled(self, visible: bool) -> None:
        applied = self.active_scene_controller.set_mesh_quality_highlight_visible(
            visible
        )
        self._refresh_mesh_diagnostics_panel()
        if visible and not applied:
            self.mesh_diagnostics_panel.set_status(
                self.active_scene_controller.fallback_reason
                or "Highlight requires analysis, bad cells, and an interactive renderer."
            )

    def _on_mesh_diagnostics_isolate_toggled(self, isolated: bool) -> None:
        applied = self.active_scene_controller.set_mesh_quality_isolated(isolated)
        self._refresh_mesh_diagnostics_panel()
        if isolated and not applied:
            self.mesh_diagnostics_panel.set_status(
                "Isolate requires a visible bad-cell highlight."
            )

    def _on_mesh_diagnostics_restore(self) -> None:
        if self.active_scene_controller.restore_mesh_quality_visibility():
            self.mesh_diagnostics_panel.set_status(
                "Restored the pre-isolate base mesh visibility."
            )

    def _on_mesh_diagnostics_clear(self) -> None:
        self.active_scene_controller.clear_mesh_quality_overlay()
        self._refresh_mesh_diagnostics_panel()
        self.mesh_diagnostics_panel.set_status(
            "Cleared the transient Mesh Diagnostics overlay."
        )

    def closeEvent(self, event: object) -> None:
        """Close renderer resources before Qt tears down child widgets."""

        self.active_scene_controller.close()
        super().closeEvent(event)

    def build_current_report_summary(self) -> object:
        """Build report summary data without executing tools."""

        from osw.post.report_sections import build_report_summary

        figure_datasets = (
            (self.last_figure_dataset,)
            if self.last_figure_dataset is not None
            else ()
        )
        summary = build_report_summary(
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
        return self._add_scene_screenshot_preview_section(
            summary,
            scene_screenshot_records=self._persisted_report_scene_screenshots(),
        )

    def _add_scene_screenshot_preview_section(
        self,
        summary: object,
        *,
        scene_screenshot_records: Sequence[object],
    ) -> object:
        """Attach staged screenshot sections to preview summary without mutating figures."""

        candidates = tuple(scene_screenshot_records)
        if not candidates:
            return summary

        from osw.post.report_generator import (
            _scene_screenshot_provenance_lines,
            _scene_screenshot_warning,
        )
        from osw.post.report_model import ReportSection, scene_screenshots_to_report_figures

        figures = scene_screenshots_to_report_figures(candidates)
        if not figures:
            return summary

        content_blocks: list[str] = []
        for figure in figures:
            caption = figure.caption or figure.title or figure.figure_id
            content_blocks.append(f"{figure.figure_id}: {caption}")
            screenshot_path = str(figure.primary_path or "")
            if screenshot_path:
                screenshot_format = figure.format.lower() if figure.format else ""
                if screenshot_format and screenshot_format not in {
                    "png",
                    "jpg",
                    "jpeg",
                    "svg",
                    "gif",
                    "webp",
                }:
                    content_blocks.append(
                        f"Scene screenshot artifact ({figure.format}): "
                        f"{screenshot_path}"
                    )
                else:
                    basename = screenshot_path.replace("\\", "/").rsplit("/", 1)[-1]
                    content_blocks.append(f"Image: {basename}")
            else:
                content_blocks.append("Image path: (no image path)")

            warning = _scene_screenshot_warning(figure)
            if warning:
                content_blocks.append(warning)
            content_blocks.extend(_scene_screenshot_provenance_lines(figure.metadata))
            caveat = figure.metadata.get("artifact_caveat")
            if caveat:
                content_blocks.append(str(caveat))

        if not content_blocks:
            return summary

        screenshot_section = ReportSection(
            section_id="scene-screenshots",
            title="3D Scene Screenshots",
            content_blocks=content_blocks,
        )
        return replace(
            summary,
            sections=(*tuple(getattr(summary, "sections", ())), screenshot_section),
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
            scene_screenshots=self._persisted_report_scene_screenshots(),
            warnings=tuple(getattr(self.workflow_session, "warnings", ())),
        )
        if hasattr(self.properties_panel.report_preview_panel, "set_report_summary"):
            self.properties_panel.report_preview_panel.set_report_summary(result.summary)
        self._placeholder_action(f"Exported report: {result.output_path}")
        return Path(result.output_path)

    def new_project(self, _checked: bool = False) -> bool:
        """Reset to the curated demo project until full project creation is designed."""

        try:
            project = create_heatsink_flow_demo_project()
        except Exception:
            self._project_error_reporter(
                "Could not create a new project. The current document was not changed."
            )
            return False
        replaced = self._replace_project_document(
            project,
            project_file_path=None,
            origin=ProjectDocumentOrigin.NEW,
            success_message="New Project",
            failure_message=(
                "Could not display the new project. The current document was restored."
            ),
        )
        return replaced

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
        aliases = _mesh_aliases_for_imported_mesh(mesh, resolved_ref)
        self._register_mesh_data_for_viewer(mesh_data, aliases)
        selected_context = self._refresh_selected_mesh_context_from_aliases(
            mesh_data,
            aliases,
        )
        self.last_imported_mesh_data = mesh_data
        self.last_imported_mesh_ref = resolved_ref or None
        if (
            selected_context is None
            and getattr(self.central_viewport_panel, "interactive_available", False)
            and hasattr(self.central_viewport_panel, "set_mesh")
        ):
            self.central_viewport_panel.set_mesh(
                mesh_data,
                mesh_ref=self.last_imported_mesh_ref or "",
            )
        if self.mesh_viewer is not None and hasattr(self.mesh_viewer, "set_mesh"):
            if selected_context is not None:
                self._apply_selected_mesh_context_to_viewer(selected_context)
            else:
                self.mesh_viewer.set_mesh(mesh_data, mesh_ref=self.last_imported_mesh_ref or "")
                self._sync_mesh_viewer_result_datasets()
        self._refresh_mesh_diagnostics_panel()

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

        dialog.previewAccepted.connect(self._guard_document_callback(_attach))
        dialog.scriptRunCompleted.connect(
            self._guard_document_callback(self._on_script_run_completed)
        )
        dialog.figureDatasetReady.connect(
            self._guard_document_callback(self._on_figure_dataset_ready)
        )
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

        dialog.matPreviewAccepted.connect(self._guard_document_callback(_attach))
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
        dialog.boundaryCurveAccepted.connect(
            self._guard_document_callback(self.attach_boundary_curve_to_project)
        )
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
        self.calculix_deck_dialog.deckWritten.connect(
            self._guard_document_callback(self._on_calculix_deck_written)
        )
        if hasattr(self.calculix_deck_dialog, "calculixRunCompleted"):
            self.calculix_deck_dialog.calculixRunCompleted.connect(
                self._guard_document_callback(self._on_calculix_run_completed)
            )
        if hasattr(self.calculix_deck_dialog, "calculixResultsParsed"):
            self.calculix_deck_dialog.calculixResultsParsed.connect(
                self._guard_document_callback(self._on_calculix_results_parsed)
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
                self._guard_document_callback(self._on_openfoam_case_generated)
            )
            self.openfoam_template_dialog.openfoamRunCompleted.connect(
                self._guard_document_callback(self._on_openfoam_run_completed)
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
            self.chm_property_dialog.resultDatasetReady.connect(
                self._guard_document_callback(self._on_chm_dataset_ready)
            )
            self.chm_property_dialog.propertyCalculated.connect(
                self._guard_document_callback(self._on_chm_property_result)
            )
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
            self.chm_reactor_dialog.resultDatasetReady.connect(
                self._guard_document_callback(self._on_chm_dataset_ready)
            )
            self.chm_reactor_dialog.reactorRunCompleted.connect(
                self._guard_document_callback(self._on_chm_reactor_result)
            )
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
        self._sync_mesh_viewer_result_datasets()

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
            self.mesh_viewer = build_mesh_viewer_panel(
                self.mesh_viewer_dialog,
                scene_adapter=self.active_scene_controller,
            )
            if hasattr(self.mesh_viewer, "set_bind_result_callback"):
                self.mesh_viewer.set_bind_result_callback(
                    self._guard_document_callback(
                        self.persist_mesh_viewer_result_binding,
                        stale_result=False,
                    )
                )
            if hasattr(self.mesh_viewer, "set_rebind_result_callback"):
                self.mesh_viewer.set_rebind_result_callback(
                    self._guard_document_callback(
                        self.rebind_mesh_viewer_result_binding,
                        stale_result=False,
                    )
                )
            if hasattr(self.mesh_viewer, "set_capture_scene_screenshot_callback"):
                self.mesh_viewer.set_capture_scene_screenshot_callback(
                    self._guard_document_callback(
                        self.capture_scene_screenshot_to_report_candidates
                    )
                )
            if hasattr(self.mesh_viewer, "set_scene_screenshot_candidates_provider"):
                self.mesh_viewer.set_scene_screenshot_candidates_provider(
                    self._guard_document_callback(
                        self.scene_screenshot_candidates,
                        stale_result=(),
                    )
                )
            if hasattr(self.mesh_viewer, "set_clear_scene_screenshots_callback"):
                self.mesh_viewer.set_clear_scene_screenshots_callback(
                    self._guard_document_callback(
                        self.clear_scene_screenshots_from_viewer,
                        stale_result=0,
                    )
                )
            if hasattr(self.mesh_viewer, "set_edit_scene_screenshot_caption_callback"):
                self.mesh_viewer.set_edit_scene_screenshot_caption_callback(
                    self._guard_document_callback(
                        self.update_scene_screenshot_caption,
                        stale_result=False,
                    )
                )
            if hasattr(self.mesh_viewer, "set_remove_scene_screenshot_callback"):
                self.mesh_viewer.set_remove_scene_screenshot_callback(
                    self._guard_document_callback(
                        self.remove_scene_screenshot_candidate,
                        stale_result=False,
                    )
                )
            if hasattr(self.mesh_viewer, "set_persist_scene_screenshots_callback"):
                self.mesh_viewer.set_persist_scene_screenshots_callback(
                    self._guard_document_callback(
                        self.persist_staged_scene_screenshots,
                        stale_result=0,
                    )
                )
            if hasattr(self.mesh_viewer, "set_persisted_report_screenshots_provider"):
                self.mesh_viewer.set_persisted_report_screenshots_provider(
                    self._guard_document_callback(
                        self.persisted_report_screenshot_assets,
                        stale_result=(),
                    )
                )
            if hasattr(
                self.mesh_viewer,
                "set_open_persisted_report_screenshot_manager_callback",
            ):
                self.mesh_viewer.set_open_persisted_report_screenshot_manager_callback(
                    self._guard_document_callback(
                        self.open_persisted_report_screenshot_manager
                    )
                )
            if hasattr(self.mesh_viewer, "set_clear_saved_active_scene_callback"):
                self.mesh_viewer.set_clear_saved_active_scene_callback(
                    self._guard_document_callback(
                        self.clear_saved_active_scene_state,
                        stale_result=False,
                    )
                )
            layout.addWidget(self.mesh_viewer)
            if hasattr(self.mesh_viewer, "set_theme_tokens"):
                self.mesh_viewer.set_theme_tokens(self.theme_manager.current_tokens)
        self._populate_mesh_viewer_from_latest()
        self._refresh_saved_active_scene_status()
        self.mesh_viewer_dialog.show()
        self.mesh_viewer_dialog.raise_()
        self.mesh_viewer_dialog.activateWindow()
        return self.mesh_viewer_dialog

    def scene_screenshot_candidates(self) -> tuple[SceneScreenshotRecord, ...]:
        """Return transient report-ready scene screenshot records."""
        return self._scene_screenshot_candidates

    def persisted_report_screenshot_assets(self) -> tuple[object, ...]:
        """Return the current Project-owned persisted screenshot assets."""
        return tuple(getattr(self.current_project, "report_screenshots", ()) or ())

    def clear_saved_active_scene_state(self) -> bool:
        """Explicitly clear only saved workspace metadata and mark the Project dirty."""

        if self.current_project.active_scene is None:
            self.active_scene_controller.clear_saved_active_scene_state()
            self._refresh_saved_active_scene_status()
            return False
        self.current_project = project_with(self.current_project, active_scene=None)
        self.workflow_session.project = self.current_project
        self.active_scene_controller.clear_saved_active_scene_state()
        self._project_dirty = True
        self._refresh_saved_active_scene_status()
        return True

    def _refresh_saved_active_scene_status(self) -> None:
        panel = self.mesh_viewer
        if panel is None or not hasattr(panel, "show_saved_active_scene_status"):
            return
        result = self.active_scene_controller.active_scene_restore_result
        if self.current_project.active_scene is None:
            message = "No saved workspace state"
        else:
            labels = {
                "PENDING": "Pending mesh reload",
                "RESTORED": "Restored",
                "PARTIAL": "Partially restored",
                "STALE": "Stale mesh",
                "INVALID": "Invalid saved state",
            }
            message = labels.get(str(result.status), str(result.status))
            if result.reason_codes:
                message = f"{message}: {', '.join(result.reason_codes)}"
        panel.show_saved_active_scene_status(message)

    def _transient_scene_screenshot_ids(self) -> tuple[str, ...]:
        return tuple(
            record.id for record in self._scene_screenshot_candidates if record.id
        )

    def clear_scene_screenshot_candidates(self) -> None:
        """Clear transient scene screenshot candidate records for report export."""
        self._scene_screenshot_candidates = ()

    def clear_scene_screenshots_from_viewer(self) -> None:
        """Clear transient staged scene screenshots and refresh the viewer status.

        Owned by MainWindow so the mesh viewer panel drives the clear action
        through an injected callback without owning candidate storage. Only the
        transient in-session candidate list is affected; no ProjectSchema,
        ResultDataset, result binding, mesh, or project-file state is mutated.
        """
        self.clear_scene_screenshot_candidates()
        self._refresh_scene_screenshot_viewer()

    def update_scene_screenshot_caption(self, record_id: str, caption: str | None) -> bool:
        """Update one staged screenshot record's caption (transient immutable replace).

        Returns True when a record matched. The frozen ``SceneScreenshotRecord``
        is replaced with a copy carrying the new caption; every other field is
        preserved. Only the transient candidate list is affected -- no
        ProjectSchema / ResultDataset / result binding / mesh mutation and no
        project auto-save.
        """
        target = str(record_id)
        updated = False
        rebuilt: list[SceneScreenshotRecord] = []
        for record in self._scene_screenshot_candidates:
            if not updated and str(getattr(record, "id", "")) == target:
                rebuilt.append(replace(record, caption=caption))
                updated = True
            else:
                rebuilt.append(record)
        if updated:
            self._scene_screenshot_candidates = tuple(rebuilt)
            self._refresh_scene_screenshot_viewer()
        return updated

    def remove_scene_screenshot_candidate(self, record_id: str) -> bool:
        """Remove one staged screenshot record by id (transient); keep the rest.

        Returns True when a record was removed. Monotonic ids make the match
        unique, so exactly one record is dropped. Bulk clear behavior is
        unchanged; only the transient candidate list is affected.
        """
        target = str(record_id)
        remaining = tuple(
            record
            for record in self._scene_screenshot_candidates
            if str(getattr(record, "id", "")) != target
        )
        if len(remaining) == len(self._scene_screenshot_candidates):
            return False
        self._scene_screenshot_candidates = remaining
        self._refresh_scene_screenshot_viewer()
        return True

    def _refresh_scene_screenshot_viewer(self) -> None:
        """Refresh the mesh viewer's staged screenshot status, if present."""
        if self.mesh_viewer is not None and hasattr(
            self.mesh_viewer, "refresh_scene_screenshot_status"
        ):
            self.mesh_viewer.refresh_scene_screenshot_status()

    def _report_scene_screenshots(self) -> tuple[SceneScreenshotRecord, ...]:
        """Combine transient staged and persisted project scene screenshots.

        Transient staged candidates take priority; persisted project report
        assets (converted back into records) are appended and de-duplicated by
        id. Transient-only sessions are unchanged, while persisted assets surface
        after a project reload.
        """
        from osw.post.report_model import report_asset_to_scene_screenshot

        records = list(self._scene_screenshot_candidates)
        seen = {record.id for record in records if record.id}
        for asset in getattr(self.current_project, "report_screenshots", ()) or ():
            record = report_asset_to_scene_screenshot(asset)
            if record.id and record.id in seen:
                continue
            if record.id:
                seen.add(record.id)
            records.append(record)
        return tuple(records)

    def _persisted_report_scene_screenshots(
        self,
    ) -> tuple[SceneScreenshotRecord, ...]:
        """Return persisted Project report assets only; never capture a scene."""

        from osw.post.report_model import report_assets_to_scene_screenshots

        return report_assets_to_scene_screenshots(
            self.current_project.report_screenshots
        )

    def persist_staged_scene_screenshots(self) -> int:
        """Persist staged scene screenshots into project report assets (opt-in).

        User-triggered only. Bridges the transient candidates into core
        ``ReportScreenshotAsset`` records and merges them into the current
        project's ``report_screenshots`` (local paths only; no image bytes
        copied, no project auto-save). Returns the number persisted, 0 when
        nothing is staged, or -1 when the confirmation is declined. Transient
        candidates are preserved.
        """
        candidates = self._scene_screenshot_candidates
        if not candidates:
            return 0
        candidate_ids = [record.id for record in candidates]
        persisted_ids = {
            asset.id for asset in self.current_project.report_screenshots
        }
        if (
            len(candidate_ids) != len(set(candidate_ids))
            or any(record_id in persisted_ids for record_id in candidate_ids)
        ):
            self._show_persisted_report_screenshot_status(
                "Duplicate scene screenshot IDs must be resolved before staging."
            )
            return -2
        if not self._confirm_persist_scene_screenshots(len(candidates)):
            return -1
        from osw.post.report_model import scene_screenshots_to_report_assets

        assets = scene_screenshots_to_report_assets(candidates)
        self.set_project(_project_with_report_screenshots(self.current_project, assets))
        self._project_dirty = True
        return len(assets)

    def _confirm_persist_scene_screenshots(self, count: int) -> bool:
        """Confirm persisting staged screenshots; overridable seam for tests."""
        if QtWidgets is None:
            return True
        answer = QtWidgets.QMessageBox.question(
            self,
            "Persist scene screenshot report assets",
            (
                "Persist staged scene screenshots as project report assets? "
                "Image files are not copied; local paths are stored."
            ),
        )
        return answer == QtWidgets.QMessageBox.StandardButton.Yes

    def open_persisted_report_screenshot_manager(
        self, _checked: bool = False
    ) -> object:
        """Open the persisted-only manager without transferring Project ownership."""
        from osw.gui.widgets.persisted_report_screenshot_manager import (
            PersistedReportScreenshotManager,
        )

        if self.persisted_report_screenshot_manager is None:
            self.persisted_report_screenshot_manager = PersistedReportScreenshotManager(
                self,
                assets_provider=self.persisted_report_screenshot_assets,
                transient_ids_provider=self._transient_scene_screenshot_ids,
                edit_callback=self.update_persisted_report_screenshot_caption,
                remove_callback=self.remove_persisted_report_screenshot,
                relink_callback=self.relink_persisted_report_screenshot,
            )
        manager = self.persisted_report_screenshot_manager
        manager.refresh_records()
        manager.show()
        manager.raise_()
        manager.activateWindow()
        return manager

    def update_persisted_report_screenshot_caption(
        self,
        target: object,
        caption: object = _PERSISTED_CAPTION_NOT_SUPPLIED,
    ) -> bool:
        """Replace one exact persisted caption after stale-target revalidation."""
        matched = self._validated_persisted_report_screenshot_target(target)
        if matched is None:
            return self._show_persisted_report_screenshot_status(
                _PERSISTED_SCREENSHOT_STALE_TEXT
            )
        _, asset = matched
        if caption is _PERSISTED_CAPTION_NOT_SUPPLIED:
            new_caption = self._prompt_persisted_report_screenshot_caption(asset.caption)
            if new_caption is None:
                return self._show_persisted_report_screenshot_status(
                    "Persisted scene screenshot caption edit cancelled."
                )
        else:
            new_caption = str(caption)

        matched = self._validated_persisted_report_screenshot_target(target)
        if matched is None:
            return self._show_persisted_report_screenshot_status(
                _PERSISTED_SCREENSHOT_STALE_TEXT
            )
        index, asset = matched
        assets = list(self.persisted_report_screenshot_assets())
        assets[index] = replace(asset, caption=new_caption)
        self.set_project(
            _project_replacing_report_screenshots(self.current_project, assets)
        )
        self._show_persisted_report_screenshot_status(
            "Updated persisted scene screenshot caption."
        )
        return True

    def remove_persisted_report_screenshot(self, target: object) -> bool:
        """Remove one exact persisted metadata row without touching its file."""
        matched = self._validated_persisted_report_screenshot_target(target)
        if matched is None:
            return self._show_persisted_report_screenshot_status(
                _PERSISTED_SCREENSHOT_STALE_TEXT
            )
        _, asset = matched
        if not self._confirm_remove_persisted_report_screenshot(asset):
            return self._show_persisted_report_screenshot_status(
                "Persisted scene screenshot removal cancelled."
            )

        matched = self._validated_persisted_report_screenshot_target(target)
        if matched is None:
            return self._show_persisted_report_screenshot_status(
                _PERSISTED_SCREENSHOT_STALE_TEXT
            )
        index, _asset = matched
        assets = list(self.persisted_report_screenshot_assets())
        del assets[index]
        self.set_project(
            _project_replacing_report_screenshots(self.current_project, assets)
        )
        self._show_persisted_report_screenshot_status(
            "Removed persisted scene screenshot record."
        )
        return True

    def relink_persisted_report_screenshot(
        self,
        target: object,
        selected_path: str | Path | None = None,
    ) -> bool:
        """Explicitly replace one stored path without copying or rewriting a file."""
        matched = self._validated_persisted_report_screenshot_target(target)
        if matched is None:
            return self._show_persisted_report_screenshot_status(
                _PERSISTED_SCREENSHOT_STALE_TEXT
            )
        _, asset = matched
        selected = (
            self._pick_persisted_report_screenshot_relink_path()
            if selected_path is None
            else str(selected_path)
        )
        if not selected:
            return self._show_persisted_report_screenshot_status(
                "Persisted scene screenshot relink cancelled."
            )
        if selected == asset.path:
            return self._show_persisted_report_screenshot_status(
                "The selected file is already linked to this screenshot."
            )
        candidate = Path(selected)
        if not candidate.is_file() or candidate.suffix.lower() not in (
            _PERSISTED_SCREENSHOT_SUFFIXES
        ):
            return self._show_persisted_report_screenshot_status(
                "Select an existing PNG, JPG, JPEG, WEBP, or GIF file."
            )
        replacement_kind = _relinked_report_screenshot_path_kind(asset.path_kind)
        try:
            replacement = replace(
                asset,
                path=selected,
                path_kind=replacement_kind,
            )
        except (TypeError, ValueError):
            return self._show_persisted_report_screenshot_status(
                "The selected image path is incompatible with its path classification."
            )
        if not self._confirm_relink_persisted_report_screenshot(asset, selected):
            return self._show_persisted_report_screenshot_status(
                "Persisted scene screenshot relink cancelled."
            )
        if not candidate.is_file() or candidate.suffix.lower() not in (
            _PERSISTED_SCREENSHOT_SUFFIXES
        ):
            return self._show_persisted_report_screenshot_status(
                "Select an existing PNG, JPG, JPEG, WEBP, or GIF file."
            )

        matched = self._validated_persisted_report_screenshot_target(target)
        if matched is None:
            return self._show_persisted_report_screenshot_status(
                _PERSISTED_SCREENSHOT_STALE_TEXT
            )
        index, _asset = matched
        assets = list(self.persisted_report_screenshot_assets())
        assets[index] = replacement
        self.set_project(
            _project_replacing_report_screenshots(self.current_project, assets)
        )
        self._show_persisted_report_screenshot_status(
            "Relinked persisted scene screenshot."
        )
        return True

    def _validated_persisted_report_screenshot_target(
        self, target: object
    ) -> tuple[int, object] | None:
        """Return the exact current asset only when index, id, and snapshot match."""
        try:
            index = int(target.index)
        except (AttributeError, TypeError, ValueError):
            return None
        assets = self.persisted_report_screenshot_assets()
        if index < 0 or index >= len(assets):
            return None
        asset = assets[index]
        expected_id = str(getattr(target, "expected_id", ""))
        expected_asset = getattr(target, "expected_asset", None)
        if asset.id != expected_id or asset != expected_asset:
            return None
        return index, asset

    def _prompt_persisted_report_screenshot_caption(self, current: str) -> str | None:
        text, accepted = QtWidgets.QInputDialog.getText(
            self,
            "Edit persisted scene screenshot caption",
            "Caption:",
            text=current,
        )
        return str(text) if accepted else None

    def _confirm_remove_persisted_report_screenshot(self, asset: object) -> bool:
        answer = QtWidgets.QMessageBox.question(
            self,
            "Remove persisted scene screenshot",
            (
                "Only the project metadata record will be removed.\n"
                "The referenced image file will not be deleted.\n\n"
                f"Record: {getattr(asset, 'id', '') or '(missing id)'}"
            ),
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return answer == QtWidgets.QMessageBox.StandardButton.Yes

    def _pick_persisted_report_screenshot_relink_path(self) -> str | None:
        selected, _selected_filter = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Relink selected screenshot...",
            "",
            _PERSISTED_SCREENSHOT_FILE_FILTER,
        )
        return str(selected) if selected else None

    def _confirm_relink_persisted_report_screenshot(
        self, asset: object, selected_path: str
    ) -> bool:
        path_kind_confirmation = _relinked_report_screenshot_path_kind_confirmation(
            getattr(asset, "path_kind", None)
        )
        answer = QtWidgets.QMessageBox.question(
            self,
            "Relink persisted scene screenshot",
            (
                "Only the stored path reference will change.\n"
                f"{path_kind_confirmation}\n"
                "No file will be copied or moved. Saving the Project remains a "
                "separate explicit action.\n"
                "The local path will be stored as selected.\n\n"
                f"Old path: {getattr(asset, 'path', '') or '(no image path)'}\n"
                f"New path: {selected_path}"
            ),
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return answer == QtWidgets.QMessageBox.StandardButton.Yes

    def _refresh_persisted_report_screenshot_surfaces(self) -> None:
        self._refresh_scene_screenshot_viewer()
        manager = self.persisted_report_screenshot_manager
        if manager is not None and hasattr(manager, "refresh_records"):
            manager.refresh_records()

    def _show_persisted_report_screenshot_status(self, message: str) -> bool:
        self._last_persisted_report_screenshot_status = str(message)
        if self.mesh_viewer is not None and hasattr(
            self.mesh_viewer, "show_persisted_report_screenshot_status"
        ):
            self.mesh_viewer.show_persisted_report_screenshot_status(message)
        manager = self.persisted_report_screenshot_manager
        if manager is not None and hasattr(manager, "show_status"):
            manager.show_status(message)
        return False

    def capture_scene_screenshot_to_report_candidates(self) -> SceneScreenshotRecord | None:
        """Capture an active viewer scene screenshot into report candidates."""
        if self.mesh_viewer is None:
            return None

        path = self._pick_scene_screenshot_target_path()
        if not path:
            return None

        record = self.mesh_viewer.capture_scene_metadata(
            path,
            record_id=self._next_scene_screenshot_record_id(),
            created_by="mesh-viewer",
        )
        if record is None:
            return None
        self._scene_screenshot_candidates = (
            *self._scene_screenshot_candidates,
            record,
        )
        return record

    def _pick_scene_screenshot_target_path(self) -> str | None:
        """Resolve user-confirmed target path for report scene screenshot capture."""
        if QtWidgets is None:
            return None
        selected, _selected_filter = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Add scene screenshot to report...",
            "",
            "Image Files (*.png *.jpg *.jpeg *.webp *.gif);;All Files (*.*)",
        )
        return selected or None

    def _next_scene_screenshot_record_id(self) -> str:
        """Allocate a session-monotonic id so removal never yields a duplicate.

        A monotonic counter (never decremented on removal or bulk clear)
        guarantees that capturing after a per-record removal cannot reuse an
        existing id. Append-only sessions still read scene-screenshot-1, -2, ...,
        preserving existing behavior.
        """
        self._scene_screenshot_counter += 1
        return f"scene-screenshot-{self._scene_screenshot_counter}"

    def _populate_mesh_viewer_from_latest(self) -> None:
        """Show selected or latest imported mesh when the panel has none yet.

        Runs on open so the first open after an import displays that mesh, but it
        never clobbers a mesh the panel already holds (a manual load or a prior
        refresh), keeping ``latest wins`` idempotent.
        """

        context = self.selected_mesh_context
        if (
            self.mesh_viewer is not None
            and hasattr(self.mesh_viewer, "set_mesh")
            and hasattr(self.mesh_viewer, "current_state")
            and self.mesh_viewer.current_state().mesh is None
        ):
            if context is not None:
                self._apply_selected_mesh_context_to_viewer(context)
                return
            if self.last_imported_mesh_data is None:
                self._sync_mesh_viewer_result_datasets()
                return
            self.mesh_viewer.set_mesh(
                self.last_imported_mesh_data,
                mesh_ref=self.last_imported_mesh_ref or "",
            )
            if hasattr(self.mesh_viewer, "show_active_mesh_status"):
                self.mesh_viewer.show_active_mesh_status(
                    "Loaded latest imported mesh for 3D preview."
                )
        self._sync_mesh_viewer_result_datasets()

    def load_mesh_into_viewer(self, mesh: object, *, mesh_ref: str = "") -> object:
        """Show the mesh preview dialog and hand it an already-built mesh.

        This receives MeshData that existing import/workflow state already
        produced; it neither generates, parses, nor converts meshes.
        """

        self.open_mesh_viewer()
        if hasattr(self.central_viewport_panel, "set_mesh"):
            self.central_viewport_panel.set_mesh(mesh, mesh_ref=mesh_ref)
        if self.mesh_viewer is not None and hasattr(self.mesh_viewer, "set_mesh"):
            self.mesh_viewer.set_mesh(mesh, mesh_ref=mesh_ref)
            self._sync_mesh_viewer_result_datasets()
        self._refresh_mesh_diagnostics_panel()
        self._refresh_saved_active_scene_status()
        return self.mesh_viewer_dialog

    def _sync_mesh_viewer_result_datasets(self) -> None:
        """Offer already-built result datasets to the 3D mesh preview panel.

        This is a GUI hand-off only. It does not open the viewer, parse artifacts,
        run solvers, generate/convert meshes, or render; the panel decides whether
        one in-memory dataset is safe to associate with its active mesh.
        """

        if self.mesh_viewer is None or not hasattr(
            self.mesh_viewer, "set_result_dataset_candidates"
        ):
            return
        associated = self.mesh_viewer.set_result_dataset_candidates(
            self._mesh_viewer_result_dataset_candidates()
        )
        if not hasattr(self.mesh_viewer, "set_result_binding"):
            return
        binding = None
        result_ref_id = ""
        if associated is not None:
            candidates = self._result_ref_candidates_for_dataset(associated)
            if len(candidates) == 1:
                from osw.core.result_mesh_binding import (
                    result_mesh_binding_from_metadata,
                )

                binding = result_mesh_binding_from_metadata(
                    candidates[0].result_ref.metadata
                )
                result_ref_id = str(
                    getattr(candidates[0].result_ref, "id", "")
                    or getattr(candidates[0].result_ref, "ref_id", "")
                )
        self.mesh_viewer.set_result_binding(
            binding,
            result_ref_id=result_ref_id,
        )

    def _mesh_viewer_result_dataset_candidates(self) -> tuple[object, ...]:
        if self.last_result_datasets:
            return tuple(self.last_result_datasets)
        if self.result_catalog is None:
            return ()
        return tuple(
            dataset
            for dataset in getattr(self.result_catalog, "datasets", ()) or ()
            if getattr(dataset, "fields", ())
        )

    def persist_mesh_viewer_result_binding(
        self,
        *,
        allow_rebind: bool = False,
    ) -> bool:
        """Persist one confirmed result/mesh binding into Project result metadata."""
        if self.mesh_viewer is None or not hasattr(self.mesh_viewer, "current_state"):
            return self._show_result_mesh_binding_status(
                "Open the 3D Mesh Preview before binding a result to a mesh."
            )

        state = self.mesh_viewer.current_state()
        mesh = getattr(state, "mesh", None)
        mesh_ref = str(getattr(state, "mesh_ref", "") or "").strip()
        if mesh is None:
            return self._show_result_mesh_binding_status(
                "No active mesh is loaded; result/mesh binding was not persisted."
            )
        if not mesh_ref:
            return self._show_result_mesh_binding_status(
                "Active mesh ref is required before result/mesh binding can be persisted."
            )

        result_dataset = (
            self.mesh_viewer.current_result_dataset()
            if hasattr(self.mesh_viewer, "current_result_dataset")
            else None
        )
        if result_dataset is None:
            return self._show_result_mesh_binding_status(
                "No result dataset is staged for this mesh; binding was not persisted."
            )

        field_id = (
            self.mesh_viewer.selected_result_field_id()
            if hasattr(self.mesh_viewer, "selected_result_field_id")
            else None
        )
        if not field_id:
            return self._show_result_mesh_binding_status(
                "Select a result field before persisting the result/mesh binding."
            )

        target_candidates = self._result_ref_candidates_for_dataset(result_dataset)
        if not target_candidates:
            dataset_id = _dataset_identifier(result_dataset)
            return self._show_result_mesh_binding_status(
                "No persisted ResultRef target matches staged ResultDataset "
                f"'{dataset_id}'. Binding was not persisted."
            )
        if len(target_candidates) > 1:
            target_candidate, selection_diagnostics = (
                self._select_result_mesh_binding_target(target_candidates)
            )
            if target_candidate is None:
                return self._show_result_mesh_binding_status(
                    "Result/mesh binding was not persisted because target selection "
                    "was cancelled.",
                    selection_diagnostics,
                )
        else:
            target_candidate = target_candidates[0]

        target_index = target_candidate.index
        target_ref = target_candidate.result_ref
        node_count, cell_count = _mesh_counts(mesh)
        from osw.mesh.identity import compute_mesh_fingerprint

        mesh_fingerprint = compute_mesh_fingerprint(mesh)
        existing_diagnostics = self._existing_result_binding_diagnostics(
            target_ref,
            active_mesh_ref=mesh_ref,
            node_count=node_count,
            cell_count=cell_count,
            active_mesh_fingerprint=mesh_fingerprint.digest,
        )
        if existing_diagnostics and not allow_rebind:
            return self._show_result_mesh_binding_status(
                "Existing result/mesh binding metadata is stale or malformed; "
                "use the explicit rebind action to replace it.",
                existing_diagnostics,
            )

        dataset_id = _dataset_identifier(result_dataset)
        confirmation_text = _result_mesh_binding_confirmation_text(
            result_ref=target_ref,
            result_dataset_id=dataset_id,
            mesh_ref=mesh_ref,
            field_id=field_id,
            node_count=node_count,
            cell_count=cell_count,
        )
        if not self._confirm_result_mesh_binding(confirmation_text):
            return self._show_result_mesh_binding_status(
                "Result/mesh binding was not persisted because confirmation was cancelled."
            )

        from osw.core.result_mesh_binding import bridge_result_dataset_mesh_binding

        proposal_metadata = getattr(result_dataset, "metadata", {}) or {}
        if not isinstance(proposal_metadata, Mapping):
            proposal_metadata = {}
        bridge = bridge_result_dataset_mesh_binding(
            target_ref,
            result_dataset_id=dataset_id,
            mesh_ref=mesh_ref,
            field_id=field_id,
            node_count=node_count,
            cell_count=cell_count,
            mesh_identity_schema="osw.mesh_identity.v1",
            mesh_fingerprint=mesh_fingerprint.digest,
            proposal_metadata=proposal_metadata,
            active_mesh_ref=mesh_ref,
            require_field_id=True,
            require_mesh_fingerprint=True,
        )
        if not bridge.valid:
            return self._show_result_mesh_binding_status(
                "Result/mesh binding metadata was not persisted.",
                bridge.diagnostics,
            )

        self.set_project(
            _project_with_replaced_result_ref(
                self.current_project,
                target_index,
                bridge.result_ref,
            )
        )
        self._project_dirty = True
        message = (
            "Persisted result/mesh binding metadata for result "
            f"'{_result_ref_display_id(target_ref)}' on mesh '{mesh_ref}' "
            f"field '{field_id}'."
        )
        if self.mesh_viewer is not None and hasattr(
            self.mesh_viewer, "mark_result_mesh_binding_persisted"
        ):
            self.mesh_viewer.mark_result_mesh_binding_persisted(message)
        if self.mesh_viewer is not None and hasattr(
            self.mesh_viewer,
            "set_result_binding",
        ):
            self.mesh_viewer.set_result_binding(
                bridge.binding,
                result_ref_id=str(
                    getattr(bridge.result_ref, "id", "")
                    or getattr(bridge.result_ref, "ref_id", "")
                ),
            )
        self._placeholder_action(message)
        return True

    def rebind_mesh_viewer_result_binding(self) -> bool:
        """Explicitly replace stale/legacy binding metadata after confirmation."""

        return self.persist_mesh_viewer_result_binding(allow_rebind=True)

    def _show_result_mesh_binding_status(
        self,
        message: str,
        diagnostics: Sequence[str] = (),
    ) -> bool:
        if self.mesh_viewer is not None and hasattr(
            self.mesh_viewer, "show_result_mesh_binding_status"
        ):
            self.mesh_viewer.show_result_mesh_binding_status(message, diagnostics)
        self._placeholder_action(message)
        return False

    def _confirm_result_mesh_binding(self, message: str) -> bool:
        if self._result_mesh_binding_confirmation is not None:
            return bool(self._result_mesh_binding_confirmation(message))
        result = QtWidgets.QMessageBox.question(
            self,
            "Bind result to active mesh",
            message,
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        return result == QtWidgets.QMessageBox.StandardButton.Yes

    def _select_result_mesh_binding_target(
        self,
        candidates: Sequence[ResultMeshBindingTargetCandidate],
    ) -> tuple[ResultMeshBindingTargetCandidate | None, tuple[str, ...]]:
        dataset_hint = (
            "Multiple persisted ResultRef targets match the staged ResultDataset; "
            "select one target before binding confirmation."
        )
        if self._result_mesh_binding_target_selector is not None:
            try:
                selection = self._result_mesh_binding_target_selector(tuple(candidates))
            except (TypeError, ValueError) as exc:
                return None, (f"ResultRef target selection failed: {exc}",)
            selected = _candidate_from_target_selection(selection, candidates)
            if selected is None:
                return None, (
                    dataset_hint,
                    "No ResultRef target was selected.",
                    *tuple(candidate.label for candidate in candidates),
                )
            return selected, ()

        labels = [candidate.label for candidate in candidates]
        selected_label, accepted = QtWidgets.QInputDialog.getItem(
            self,
            "Select result binding target",
            "Select the persisted ResultRef target to bind after confirmation:",
            labels,
            0,
            False,
        )
        if not accepted:
            return None, (
                dataset_hint,
                "ResultRef target selection was cancelled.",
                *tuple(labels),
            )
        try:
            selected_index = labels.index(selected_label)
        except ValueError:
            return None, (
                dataset_hint,
                "Selected ResultRef target is no longer available.",
            )
        return candidates[selected_index], ()

    def _result_ref_candidates_for_dataset(
        self,
        result_dataset: object,
    ) -> list[ResultMeshBindingTargetCandidate]:
        dataset_id = _dataset_identifier(result_dataset)
        if not dataset_id:
            return []
        exact = [
            _result_mesh_binding_target_candidate(
                index,
                result_ref,
                reason="exact id/ref_id match",
            )
            for index, result_ref in enumerate(self.current_project.results)
            if dataset_id
            in {str(getattr(result_ref, "id", "")), str(getattr(result_ref, "ref_id", ""))}
        ]
        if exact:
            return exact

        metadata_matches = [
            _result_mesh_binding_target_candidate(
                index,
                result_ref,
                reason="metadata match",
            )
            for index, result_ref in enumerate(self.current_project.results)
            if _result_ref_metadata_matches_dataset(result_ref, dataset_id)
        ]
        if metadata_matches:
            return metadata_matches

        dataset_source = str(getattr(result_dataset, "source", "") or "").strip()
        if not dataset_source:
            return []
        return [
            _result_mesh_binding_target_candidate(
                index,
                result_ref,
                reason="source/path match",
            )
            for index, result_ref in enumerate(self.current_project.results)
            if _result_ref_source_matches_dataset(result_ref, dataset_source)
        ]

    def _existing_result_binding_diagnostics(
        self,
        result_ref: object,
        *,
        active_mesh_ref: str,
        node_count: int | None,
        cell_count: int | None,
        active_mesh_fingerprint: str | None = None,
    ) -> tuple[str, ...]:
        from osw.core.result_mesh_binding import (
            MESH_BINDING_METADATA_KEY,
            check_result_mesh_binding,
        )

        metadata = getattr(result_ref, "metadata", {}) or {}
        if not isinstance(metadata, Mapping) or MESH_BINDING_METADATA_KEY not in metadata:
            return ()
        check = check_result_mesh_binding(
            metadata,
            active_mesh_ref=active_mesh_ref,
            node_count=node_count,
            cell_count=cell_count,
            active_mesh_fingerprint=active_mesh_fingerprint,
        )
        return () if check.valid else tuple(check.diagnostics)

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


def _project_replacing_named_selections(
    project: Project,
    selections: Sequence[object],
) -> Project:
    """Return a Project copy with exact durable NamedSelections preserved."""

    return project_with(project, selections=selections)


def _setup_record_from_payload(record_id: str, payload: Mapping[str, object]) -> object:
    from osw.core.solver_setup import (
        FixedSupportRecord,
        ForceLoadRecord,
        MaterialAssignmentRecord,
    )
    from osw.core.units import Quantity

    kind = str(payload.get("kind", ""))
    field_name = _setup_field(kind)
    common = {
        "id": record_id,
        "name": str(payload.get("name", "") or record_id),
        "target_selection_id": str(payload.get("target_selection_id", "")),
        "enabled": bool(payload.get("enabled", True)),
    }
    if field_name == "material_assignment_records":
        return MaterialAssignmentRecord(
            **common,
            material_id=str(payload.get("material_id", "")),
        )
    if field_name == "fixed_support_records":
        return FixedSupportRecord(
            **common,
            translational_dofs=tuple(
                int(item)
                for item in payload.get("translational_dofs", (1, 2, 3))
            ),
        )
    return ForceLoadRecord(
        **common,
        magnitude=Quantity(
            float(payload.get("magnitude", 0.0)),
            str(payload.get("unit", "N")),
        ),
        direction=tuple(float(item) for item in payload.get("direction", (0, 0, 0))),
        coordinate_system=str(payload.get("coordinate_system", "GLOBAL")),
        application_mode=str(payload.get("application_mode", "PER_NODE")),
    )


def _setup_field(kind: str) -> str:
    normalized = str(kind).casefold().replace("_", " ")
    if normalized == "material":
        return "material_assignment_records"
    if normalized in {"fixed support", "fixed"}:
        return "fixed_support_records"
    if normalized == "force":
        return "force_load_records"
    raise ValueError(f"Unsupported setup kind: {kind}")


def _setup_with_record(
    setup: object | None,
    kind: str,
    record: object,
    *,
    replace_existing: bool = False,
) -> object:
    from osw.core.project_schema import PhysicsSetup

    current = setup or PhysicsSetup(
        setup_id="structural",
        name="Structural Setup",
        analysis_type="linear_static",
        domain="STRUCTURAL",
    )
    field_name = _setup_field(kind)
    records = list(getattr(current, field_name))
    if replace_existing:
        records = [
            record if getattr(item, "id", "") == getattr(record, "id", "") else item
            for item in records
        ]
    else:
        records.append(record)
    return replace(current, **{field_name: records})


def _setup_without_record(
    setup: object | None,
    kind: str,
    record_id: str,
) -> object:
    from osw.core.project_schema import PhysicsSetup

    current = setup or PhysicsSetup()
    field_name = _setup_field(kind)
    records = [
        item
        for item in getattr(current, field_name)
        if getattr(item, "id", "") != record_id
    ]
    return replace(current, **{field_name: records})


def _project_replacing_primary_physics(project: Project, setup: object) -> Project:
    physics = list(project.physics)
    if physics:
        physics[0] = setup
    else:
        physics.append(setup)
    return project_with(project, physics=physics)


def _project_with_report_screenshots(project: Project, assets: object) -> Project:
    """Return a copy of ``project`` merging ``assets`` into report_screenshots.

    Existing persisted assets are kept unless superseded by a new asset with the
    same id (new wins). All other project fields, including named selections, are
    preserved. Only the transient candidate list feeds this; no image bytes are
    copied and no project file is saved.
    """
    new_assets = tuple(assets or ())
    new_ids = {getattr(asset, "id", "") for asset in new_assets}
    kept = [
        asset
        for asset in getattr(project, "report_screenshots", ()) or ()
        if getattr(asset, "id", "") not in new_ids
    ]
    return _project_replacing_report_screenshots(project, [*kept, *new_assets])


def _project_replacing_report_screenshots(
    project: Project, assets: Sequence[object]
) -> Project:
    """Return a Project copy with the exact ordered screenshot asset list."""
    return project_with(project, report_screenshots=assets)


def _project_with_mesh_ref(project: Project, mesh_ref: object) -> Project:
    meshes = [
        mesh
        for mesh in project.mesh_refs
        if getattr(mesh, "id", "") != getattr(mesh_ref, "id", "")
        and getattr(mesh, "path", "") != getattr(mesh_ref, "path", "")
    ]
    meshes.append(mesh_ref)
    return project_with(project, meshes=meshes)


def _project_with_replaced_result_ref(
    project: Project,
    result_index: int,
    result_ref: object,
) -> Project:
    results = list(project.results)
    results[result_index] = result_ref
    return project_with(project, results=results)


def _project_with_script_ref(project: Project, script_ref: object) -> Project:
    scripts = [
        script
        for script in project.script_refs
        if getattr(script, "id", "") != getattr(script_ref, "id", "")
        and getattr(script, "path", "") != getattr(script_ref, "path", "")
    ]
    scripts.append(script_ref)
    return project_with(project, scripts=scripts)


def _project_with_boundary_curve(project: Project, curve: object) -> Project:
    curves = [
        item
        for item in project.boundary_curves
        if getattr(item, "curve_id", "") != getattr(curve, "curve_id", "")
    ]
    curves.append(curve)
    return project_with(project, boundary_curves=curves)


def _dataset_identifier(result_dataset: object) -> str:
    return str(getattr(result_dataset, "dataset_id", "") or "").strip()


def _candidate_from_target_selection(
    selection: object | None,
    candidates: Sequence[ResultMeshBindingTargetCandidate],
) -> ResultMeshBindingTargetCandidate | None:
    if selection is None:
        return None
    if isinstance(selection, ResultMeshBindingTargetCandidate):
        return selection if selection in candidates else None
    try:
        selected_index = int(selection)
    except (TypeError, ValueError, OverflowError):
        return None
    if 0 <= selected_index < len(candidates):
        return candidates[selected_index]
    project_index_matches = [
        candidate for candidate in candidates if candidate.index == selected_index
    ]
    if len(project_index_matches) == 1:
        return project_index_matches[0]
    return None


def _result_mesh_binding_target_candidate(
    index: int,
    result_ref: object,
    *,
    reason: str,
) -> ResultMeshBindingTargetCandidate:
    diagnostics = _result_ref_target_diagnostics(result_ref)
    return ResultMeshBindingTargetCandidate(
        index=index,
        result_ref=result_ref,
        reason=reason,
        label=_result_mesh_binding_target_label(
            index=index,
            result_ref=result_ref,
            reason=reason,
            diagnostics=diagnostics,
        ),
        diagnostics=diagnostics,
    )


def _result_mesh_binding_target_label(
    *,
    index: int,
    result_ref: object,
    reason: str,
    diagnostics: Sequence[str] = (),
) -> str:
    display_id = _result_ref_display_id(result_ref) or "(unnamed)"
    ref_id = str(getattr(result_ref, "ref_id", "") or "").strip()
    path = _result_ref_source_hint(result_ref) or "(no source/path)"
    kind = str(getattr(result_ref, "kind", "") or "").strip() or "(unknown kind)"
    binding_state = _result_ref_binding_state(result_ref)
    source_mesh_ref = _result_ref_metadata_text(result_ref, "source_mesh_ref")
    source_mesh = (
        f"source_mesh_ref={source_mesh_ref}"
        if source_mesh_ref
        else "source_mesh_ref=(none)"
    )
    diagnostic_text = (
        f"; diagnostics={'; '.join(diagnostics)}" if diagnostics else ""
    )
    ref_text = f"; ref_id={ref_id}" if ref_id and ref_id != display_id else ""
    return (
        f"{reason}: result[{index}] id={display_id}{ref_text}; path={path}; "
        f"kind={kind}; {source_mesh}; {binding_state}{diagnostic_text}"
    )


def _result_ref_display_id(result_ref: object) -> str:
    return str(
        getattr(result_ref, "id", "")
        or getattr(result_ref, "ref_id", "")
        or getattr(result_ref, "path", "")
        or ""
    ).strip()


def _result_ref_source_hint(result_ref: object) -> str:
    path = str(getattr(result_ref, "path", "") or "").strip()
    if path:
        return path
    metadata = getattr(result_ref, "metadata", {}) or {}
    if not isinstance(metadata, Mapping):
        return ""
    for key in ("source", "source_path", "result_source"):
        value = str(metadata.get(key, "") or "").strip()
        if value:
            return value
    return ""


def _result_ref_metadata_text(result_ref: object, key: str) -> str:
    metadata = getattr(result_ref, "metadata", {}) or {}
    if not isinstance(metadata, Mapping):
        return ""
    return str(metadata.get(key, "") or "").strip()


def _result_ref_binding_state(result_ref: object) -> str:
    metadata = getattr(result_ref, "metadata", {}) or {}
    if not isinstance(metadata, Mapping):
        return "binding=metadata unavailable"
    binding = metadata.get("mesh_binding")
    if not isinstance(binding, Mapping):
        return "binding=none"
    mesh_ref = str(binding.get("mesh_ref", "") or "").strip() or "(unknown mesh)"
    field_id = str(binding.get("field_id", "") or "").strip() or "(no field)"
    return f"binding=mesh:{mesh_ref}, field:{field_id}"


def _result_ref_target_diagnostics(result_ref: object) -> tuple[str, ...]:
    metadata = getattr(result_ref, "metadata", {}) or {}
    if not isinstance(metadata, Mapping):
        return ("ResultRef metadata is not a mapping.",)
    binding = metadata.get("mesh_binding")
    if binding is None:
        return ()
    if not isinstance(binding, Mapping):
        return ("Existing mesh_binding metadata is malformed.",)
    return ()


def _result_ref_metadata_matches_dataset(result_ref: object, dataset_id: str) -> bool:
    metadata = getattr(result_ref, "metadata", {}) or {}
    if not isinstance(metadata, Mapping):
        return False
    return any(
        str(metadata.get(key, "") or "").strip() == dataset_id
        for key in ("result_dataset_id", "dataset_id")
    )


def _result_ref_source_matches_dataset(result_ref: object, dataset_source: str) -> bool:
    if str(getattr(result_ref, "path", "") or "").strip() == dataset_source:
        return True
    metadata = getattr(result_ref, "metadata", {}) or {}
    if not isinstance(metadata, Mapping):
        return False
    return any(
        str(metadata.get(key, "") or "").strip() == dataset_source
        for key in ("source", "source_path", "result_source")
    )


def _mesh_counts(mesh: object) -> tuple[int | None, int | None]:
    points = getattr(mesh, "points", None)
    try:
        node_count = len(points) if points is not None else None
    except TypeError:
        node_count = None

    cells = getattr(mesh, "cells", None)
    if cells is None:
        return node_count, None
    cell_count = 0
    try:
        for block in cells:
            count = getattr(block, "count", None)
            if count is not None:
                cell_count += int(count)
            else:
                cell_count += len(getattr(block, "data", ()) or ())
    except (TypeError, ValueError):
        return node_count, None
    return node_count, cell_count


def _is_project_tree_mesh_item(
    kind: str,
    icon_key: str,
    payload: Mapping[str, str],
) -> bool:
    return kind == "mesh_ref" or (icon_key == "mesh_file" and bool(payload.get("mesh_ref")))


def _selected_mesh_ref(payload: Mapping[str, str], label: str) -> str:
    return (
        str(
            payload.get("mesh_ref")
            or payload.get("id")
            or payload.get("ref_id")
            or payload.get("path")
            or payload.get("name")
            or label
            or ""
        )
        .strip()
    )


def _mesh_aliases_for_imported_mesh(mesh: object, explicit_ref: object) -> tuple[str, ...]:
    values: list[object] = [
        explicit_ref,
        getattr(mesh, "id", ""),
        getattr(mesh, "ref_id", ""),
        getattr(mesh, "name", ""),
        getattr(mesh, "path", ""),
        getattr(mesh, "source_path", ""),
    ]
    info = getattr(mesh, "info", None)
    if info is not None:
        values.extend(
            (
                getattr(info, "source", ""),
                getattr(info, "source_path", ""),
            )
        )
    return _mesh_ref_aliases(values)


def _mesh_ref_aliases(values: Sequence[object]) -> tuple[str, ...]:
    aliases: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            aliases.append(text)
            path_name = Path(text).name
            if path_name and path_name not in seen:
                seen.add(path_name)
                aliases.append(path_name)
    return tuple(aliases)


def _metadata_mesh_source_path(payload: Mapping[str, str]) -> str:
    return str(
        payload.get("path")
        or payload.get("source_path")
        or ""
    ).strip()


def _metadata_mesh_missing_path_diagnostics(source_path: str) -> tuple[str, ...]:
    if source_path:
        return (
            f"Stored mesh path '{source_path}' is not an absolute load path. "
            "Choose the mesh file explicitly before loading MeshData.",
            "MeshData load was canceled; the active mesh was not changed.",
        )
    return (
        "No source path is stored for the selected MeshRef. "
        "Choose a mesh file explicitly before loading MeshData.",
        "MeshData load was canceled; the active mesh was not changed.",
    )


def _mesh_import_diagnostics(result: object) -> tuple[str, ...]:
    diagnostics = getattr(result, "diagnostics", None)
    if diagnostics is None:
        return ()
    if hasattr(diagnostics, "summary"):
        summary = str(diagnostics.summary() or "").strip()
        return (summary,) if summary else ()
    if isinstance(diagnostics, Sequence) and not isinstance(diagnostics, str | bytes):
        return tuple(str(item) for item in diagnostics if str(item).strip())
    text = str(diagnostics or "").strip()
    return (text,) if text else ()


def _metadata_mesh_mismatch_diagnostics(
    payload: Mapping[str, str],
    selected_path: Path,
    result: object,
) -> tuple[str, ...]:
    expected_path = _metadata_mesh_source_path(payload)
    if expected_path and Path(expected_path).is_absolute():
        if not _same_mesh_path(Path(expected_path), selected_path):
            return (
                "Loaded mesh path does not match the selected MeshRef source path.",
                f"Selected MeshRef path: {expected_path}",
                f"Loaded mesh path: {selected_path}",
                "MeshData was not made active; choose the matching mesh file explicitly.",
            )

    expected_format = str(payload.get("format", "") or "").strip().lower().lstrip(".")
    actual_format = str(getattr(result, "format", "") or "").strip().lower().lstrip(".")
    if expected_format and actual_format and expected_format != actual_format:
        return (
            "Loaded mesh format does not match the selected MeshRef metadata.",
            f"Selected MeshRef format: {expected_format}",
            f"Loaded mesh format: {actual_format}",
            "MeshData was not made active; choose the matching mesh file explicitly.",
        )
    return ()


def _same_mesh_path(expected: Path, actual: Path) -> bool:
    expected_text = str(expected)
    actual_text = str(actual)
    if expected_text == actual_text:
        return True
    if not (expected.is_absolute() and actual.is_absolute()):
        return False
    try:
        return expected.resolve(strict=False) == actual.resolve(strict=False)
    except OSError:
        return expected == actual


def _result_mesh_binding_confirmation_text(
    *,
    result_ref: object,
    result_dataset_id: str,
    mesh_ref: str,
    field_id: str,
    node_count: int | None,
    cell_count: int | None,
) -> str:
    signature = (
        f"nodes={node_count}, cells={cell_count}"
        if node_count is not None and cell_count is not None
        else "mesh count signature unavailable"
    )
    return (
        "Persist result/mesh binding metadata?\n\n"
        f"ResultRef: {getattr(result_ref, 'id', '')}\n"
        f"ResultDataset: {result_dataset_id}\n"
        f"Mesh: {mesh_ref}\n"
        f"Field: {field_id}\n"
        f"Signature: {signature}\n\n"
        "This updates project metadata only and does not save the project file."
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
