"""PySide6 mesh viewer panel for the 3D workspace (MVP SLICE-004).

The panel displays a mesh summary and previews the mesh through the reviewed
post-level scene shell via an injected scene adapter. It owns no meshes, parses
no solvers, generates no meshes, and runs no external process: rendering is
delegated to the adapter, and PyVista stays optional and lazy. A local scene
screenshot record is artifact metadata only -- not a release asset and not
validation evidence. The panel exposes no direct backend-execution control.
"""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.workspace_scene_view_model import (
    DefaultSceneAdapter,
    MeshViewerState,
    SceneAdapterProtocol,
    mesh_input_ref,
    mesh_scalar_field_names,
    mesh_summary_rows,
    scene_view_state_from_toggles,
    summary_rows_to_text,
)
from osw.mesh.mesh_model import MeshData
from osw.post.pyvista_scene import PyVistaUnavailableError
from osw.post.scene_model import SceneScreenshotRecord

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

_NONE_FIELD = "(none)"
_NO_MESH_TEXT = "No mesh loaded."
_MESH_READY_TEXT = "Mesh loaded. Select 'Load mesh preview' to build the scene."
_PREVIEW_LOADED_TEXT = "Mesh preview loaded."
_CAPTURED_TEXT = "Captured scene metadata."
_PYVISTA_MISSING_TEXT = (
    "PyVista unavailable -- install the visualization extra to render 3D scenes."
)


