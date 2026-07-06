"""PySide6 mesh viewer panel for the 3D workspace (MVP SLICE-004).

The panel displays a mesh summary and previews the mesh through the reviewed
post-level scene shell via an injected scene adapter. It owns no meshes, parses
no solvers, generates no meshes, and runs no external process: rendering is
delegated to the adapter, and PyVista stays optional and lazy. A local scene
screenshot record is artifact metadata only -- not a release asset and not
validation evidence. The panel exposes no direct backend-execution control.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
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
from osw.post.result_field_mapping import map_result_field_to_mesh, result_field_names
from osw.post.scene_model import SceneScreenshotRecord

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

_NONE_FIELD = "(none)"
_RESULT_PREFIX = "result: "
_NO_MESH_TEXT = "No mesh loaded."
_MESH_READY_TEXT = "Mesh loaded. Select 'Load mesh preview' to build the scene."
_PREVIEW_LOADED_TEXT = "Mesh preview loaded."
_CAPTURED_TEXT = "Captured scene metadata."
_PYVISTA_MISSING_TEXT = (
    "PyVista unavailable -- install the visualization extra to render 3D scenes."
)
_NO_ACTIVE_MESH_TEXT = "No active mesh is loaded; result fields were not associated."
_NO_RESULT_DATASETS_TEXT = "No result datasets are available for this mesh."
_AMBIGUOUS_RESULT_DATASETS_TEXT = (
    "Multiple result datasets could match this mesh; choose one explicitly."
)
_NO_STAGED_BINDING_TEXT = "No result dataset is staged for persisted binding."
_BINDING_HANDLER_MISSING_TEXT = (
    "Persisted binding requires a MainWindow confirmation handler."
)
_PERSISTED_BINDING_TEXT = "Persisted result/mesh binding metadata."
_MESH_REF_METADATA_KEYS = (
    "mesh_ref",
    "source_mesh_ref",
    "source_mesh_id",
    "mesh_id",
    "workflow_item_id",
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
        self._result_dataset: object | None = None
        self._result_dataset_ref: str = ""
        self._result_field_lookup: dict[str, object] = {}
        self._bind_result_callback: Callable[[], object] | None = None
        self._binding_status_message = _NO_STAGED_BINDING_TEXT
        self._binding_persisted = False

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
        self.bind_result_button = QtWidgets.QPushButton(
            "Bind result to active mesh...", self
        )
        self.bind_result_button.setObjectName("oswMeshViewerBindResultButton")

        self.binding_status_label = QtWidgets.QLabel(_NO_STAGED_BINDING_TEXT, self)
        self.binding_status_label.setObjectName("oswMeshViewerBindingStatus")
        self.binding_status_label.setWordWrap(True)

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
        buttons.addWidget(self.bind_result_button)
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
        layout.addWidget(self.binding_status_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.diagnostics_list)

        self.load_button.clicked.connect(lambda _checked=False: self.load_mesh_preview())
        self.capture_button.clicked.connect(
            lambda _checked=False: self._on_capture_requested()
        )
        self.bind_result_button.clicked.connect(
            lambda _checked=False: self._on_bind_result_requested()
        )
        self.scalar_selector.currentTextChanged.connect(
            lambda _text: self._on_scalar_selection_changed()
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
        self._refresh_binding_status()
        self._render_state()

    def set_selected_selection_ids(self, selection_ids: object) -> None:
        """Record selected NamedSelection ids for the next preview build."""
        self._state.selected_selection_ids = tuple(str(item) for item in selection_ids)

    def set_result_dataset(self, result_dataset: object | None) -> None:
        """Attach an already-built result dataset whose fields can color the mesh.

        Its scalar fields are offered in the selector (namespaced ``result: <name>``)
        and, on selection, mapped onto a MeshData overlay for the existing color-by
        path. This consumes built values only -- no solver run, no artifact parse.
        """
        self._result_dataset = result_dataset
        self._result_dataset_ref = str(getattr(result_dataset, "dataset_id", "") or "")
        self._result_field_lookup = {
            str(getattr(item, "name", "")): item
            for item in getattr(result_dataset, "fields", ()) or ()
            if getattr(item, "name", "")
        }
        self._populate_scalar_selector(self._state.mesh)
        self._refresh_binding_status()
        self._render_state()

    def set_bind_result_callback(self, callback: Callable[[], object] | None) -> None:
        """Connect the panel action to a MainWindow-owned confirmation flow."""
        self._bind_result_callback = callback

    def current_result_dataset(self) -> object | None:
        return self._result_dataset

    def current_result_dataset_id(self) -> str:
        return self._result_dataset_ref

    def selected_result_field_id(self) -> str | None:
        selected = self.scalar_selector.currentText()
        if selected.startswith(_RESULT_PREFIX):
            return selected[len(_RESULT_PREFIX):] or None
        return None

    def show_result_mesh_binding_status(
        self,
        message: str,
        diagnostics: Sequence[str] = (),
        *,
        persisted: bool = False,
    ) -> None:
        """Display persistence diagnostics without mutating project data."""
        self._binding_persisted = persisted
        self._binding_status_message = str(message)
        self._state.status_message = str(message)
        self._state.warning_messages = tuple(str(item) for item in diagnostics)
        self._render_state()

    def show_active_mesh_status(
        self,
        message: str,
        diagnostics: Sequence[str] = (),
    ) -> None:
        """Display active-mesh selection diagnostics without changing the mesh."""
        self._state.status_message = str(message)
        self._state.warning_messages = tuple(str(item) for item in diagnostics)
        self._render_state()

    def mark_result_mesh_binding_persisted(self, message: str = _PERSISTED_BINDING_TEXT) -> None:
        self.show_result_mesh_binding_status(message, persisted=True)

    def set_result_dataset_candidates(self, result_datasets: object) -> object | None:
        """Associate a safe in-memory result dataset candidate with the active mesh.

        This is the first auto-association route for the 3D workspace. It consumes
        already-built datasets only: exact mesh-ref metadata wins; otherwise a
        single unambiguous compatible candidate may be staged. Ambiguous or
        incompatible candidates stay diagnostic-first and do not run solvers,
        parse artifacts, generate meshes, convert meshes, or render.
        """

        mesh = self._state.mesh
        datasets = _candidate_datasets(result_datasets)
        if mesh is None:
            return self._clear_result_dataset_association(_NO_ACTIVE_MESH_TEXT)
        if not datasets:
            return self._clear_result_dataset_association(_NO_RESULT_DATASETS_TEXT)

        mesh_ref = self._state.mesh_ref
        exact_matches = (
            tuple(
                dataset
                for dataset in datasets
                if mesh_ref and mesh_ref in _dataset_mesh_refs(dataset)
            )
            if mesh_ref
            else ()
        )
        if exact_matches:
            return self._associate_from_exact_matches(mesh, mesh_ref, exact_matches)

        if len(datasets) > 1:
            return self._clear_result_dataset_association(_AMBIGUOUS_RESULT_DATASETS_TEXT)

        dataset = datasets[0]
        dataset_refs = _dataset_mesh_refs(dataset)
        if dataset_refs:
            dataset_id = _dataset_id(dataset)
            active = mesh_ref or "(unspecified)"
            refs = ", ".join(dataset_refs)
            return self._clear_result_dataset_association(
                f"Result dataset '{dataset_id}' refers to mesh '{refs}' but the "
                f"active mesh is '{active}'."
            )

        field_name, diagnostics = _first_compatible_result_field(mesh, dataset)
        if field_name is None:
            return self._clear_result_dataset_association(
                _no_matching_field_message(dataset), diagnostics
            )
        dataset_id = _dataset_id(dataset)
        return self._apply_result_dataset_association(
            dataset,
            f"Staged result dataset '{dataset_id}' for active mesh "
            f"'{mesh_ref or '(unspecified)'}'.",
        )

    def clear_mesh(self) -> None:
        """Return the panel to its friendly empty state."""
        self._state = MeshViewerState(status_message=_NO_MESH_TEXT)
        self._populate_scalar_selector(None)
        self._set_controls_enabled(False)
        self._refresh_binding_status()
        self._render_state()

    def load_mesh_preview(self) -> Any:
        """Build the scene input/state from the toggles and call the adapter."""
        mesh = self._state.mesh
        if mesh is None:
            self._state.status_message = _NO_MESH_TEXT
            self._render_state()
            return None

        render_mesh, color_by, result_dataset_ref, field_id, field_warnings = (
            self._resolve_color_source(mesh)
        )
        scene_input = mesh_input_ref(
            self._state.mesh_ref,
            self._state.selected_selection_ids,
            result_dataset_ref=result_dataset_ref,
            field_id=field_id,
        )
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

        try:
            result = self._adapter.load_mesh(render_mesh, scene_input, scene_state)
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

    def _on_bind_result_requested(self) -> None:
        if self._bind_result_callback is None:
            self.show_result_mesh_binding_status(_BINDING_HANDLER_MISSING_TEXT)
            return
        self._bind_result_callback()

    def _on_scalar_selection_changed(self) -> None:
        if self._result_dataset is None:
            return
        self._refresh_binding_status()
        self._render_state()

    def _refresh_binding_status(self) -> None:
        self._binding_persisted = False
        mesh = self._state.mesh
        if mesh is None:
            self._binding_status_message = _NO_ACTIVE_MESH_TEXT
            return
        if self._result_dataset is None:
            self._binding_status_message = _NO_STAGED_BINDING_TEXT
            return
        dataset_id = self._result_dataset_ref or _dataset_id(self._result_dataset)
        mesh_ref = self._state.mesh_ref or "(unspecified)"
        field_id = self.selected_result_field_id()
        field_text = (
            f" field '{field_id}'"
            if field_id
            else "; select a result field before persisting"
        )
        self._binding_status_message = (
            f"Result dataset '{dataset_id}' is staged for active mesh '{mesh_ref}'"
            f"{field_text}. Binding is not persisted."
        )

    def _populate_scalar_selector(self, mesh: MeshData | None) -> None:
        """Fill the scalar selector: '(none)' + mesh fields + namespaced result fields."""
        current = self.scalar_selector.currentText()
        self.scalar_selector.blockSignals(True)
        self.scalar_selector.clear()
        items = [_NONE_FIELD]
        for name in mesh_scalar_field_names(mesh):
            items.append(name)
        for name in result_field_names(self._result_dataset):
            items.append(f"{_RESULT_PREFIX}{name}")
        self.scalar_selector.addItems(items)
        self.scalar_selector.setCurrentText(current if current in items else _NONE_FIELD)
        self.scalar_selector.blockSignals(False)

    def _associate_from_exact_matches(
        self, mesh: MeshData, mesh_ref: str, datasets: tuple[object, ...]
    ) -> object | None:
        compatible: list[object] = []
        diagnostics: list[str] = []
        for dataset in datasets:
            field_name, field_diagnostics = _first_compatible_result_field(mesh, dataset)
            if field_name is not None:
                compatible.append(dataset)
            else:
                diagnostics.extend(field_diagnostics)

        if len(compatible) == 1:
            dataset = compatible[0]
            dataset_id = _dataset_id(dataset)
            return self._apply_result_dataset_association(
                dataset,
                f"Associated result dataset '{dataset_id}' with active mesh '{mesh_ref}'.",
            )
        if len(compatible) > 1:
            return self._clear_result_dataset_association(_AMBIGUOUS_RESULT_DATASETS_TEXT)
        return self._clear_result_dataset_association(
            _no_matching_field_message(datasets[0]), tuple(diagnostics)
        )

    def _apply_result_dataset_association(
        self,
        result_dataset: object,
        status_message: str,
        diagnostics: Sequence[str] = (),
    ) -> object:
        self.set_result_dataset(result_dataset)
        self._state.status_message = status_message
        self._state.warning_messages = tuple(str(item) for item in diagnostics)
        self._render_state()
        return result_dataset

    def _clear_result_dataset_association(
        self,
        status_message: str,
        diagnostics: Sequence[str] = (),
    ) -> None:
        self.set_result_dataset(None)
        self._state.status_message = status_message
        self._state.warning_messages = tuple(str(item) for item in diagnostics)
        self._render_state()
        return None

    def _resolve_color_source(
        self, mesh: MeshData
    ) -> tuple[MeshData, str | None, str | None, str | None, tuple[str, ...]]:
        """Resolve the selection to (render_mesh, color_by, result_ref, field_id, warnings).

        A mesh point/cell field colors the base mesh; a namespaced result field is
        mapped onto an overlay MeshData (or, on mismatch, skipped with a friendly
        warning). ``'(none)'`` colors nothing.
        """
        selected = self.scalar_selector.currentText()
        if not selected or selected == _NONE_FIELD:
            return mesh, None, None, None, ()
        if selected.startswith(_RESULT_PREFIX):
            field_name = selected[len(_RESULT_PREFIX):]
            result_field = self._result_field_lookup.get(field_name)
            if result_field is None:
                return mesh, None, None, None, (f"Result field '{field_name}' is not available.",)
            mapping = map_result_field_to_mesh(mesh, result_field)
            if not mapping.applied:
                return mesh, None, None, None, mapping.diagnostics
            return (
                mapping.mesh_data,
                mapping.field_name,
                self._result_dataset_ref or None,
                field_name,
                (),
            )
        warnings: tuple[str, ...] = ()
        if selected not in mesh_scalar_field_names(mesh):
            warnings = (f"Scalar field '{selected}' is not present on the mesh.",)
        return mesh, selected, None, None, warnings

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.load_button.setEnabled(enabled)
        self.capture_button.setEnabled(enabled)
        self.bind_result_button.setEnabled(enabled and self._result_dataset is not None)

    def _render_state(self) -> None:
        has_mesh = self._state.mesh is not None
        if has_mesh and self._state.summary_rows:
            self.summary_label.setText(summary_rows_to_text(self._state.summary_rows))
        else:
            self.summary_label.setText(_NO_MESH_TEXT)
        self.empty_state.setVisible(not has_mesh)
        self.status_label.setText(self._state.status_message or _NO_MESH_TEXT)
        self.binding_status_label.setText(self._binding_status_message)
        self.bind_result_button.setEnabled(has_mesh and self._result_dataset is not None)

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


def _candidate_datasets(result_datasets: object) -> tuple[object, ...]:
    if result_datasets is None:
        return ()
    datasets = getattr(result_datasets, "datasets", result_datasets)
    if isinstance(datasets, (str, bytes)):
        return ()
    try:
        return tuple(item for item in datasets if item is not None)
    except TypeError:
        return (datasets,)


def _dataset_id(result_dataset: object) -> str:
    return str(getattr(result_dataset, "dataset_id", "") or "result")


def _dataset_mesh_refs(result_dataset: object) -> tuple[str, ...]:
    metadata = getattr(result_dataset, "metadata", {}) or {}
    if not isinstance(metadata, Mapping):
        return ()
    refs: list[str] = []
    seen: set[str] = set()
    for key in _MESH_REF_METADATA_KEYS:
        value = metadata.get(key)
        values = value if isinstance(value, (list, tuple, set, frozenset)) else (value,)
        for item in values:
            text = str(item or "").strip()
            if text and text not in seen:
                seen.add(text)
                refs.append(text)
    return tuple(refs)


def _first_compatible_result_field(
    mesh: MeshData, result_dataset: object
) -> tuple[str | None, tuple[str, ...]]:
    diagnostics: list[str] = []
    fields = tuple(getattr(result_dataset, "fields", ()) or ())
    if not fields:
        return None, (_no_matching_field_message(result_dataset),)
    for field in fields:
        name = str(getattr(field, "name", "") or "")
        if not name:
            continue
        mapping = map_result_field_to_mesh(mesh, field)
        if mapping.applied:
            return name, ()
        diagnostics.extend(mapping.diagnostics)
    return None, tuple(diagnostics) or (_no_matching_field_message(result_dataset),)


def _no_matching_field_message(result_dataset: object) -> str:
    return (
        f"Result dataset '{_dataset_id(result_dataset)}' has no scalar field "
        "matching the active mesh node/cell count."
    )