class MeshViewerPanel(_BaseWidget):
    """3D workspace panel: mesh summary plus scene-shell preview via an adapter."""

    def __init__(
        self,
        parent: object | None = None,
        *,
        scene_adapter: SceneAdapterProtocol | None = None,
    ) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswThreeDMeshViewerPanel")
        self._adapter: SceneAdapterProtocol = scene_adapter or DefaultSceneAdapter()
        self._state = MeshViewerState()

        self.title_label = QtWidgets.QLabel("3D Mesh Preview", self)
        self.title_label.setObjectName("oswMeshViewerTitle")

        self.summary_label = QtWidgets.QLabel(_NO_MESH_TEXT, self)
        self.summary_label.setObjectName("oswMeshViewerSummary")
        self.summary_label.setWordWrap(True)

        self.empty_state = QtWidgets.QLabel(_NO_MESH_TEXT, self)
        self.empty_state.setObjectName("oswMeshViewerEmptyState")
        self.empty_state.setWordWrap(True)

        self.surface_toggle = QtWidgets.QCheckBox("Surface", self)
        self.surface_toggle.setObjectName("surfaceToggle")
        self.surface_toggle.setChecked(True)
        self.edge_toggle = QtWidgets.QCheckBox("Edges", self)
        self.edge_toggle.setObjectName("edgeToggle")
        self.axis_toggle = QtWidgets.QCheckBox("Axes", self)
        self.axis_toggle.setObjectName("axisToggle")
        self.axis_toggle.setChecked(True)
        self.grid_toggle = QtWidgets.QCheckBox("Grid", self)
        self.grid_toggle.setObjectName("gridToggle")

        self.scalar_label = QtWidgets.QLabel("Color by:", self)
        self.scalar_label.setObjectName("oswMeshViewerScalarLabel")
        self.scalar_selector = QtWidgets.QComboBox(self)
        self.scalar_selector.setObjectName("oswMeshViewerScalarSelector")
        self.scalar_selector.addItem(_NONE_FIELD)

        self.load_button = QtWidgets.QPushButton("Load mesh preview", self)
        self.load_button.setObjectName("oswMeshViewerLoadButton")
        self.capture_button = QtWidgets.QPushButton("Capture scene metadata", self)
        self.capture_button.setObjectName("oswMeshViewerCaptureButton")

        self.status_label = QtWidgets.QLabel(_NO_MESH_TEXT, self)
        self.status_label.setObjectName("oswMeshViewerStatus")
        self.status_label.setWordWrap(True)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswMeshViewerDiagnostics")

        toggles = QtWidgets.QHBoxLayout()
        toggles.addWidget(self.surface_toggle)
        toggles.addWidget(self.edge_toggle)
        toggles.addWidget(self.axis_toggle)
        toggles.addWidget(self.grid_toggle)
        toggles.addStretch(1)

        fields = QtWidgets.QHBoxLayout()
        fields.addWidget(self.scalar_label)
        fields.addWidget(self.scalar_selector)
        fields.addStretch(1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.load_button)
        buttons.addWidget(self.capture_button)
        buttons.addStretch(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self.title_label)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.empty_state)
        layout.addLayout(toggles)
        layout.addLayout(fields)
        layout.addLayout(buttons)
        layout.addWidget(self.status_label)
        layout.addWidget(self.diagnostics_list)

        self.load_button.clicked.connect(lambda _checked=False: self.load_mesh_preview())
        self.capture_button.clicked.connect(
            lambda _checked=False: self._on_capture_requested()
        )
        self._set_controls_enabled(False)
        self._render_state()

    # -- public API ---------------------------------------------------------

    def set_mesh(self, mesh: MeshData, *, mesh_ref: str = "") -> None:
        """Attach an in-memory mesh and show its summary (no rendering)."""
        self._state = MeshViewerState(
            mesh=mesh,
            mesh_ref=mesh_ref,
            selected_selection_ids=self._state.selected_selection_ids,
            summary_rows=mesh_summary_rows(mesh),
            status_message=_MESH_READY_TEXT,
        )
        self._populate_scalar_selector(mesh)
        self._set_controls_enabled(True)
        self._render_state()

    def set_selected_selection_ids(self, selection_ids: object) -> None:
        """Record selected NamedSelection ids for the next preview build."""
        self._state.selected_selection_ids = tuple(str(item) for item in selection_ids)

    def clear_mesh(self) -> None:
        """Return the panel to its friendly empty state."""
        self._state = MeshViewerState(status_message=_NO_MESH_TEXT)
        self._populate_scalar_selector(None)
        self._set_controls_enabled(False)
        self._render_state()

    def load_mesh_preview(self) -> Any:
        """Build the scene input/state from the toggles and call the adapter."""
        mesh = self._state.mesh
        if mesh is None:
            self._state.status_message = _NO_MESH_TEXT
            self._render_state()
            return None

        scene_input = mesh_input_ref(
            self._state.mesh_ref,
            self._state.selected_selection_ids,
        )
        color_by = self._selected_color_by()
        scene_state = scene_view_state_from_toggles(
            show_surface=self.surface_toggle.isChecked(),
            show_edges=self.edge_toggle.isChecked(),
            show_axes=self.axis_toggle.isChecked(),
            show_grid=self.grid_toggle.isChecked(),
            color_by=color_by,
            selected_selection_ids=self._state.selected_selection_ids,
        )
        self._state.scene_input = scene_input
        self._state.scene_state = scene_state

        # Friendly warning if the chosen scalar is not present on the mesh; the
        # summary and preview still proceed (no crash, no rendering here).
        field_warnings: tuple[str, ...] = ()
        if color_by is not None and color_by not in mesh_scalar_field_names(mesh):
            field_warnings = (f"Scalar field '{color_by}' is not present on the mesh.",)

        try:
            result = self._adapter.load_mesh(mesh, scene_input, scene_state)
        except PyVistaUnavailableError as exc:
            self._state.pyvista_available = False
            self._state.status_message = _PYVISTA_MISSING_TEXT
            self._state.warning_messages = (str(exc), *field_warnings)
            self._render_state()
            return None

        self._state.pyvista_available = True
        self._state.status_message = _PREVIEW_LOADED_TEXT
        self._state.warning_messages = (
            *tuple(getattr(result, "warnings", ()) or ()),
            *field_warnings,
        )
        self._render_state()
        return result

    def capture_scene_metadata(
        self,
        target_path: object,
        *,
        record_id: str = "mesh-viewer-scene",
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord | None:
        """Delegate to the adapter to record local scene screenshot metadata."""
        mesh = self._state.mesh
        if mesh is None:
            self._state.status_message = _NO_MESH_TEXT
            self._render_state()
            return None

        scene_state = self._state.scene_state
        try:
            record = self._adapter.export_screenshot_record(
                str(target_path),
                record_id=record_id,
                scene_state=scene_state,
                mesh=mesh,
                mesh_ref=self._state.mesh_ref or None,
                selection_ids=self._state.selected_selection_ids,
                caption=caption,
                created_by=created_by,
            )
        except PyVistaUnavailableError as exc:
            self._state.pyvista_available = False
            self._state.status_message = _PYVISTA_MISSING_TEXT
            self._state.warning_messages = (str(exc),)
            self._render_state()
            return None

        self._state.screenshot_record = record
        self._state.status_message = _CAPTURED_TEXT
        self._render_state()
        return record

    def current_state(self) -> MeshViewerState:
        return self._state

    def current_screenshot_record(self) -> SceneScreenshotRecord | None:
        return self._state.screenshot_record

    # -- internal helpers ---------------------------------------------------

    def _on_capture_requested(self) -> None:
        # The button cannot supply a target path; a caller drives the export.
        self._state.status_message = (
            "Capture requires a target path from the caller."
        )
        self._render_state()

    def _populate_scalar_selector(self, mesh: MeshData | None) -> None:
        """Fill the scalar selector with '(none)' + the mesh's field names."""
        self.scalar_selector.blockSignals(True)
        self.scalar_selector.clear()
        self.scalar_selector.addItem(_NONE_FIELD)
        for name in mesh_scalar_field_names(mesh):
            self.scalar_selector.addItem(name)
        self.scalar_selector.setCurrentIndex(0)
        self.scalar_selector.blockSignals(False)

    def _selected_color_by(self) -> str | None:
        selected = self.scalar_selector.currentText()
        if not selected or selected == _NONE_FIELD:
            return None
        return selected

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.load_button.setEnabled(enabled)
        self.capture_button.setEnabled(enabled)

    def _render_state(self) -> None:
        has_mesh = self._state.mesh is not None
        if has_mesh and self._state.summary_rows:
            self.summary_label.setText(summary_rows_to_text(self._state.summary_rows))
        else:
            self.summary_label.setText(_NO_MESH_TEXT)
        self.empty_state.setVisible(not has_mesh)
        self.status_label.setText(self._state.status_message or _NO_MESH_TEXT)

        self.diagnostics_list.clear()
        for warning in self._state.warning_messages:
            self.diagnostics_list.addItem(warning)


def build_mesh_viewer_panel(
    parent: object | None = None,
    *,
    scene_adapter: SceneAdapterProtocol | None = None,
) -> object:
    """Factory mirroring the other GUI widget builders."""
    return MeshViewerPanel(parent, scene_adapter=scene_adapter)
