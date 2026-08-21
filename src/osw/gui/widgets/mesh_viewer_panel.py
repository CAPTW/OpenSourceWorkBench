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

from osw.core.workspace_3d import ActiveSceneScreenshotRequest
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.gui.workspace_scene_view_model import (
    DefaultSceneAdapter,
    MeshViewerState,
    SceneAdapterProtocol,
    mesh_input_ref,
    mesh_scalar_field_names,
    mesh_summary_rows,
    mesh_vector_field_names,
    scene_view_state_from_toggles,
    summary_rows_to_text,
)
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData
from osw.post.pyvista_scene import PyVistaUnavailableError
from osw.post.result_field_mapping import (
    map_result_field_to_mesh,
    map_result_vector_field_to_mesh,
    result_field_names,
)
from osw.post.result_probe import ResultProbeRequest
from osw.post.scene_model import SceneScreenshotRecord

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

_NONE_FIELD = "(none)"
_RESULT_PREFIX = "result: "
_RESULT_VECTOR_PREFIX = "result vector: "
_NO_VECTOR_FIELD = "(none)"
_NO_MESH_TEXT = "No mesh loaded."
_MESH_READY_TEXT = "Mesh loaded. Select 'Load mesh preview' to build the scene."
_PREVIEW_LOADED_TEXT = "Mesh preview loaded."
_CAPTURED_TEXT = "Captured scene metadata."
_CAPTURE_SCREENSHOT_STAGED_TEXT = "Captured scene screenshot and staged for report export."
_CAPTURE_SCREENSHOT_HANDLER_MISSING_TEXT = (
    "Scene screenshot capture action is not wired to the main window."
)
_NO_STAGED_SCREENSHOTS_TEXT = "No scene screenshots staged for the next report export."
_STAGED_SCREENSHOTS_COUNT_TEMPLATE = "Report screenshots staged: {count}"
_CLEARED_SCREENSHOTS_TEXT = "Cleared staged scene screenshots."
_CLEAR_SCREENSHOTS_HANDLER_MISSING_TEXT = (
    "Clear staged screenshots is not wired to the main window."
)
_SCREENSHOT_ARTIFACT_CAVEAT_TEXT = (
    "Scene screenshots are local report artifacts only; they are not validation "
    "evidence or release assets."
)
_EDIT_CAPTION_HANDLER_MISSING_TEXT = (
    "Edit scene screenshot caption is not wired to the main window."
)
_REMOVE_SCREENSHOT_HANDLER_MISSING_TEXT = (
    "Remove staged screenshot is not wired to the main window."
)
_NO_SCREENSHOT_SELECTED_TEXT = "Select a staged scene screenshot first."
_UNIDENTIFIED_SCREENSHOT_TEXT = "Could not identify the selected staged screenshot."
_CAPTION_UPDATED_TEXT = "Updated staged scene screenshot caption."
_SCREENSHOT_REMOVED_TEXT = "Removed staged scene screenshot."
_EDIT_CAPTION_PROMPT_TITLE = "Edit scene screenshot caption"
_EDIT_CAPTION_PROMPT_LABEL = "Caption:"
_PERSIST_HANDLER_MISSING_TEXT = "Persist staged screenshots is not wired to the main window."
_NO_SCREENSHOTS_TO_PERSIST_TEXT = "No staged scene screenshots to persist."
_SCREENSHOTS_PERSISTED_TEMPLATE = "Persisted {count} scene screenshot report asset(s)."
_PERSISTED_SCREENSHOTS_COUNT_TEMPLATE = "Persisted report screenshots: {count}"
_MANAGE_PERSISTED_HANDLER_MISSING_TEXT = (
    "Persisted screenshot management is not wired to the main window."
)
_RESTORE_CAPTURE_HANDLER_MISSING_TEXT = (
    "Restore view from scene capture is not wired to the main window."
)
_RESTORE_CAPTURE_NO_SELECTION_TEXT = "Select a staged scene screenshot first."
_RESTORE_CAPTURE_APPLIED_TEXT = "Restored the logical scene from the selected capture."
_RESTORE_CAPTURE_STALE_TEXT = "The selected capture is stale for the active mesh."
_RESTORE_CAPTURE_FAILED_TEXT = "The selected capture could not restore the current scene."
_PYVISTA_MISSING_TEXT = (
    "PyVista unavailable -- install the visualization extra to render 3D scenes."
)
_NO_ACTIVE_MESH_TEXT = "No active mesh is loaded; result fields were not associated."
_NO_RESULT_DATASETS_TEXT = "No result datasets are available for this mesh."
_AMBIGUOUS_RESULT_DATASETS_TEXT = (
    "Multiple result datasets could match this mesh; choose one explicitly."
)
_NO_STAGED_BINDING_TEXT = "No result dataset is staged for persisted binding."
_BINDING_HANDLER_MISSING_TEXT = "Persisted binding requires a MainWindow confirmation handler."
_NO_VECTOR_FIELDS_TEXT = "No compatible vector fields are available for glyph preview."
_NO_VECTOR_FIELD_SELECTED_TEXT = "No compatible vector field is selected for glyph preview."
_PERSISTED_BINDING_TEXT = "Persisted result/mesh binding metadata."
_NO_SAVED_SCENE_TEXT = "No saved workspace state."
_CLEAR_SAVED_SCENE_HANDLER_MISSING_TEXT = (
    "Clear saved workspace state is not wired to the main window."
)
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
        self._result_vector_field_lookup: dict[str, object] = {}
        self._result_binding: object | None = None
        self._result_ref_id = ""
        self._interactive_result_state_changed_callback: Callable[[], object] | None = None
        self._bind_result_callback: Callable[[], object] | None = None
        self._rebind_result_callback: Callable[[], object] | None = None
        self._capture_scene_screenshot_callback: (
            Callable[[], SceneScreenshotRecord | None] | None
        ) = None
        self._scene_screenshot_candidates_provider: (
            Callable[[], Sequence[SceneScreenshotRecord]] | None
        ) = None
        self._clear_scene_screenshots_callback: Callable[[], None] | None = None
        self._edit_scene_screenshot_caption_callback: Callable[[str, str], bool] | None = None
        self._remove_scene_screenshot_callback: Callable[[str], bool] | None = None
        self._persist_scene_screenshots_callback: Callable[[], object] | None = None
        self._persisted_report_screenshots_provider: Callable[[], Sequence[object]] | None = None
        self._open_persisted_report_screenshot_manager_callback: Callable[[], object] | None = None
        self._restore_scene_from_capture_callback: Callable[[object], object] | None = None
        self._clear_saved_active_scene_callback: Callable[[], object] | None = None
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

        self.vector_label = QtWidgets.QLabel("Vector glyphs:", self)
        self.vector_label.setObjectName("oswMeshViewerVectorLabel")
        self.vector_selector = QtWidgets.QComboBox(self)
        self.vector_selector.setObjectName("oswMeshViewerVectorSelector")
        self.vector_selector.addItem(_NO_VECTOR_FIELD)
        self.glyph_toggle = QtWidgets.QCheckBox("Glyphs", self)
        self.glyph_toggle.setObjectName("oswMeshViewerGlyphToggle")
        self.glyph_scale_input = QtWidgets.QDoubleSpinBox(self)
        self.glyph_scale_input.setObjectName("oswMeshViewerGlyphScale")
        self.glyph_scale_input.setRange(0.01, 1000.0)
        self.glyph_scale_input.setDecimals(3)
        self.glyph_scale_input.setSingleStep(0.25)
        self.glyph_scale_input.setValue(1.0)
        self.glyph_max_count_input = QtWidgets.QSpinBox(self)
        self.glyph_max_count_input.setObjectName("oswMeshViewerGlyphMaxCount")
        self.glyph_max_count_input.setRange(0, 100000)
        self.glyph_max_count_input.setSpecialValueText("all")

        self.load_button = QtWidgets.QPushButton("Load mesh preview", self)
        self.load_button.setObjectName("oswMeshViewerLoadButton")
        self.capture_button = QtWidgets.QPushButton("Add scene screenshot to report...", self)
        self.capture_button.setObjectName("oswMeshViewerCaptureButton")
        self.bind_result_button = QtWidgets.QPushButton("Bind result to active mesh...", self)
        self.bind_result_button.setObjectName("oswMeshViewerBindResultButton")
        self.rebind_result_button = QtWidgets.QPushButton(
            "Rebind result to active mesh...",
            self,
        )
        self.rebind_result_button.setObjectName("oswMeshViewerRebindResultButton")

        self.binding_status_label = QtWidgets.QLabel(_NO_STAGED_BINDING_TEXT, self)
        self.binding_status_label.setObjectName("oswMeshViewerBindingStatus")
        self.binding_status_label.setWordWrap(True)

        self.binding_schema_label = QtWidgets.QLabel("", self)
        self.binding_schema_label.setObjectName("oswResultBindingSchema")
        self.binding_state_label = QtWidgets.QLabel("UNRESOLVED", self)
        self.binding_state_label.setObjectName("oswResultBindingState")
        self.result_dataset_selector = QtWidgets.QComboBox(self)
        self.result_dataset_selector.setObjectName("oswResultDatasetSelector")
        self.result_dataset_selector.addItem("(no result dataset)")
        self.result_association_label = QtWidgets.QLabel("Association: —", self)
        self.result_association_label.setObjectName("oswResultAssociation")
        self.scalar_component_selector = QtWidgets.QComboBox(self)
        self.scalar_component_selector.setObjectName("oswResultScalarComponent")
        self.contour_toggle = QtWidgets.QCheckBox("Contour", self)
        self.contour_toggle.setObjectName("oswResultContourToggle")
        self.contour_toggle.setChecked(True)
        self.range_mode_selector = QtWidgets.QComboBox(self)
        self.range_mode_selector.setObjectName("oswResultRangeMode")
        self.range_mode_selector.addItems(("AUTO", "MANUAL"))
        self.manual_min_input = QtWidgets.QDoubleSpinBox(self)
        self.manual_min_input.setObjectName("oswResultManualMinimum")
        self.manual_min_input.setRange(-1e300, 1e300)
        self.manual_min_input.setDecimals(6)
        self.manual_max_input = QtWidgets.QDoubleSpinBox(self)
        self.manual_max_input.setObjectName("oswResultManualMaximum")
        self.manual_max_input.setRange(-1e300, 1e300)
        self.manual_max_input.setDecimals(6)
        self.manual_max_input.setValue(1.0)
        self.colormap_selector = QtWidgets.QComboBox(self)
        self.colormap_selector.setObjectName("oswResultColormap")
        self.colormap_selector.addItems(
            ("viridis", "plasma", "magma", "cividis", "coolwarm", "turbo", "gray")
        )
        self.colorbar_toggle = QtWidgets.QCheckBox("Colorbar", self)
        self.colorbar_toggle.setObjectName("oswResultColorbar")
        self.colorbar_toggle.setChecked(True)
        self.apply_scalar_button = QtWidgets.QPushButton("Apply scalar", self)
        self.apply_scalar_button.setObjectName("oswResultApplyScalar")
        self.apply_vector_button = QtWidgets.QPushButton("Apply vector", self)
        self.apply_vector_button.setObjectName("oswResultApplyVector")
        self.data_range_label = QtWidgets.QLabel("—", self)
        self.data_range_label.setObjectName("oswResultDataRange")
        self.applied_range_label = QtWidgets.QLabel("—", self)
        self.applied_range_label.setObjectName("oswResultAppliedRange")
        self.vector_count_label = QtWidgets.QLabel("0 / 0 / 0 / 0", self)
        self.vector_count_label.setObjectName("oswResultVectorCount")
        self.vector_scale_mode_selector = QtWidgets.QComboBox(self)
        self.vector_scale_mode_selector.setObjectName("oswResultVectorScaleMode")
        self.vector_scale_mode_selector.addItems(("AUTO", "MANUAL"))
        self.scalar_statistics_label = QtWidgets.QLabel("Scalar statistics: —", self)
        self.scalar_statistics_label.setObjectName("oswResultScalarStatistics")
        self.scalar_statistics_label.setWordWrap(True)
        self.deformation_field_selector = QtWidgets.QComboBox(self)
        self.deformation_field_selector.setObjectName("oswResultDeformationField")
        self.deformation_field_selector.addItem("(no eligible displacement)")
        self.deformation_mode_selector = QtWidgets.QComboBox(self)
        self.deformation_mode_selector.setObjectName("oswResultDeformationMode")
        self.deformation_mode_selector.addItems(("ORIGINAL", "DEFORMED", "OVERLAY"))
        self.deformation_scale_mode_selector = QtWidgets.QComboBox(self)
        self.deformation_scale_mode_selector.setObjectName("oswResultDeformationScaleMode")
        self.deformation_scale_mode_selector.addItems(("AUTO", "MANUAL"))
        self.deformation_scale_input = QtWidgets.QDoubleSpinBox(self)
        self.deformation_scale_input.setObjectName("oswResultDeformationScale")
        self.deformation_scale_input.setRange(0.0, 1.0e12)
        self.deformation_scale_input.setDecimals(6)
        self.deformation_scale_input.setValue(1.0)
        self.apply_deformation_button = QtWidgets.QPushButton("Apply deformation", self)
        self.apply_deformation_button.setObjectName("oswResultApplyDeformation")
        self.reset_result_view_button = QtWidgets.QPushButton("Reset Result View", self)
        self.reset_result_view_button.setObjectName("oswResultResetView")
        self.result_status_label = QtWidgets.QLabel(
            "Confirm an exact result/mesh binding to enable interactive results.",
            self,
        )
        self.result_status_label.setObjectName("oswResultStatus")
        self.result_status_label.setWordWrap(True)
        self.result_probe_label = QtWidgets.QLabel("No result probe.", self)
        self.result_probe_label.setObjectName("oswResultProbe")
        self.result_probe_label.setWordWrap(True)
        self.selected_result_table = QtWidgets.QTableWidget(0, 4, self)
        self.selected_result_table.setObjectName("oswSelectedResultTable")
        self.selected_result_table.setHorizontalHeaderLabels(("Entity", "Field", "Value", "Unit"))
        self.selected_result_table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.selected_result_table.setAccessibleName("Selected entity result values")
        self.selected_result_table.setToolTip(
            "Exact stored values for the current canonical point or cell selection."
        )

        for widget, accessible_name, tooltip in (
            (
                self.result_dataset_selector,
                "Result dataset selector",
                "Choose the already-loaded ResultDataset for the active mesh.",
            ),
            (
                self.scalar_selector,
                "Result field selector",
                "Choose an exact point- or cell-associated field from the active result.",
            ),
            (
                self.result_association_label,
                "Result field association",
                "Shows whether the active result field is point- or cell-associated.",
            ),
            (
                self.scalar_component_selector,
                "Result scalar component or magnitude",
                "Choose scalar, X, Y, Z, or derived magnitude where supported.",
            ),
            (
                self.contour_toggle,
                "Show result contour",
                "Show or hide one exact point/cell result contour.",
            ),
            (
                self.range_mode_selector,
                "Result range mode",
                "Choose finite-data automatic range or an explicit manual range.",
            ),
            (
                self.manual_min_input,
                "Result manual range minimum",
                "Set the lower scalar display bound; it must be below the maximum.",
            ),
            (
                self.manual_max_input,
                "Result manual range maximum",
                "Set the upper scalar display bound; it must be above the minimum.",
            ),
            (
                self.colormap_selector,
                "Result colormap selector",
                "Choose one bounded, validated result colormap.",
            ),
            (
                self.colorbar_toggle,
                "Show result colorbar",
                "Show or hide the scalar colorbar without changing field values.",
            ),
            (
                self.vector_selector,
                "Result vector field selector",
                "Choose an exact point- or cell-associated vector field for glyphs.",
            ),
            (
                self.glyph_toggle,
                "Show result vector glyphs",
                "Show or hide deterministic result vector glyphs.",
            ),
            (
                self.glyph_max_count_input,
                "Maximum result glyph count",
                "Bound deterministic glyph sampling; zero displays every valid vector.",
            ),
            (
                self.vector_scale_mode_selector,
                "Vector glyph scale mode",
                "Choose deterministic automatic or positive manual visual scale.",
            ),
            (
                self.glyph_scale_input,
                "Manual vector glyph scale",
                "Set a positive visual-only vector glyph scale.",
            ),
            (
                self.result_probe_label,
                "Current result probe",
                "Shows exact stored point or cell values; nonfinite values are N/A.",
            ),
            (
                self.deformation_field_selector,
                "Displacement field selector",
                "Only typed, exact-unit displacement fields are eligible.",
            ),
            (
                self.deformation_mode_selector,
                "Deformation display mode",
                "Choose original, deformed-only, or original/deformed overlay.",
            ),
            (
                self.deformation_scale_mode_selector,
                "Deformation scale mode",
                "Choose deterministic automatic or nonnegative manual deformation scale.",
            ),
            (
                self.deformation_scale_input,
                "Manual deformation scale",
                "Set a nonnegative visual-only displacement scale.",
            ),
            (
                self.apply_deformation_button,
                "Apply result deformation",
                "Apply the selected typed displacement field without mutating the source mesh.",
            ),
            (
                self.reset_result_view_button,
                "Reset result view",
                "Remove transient result actors without changing stored result data.",
            ),
        ):
            widget.setAccessibleName(accessible_name)
            widget.setToolTip(tooltip)

        self.status_label = QtWidgets.QLabel(_NO_MESH_TEXT, self)
        self.status_label.setObjectName("oswMeshViewerStatus")
        self.status_label.setWordWrap(True)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswMeshViewerDiagnostics")

        self.saved_scene_status_label = QtWidgets.QLabel(_NO_SAVED_SCENE_TEXT, self)
        self.saved_scene_status_label.setObjectName("oswSavedActiveSceneStatus")
        self.saved_scene_status_label.setWordWrap(True)
        self.clear_saved_scene_button = QtWidgets.QPushButton("Clear saved workspace state", self)
        self.clear_saved_scene_button.setObjectName("oswClearSavedActiveSceneButton")

        self.screenshot_status_label = QtWidgets.QLabel(_NO_STAGED_SCREENSHOTS_TEXT, self)
        self.screenshot_status_label.setObjectName("oswMeshViewerScreenshotStatus")
        self.screenshot_status_label.setWordWrap(True)
        self.staged_screenshots_list = QtWidgets.QListWidget(self)
        self.staged_screenshots_list.setObjectName("oswMeshViewerStagedScreenshots")
        self.clear_screenshots_button = QtWidgets.QPushButton("Clear staged screenshots", self)
        self.clear_screenshots_button.setObjectName("oswMeshViewerClearScreenshotsButton")
        self.clear_screenshots_button.setEnabled(False)
        self.screenshot_caveat_label = QtWidgets.QLabel(_SCREENSHOT_ARTIFACT_CAVEAT_TEXT, self)
        self.screenshot_caveat_label.setObjectName("oswMeshViewerScreenshotCaveat")
        self.screenshot_caveat_label.setWordWrap(True)
        self.edit_caption_button = QtWidgets.QPushButton("Edit caption...", self)
        self.edit_caption_button.setObjectName("oswMeshViewerEditCaptionButton")
        self.edit_caption_button.setEnabled(False)
        self.remove_screenshot_button = QtWidgets.QPushButton("Remove selected screenshot", self)
        self.remove_screenshot_button.setObjectName("oswMeshViewerRemoveScreenshotButton")
        self.remove_screenshot_button.setEnabled(False)
        self.persist_screenshots_button = QtWidgets.QPushButton(
            "Persist staged screenshots with project...", self
        )
        self.persist_screenshots_button.setObjectName("oswMeshViewerPersistScreenshotsButton")
        self.persist_screenshots_button.setEnabled(False)
        self.restore_capture_button = QtWidgets.QPushButton(
            "Restore view from selected capture",
            self,
        )
        self.restore_capture_button.setObjectName("oswMeshViewerRestoreCaptureButton")
        self.restore_capture_button.setEnabled(False)
        self.persisted_screenshots_status_label = QtWidgets.QLabel(
            _PERSISTED_SCREENSHOTS_COUNT_TEMPLATE.format(count=0), self
        )
        self.persisted_screenshots_status_label.setObjectName(
            "oswMeshViewerPersistedScreenshotsStatus"
        )
        self.manage_persisted_screenshots_button = QtWidgets.QPushButton(
            "Manage persisted report screenshots...", self
        )
        self.manage_persisted_screenshots_button.setObjectName(
            "oswMeshViewerManagePersistedScreenshotsButton"
        )
        self.manage_persisted_screenshots_button.setEnabled(False)

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

        vector_fields = QtWidgets.QHBoxLayout()
        vector_fields.addWidget(self.vector_label)
        vector_fields.addWidget(self.vector_selector)
        vector_fields.addWidget(self.glyph_toggle)
        vector_fields.addWidget(QtWidgets.QLabel("Scale:", self))
        vector_fields.addWidget(self.glyph_scale_input)
        vector_fields.addWidget(QtWidgets.QLabel("Max:", self))
        vector_fields.addWidget(self.glyph_max_count_input)
        vector_fields.addStretch(1)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addWidget(self.load_button)
        buttons.addWidget(self.capture_button)
        buttons.addWidget(self.bind_result_button)
        buttons.addWidget(self.rebind_result_button)
        buttons.addStretch(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.addWidget(self.title_label)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.empty_state)
        layout.addLayout(toggles)
        layout.addLayout(fields)
        layout.addLayout(vector_fields)
        layout.addLayout(buttons)
        layout.addWidget(self.binding_status_label)
        result_binding_row = QtWidgets.QHBoxLayout()
        result_binding_row.addWidget(QtWidgets.QLabel("Result:", self))
        result_binding_row.addWidget(self.result_dataset_selector)
        result_binding_row.addWidget(QtWidgets.QLabel("Binding:", self))
        result_binding_row.addWidget(self.binding_schema_label)
        result_binding_row.addWidget(self.binding_state_label)
        result_binding_row.addWidget(self.result_association_label)
        result_binding_row.addStretch(1)
        layout.addLayout(result_binding_row)
        scalar_result_row = QtWidgets.QHBoxLayout()
        scalar_result_row.addWidget(QtWidgets.QLabel("Component:", self))
        scalar_result_row.addWidget(self.scalar_component_selector)
        scalar_result_row.addWidget(self.contour_toggle)
        scalar_result_row.addWidget(self.range_mode_selector)
        scalar_result_row.addWidget(self.manual_min_input)
        scalar_result_row.addWidget(self.manual_max_input)
        scalar_result_row.addWidget(self.colormap_selector)
        scalar_result_row.addWidget(self.colorbar_toggle)
        scalar_result_row.addWidget(self.apply_scalar_button)
        layout.addLayout(scalar_result_row)
        vector_result_row = QtWidgets.QHBoxLayout()
        vector_result_row.addWidget(self.apply_vector_button)
        vector_result_row.addWidget(QtWidgets.QLabel("Vector scale:", self))
        vector_result_row.addWidget(self.vector_scale_mode_selector)
        vector_result_row.addWidget(QtWidgets.QLabel("Data range:", self))
        vector_result_row.addWidget(self.data_range_label)
        vector_result_row.addWidget(QtWidgets.QLabel("Applied range:", self))
        vector_result_row.addWidget(self.applied_range_label)
        vector_result_row.addWidget(QtWidgets.QLabel("Vectors:", self))
        vector_result_row.addWidget(self.vector_count_label)
        vector_result_row.addStretch(1)
        layout.addLayout(vector_result_row)
        deformation_row = QtWidgets.QHBoxLayout()
        deformation_row.addWidget(QtWidgets.QLabel("Displacement:", self))
        deformation_row.addWidget(self.deformation_field_selector)
        deformation_row.addWidget(self.deformation_mode_selector)
        deformation_row.addWidget(self.deformation_scale_mode_selector)
        deformation_row.addWidget(self.deformation_scale_input)
        deformation_row.addWidget(self.apply_deformation_button)
        deformation_row.addWidget(self.reset_result_view_button)
        deformation_row.addStretch(1)
        layout.addLayout(deformation_row)
        layout.addWidget(self.scalar_statistics_label)
        layout.addWidget(self.result_status_label)
        layout.addWidget(self.result_probe_label)
        layout.addWidget(self.selected_result_table)
        layout.addWidget(self.status_label)
        saved_scene_row = QtWidgets.QHBoxLayout()
        saved_scene_row.addWidget(self.saved_scene_status_label)
        saved_scene_row.addStretch(1)
        saved_scene_row.addWidget(self.clear_saved_scene_button)
        layout.addLayout(saved_scene_row)

        screenshots_row = QtWidgets.QHBoxLayout()
        screenshots_row.addWidget(self.screenshot_status_label)
        screenshots_row.addStretch(1)
        screenshots_row.addWidget(self.clear_screenshots_button)
        layout.addLayout(screenshots_row)
        layout.addWidget(self.staged_screenshots_list)

        screenshot_actions_row = QtWidgets.QHBoxLayout()
        screenshot_actions_row.addWidget(self.edit_caption_button)
        screenshot_actions_row.addWidget(self.remove_screenshot_button)
        screenshot_actions_row.addWidget(self.persist_screenshots_button)
        screenshot_actions_row.addWidget(self.restore_capture_button)
        screenshot_actions_row.addStretch(1)
        layout.addLayout(screenshot_actions_row)

        persisted_screenshots_row = QtWidgets.QHBoxLayout()
        persisted_screenshots_row.addWidget(self.persisted_screenshots_status_label)
        persisted_screenshots_row.addStretch(1)
        persisted_screenshots_row.addWidget(self.manage_persisted_screenshots_button)
        layout.addLayout(persisted_screenshots_row)
        layout.addWidget(self.screenshot_caveat_label)

        layout.addWidget(self.diagnostics_list)

        self.load_button.clicked.connect(lambda _checked=False: self.load_mesh_preview())
        self.capture_button.clicked.connect(lambda _checked=False: self._on_capture_requested())
        self.clear_screenshots_button.clicked.connect(
            lambda _checked=False: self._on_clear_screenshots_requested()
        )
        self.edit_caption_button.clicked.connect(
            lambda _checked=False: self._on_edit_caption_requested()
        )
        self.remove_screenshot_button.clicked.connect(
            lambda _checked=False: self._on_remove_screenshot_requested()
        )
        self.persist_screenshots_button.clicked.connect(
            lambda _checked=False: self._on_persist_screenshots_requested()
        )
        self.restore_capture_button.clicked.connect(
            lambda _checked=False: self._on_restore_capture_requested()
        )
        self.manage_persisted_screenshots_button.clicked.connect(
            lambda _checked=False: self._on_manage_persisted_screenshots_requested()
        )
        self.clear_saved_scene_button.clicked.connect(
            lambda _checked=False: self._on_clear_saved_scene_requested()
        )
        self.staged_screenshots_list.currentRowChanged.connect(
            lambda _row=-1: self._update_screenshot_action_buttons()
        )
        self.bind_result_button.clicked.connect(
            lambda _checked=False: self._on_bind_result_requested()
        )
        self.rebind_result_button.clicked.connect(
            lambda _checked=False: self._on_rebind_result_requested()
        )
        self.apply_scalar_button.clicked.connect(
            lambda _checked=False: self._apply_interactive_scalar_result()
        )
        self.apply_vector_button.clicked.connect(
            lambda _checked=False: self._apply_interactive_vector_result()
        )
        self.apply_deformation_button.clicked.connect(
            lambda _checked=False: self._apply_interactive_deformation()
        )
        self.reset_result_view_button.clicked.connect(
            lambda _checked=False: self._reset_interactive_result_view()
        )
        self.contour_toggle.toggled.connect(
            lambda checked=False: self._on_contour_toggled(bool(checked))
        )
        self.range_mode_selector.currentTextChanged.connect(
            lambda _text: self._refresh_interactive_result_controls()
        )
        self.manual_min_input.valueChanged.connect(
            lambda _value=0.0: self._refresh_interactive_result_controls()
        )
        self.manual_max_input.valueChanged.connect(
            lambda _value=0.0: self._refresh_interactive_result_controls()
        )
        self.scalar_selector.currentTextChanged.connect(
            lambda _text: self._on_scalar_selection_changed()
        )
        self.vector_selector.currentTextChanged.connect(
            lambda _text: self._on_vector_glyph_controls_changed()
        )
        self.glyph_toggle.toggled.connect(
            lambda _checked=False: self._on_vector_glyph_controls_changed()
        )
        self.glyph_scale_input.valueChanged.connect(
            lambda _value=0.0: self._on_vector_glyph_controls_changed()
        )
        self.glyph_max_count_input.valueChanged.connect(
            lambda _value=0: self._on_vector_glyph_controls_changed()
        )
        self.vector_scale_mode_selector.currentTextChanged.connect(
            lambda _text: self._refresh_interactive_result_controls()
        )
        self.deformation_scale_mode_selector.currentTextChanged.connect(
            lambda _text: self._refresh_interactive_result_controls()
        )
        self.deformation_mode_selector.currentTextChanged.connect(
            lambda _text: self._refresh_interactive_result_controls()
        )
        self._set_controls_enabled(False)
        self._refresh_interactive_result_controls()
        self._render_state()

    # -- public API ---------------------------------------------------------

    def set_mesh(self, mesh: MeshData, *, mesh_ref: str = "") -> None:
        """Attach an in-memory mesh and show its summary (no rendering)."""
        if self._state.mesh is not None and not isinstance(self._adapter, ActiveSceneController):
            clear = getattr(self._adapter, "clear", None)
            if callable(clear):
                clear()
        self._state = MeshViewerState(
            mesh=mesh,
            mesh_ref=mesh_ref,
            selected_selection_ids=self._state.selected_selection_ids,
            summary_rows=mesh_summary_rows(mesh),
            status_message=_MESH_READY_TEXT,
        )
        if (
            isinstance(self._adapter, ActiveSceneController)
            and self._adapter.backend_kind != "scene-adapter"
        ):
            fingerprint = compute_mesh_fingerprint(mesh)
            current = self._adapter.current_mesh_fingerprint
            if (
                current is None
                or current.digest != fingerprint.digest
                or self._adapter.current_mesh_ref != mesh_ref
            ):
                scene_input = mesh_input_ref(mesh_ref)
                scene_state = scene_view_state_from_toggles(
                    show_surface=self.surface_toggle.isChecked(),
                    show_edges=self.edge_toggle.isChecked(),
                    show_axes=self.axis_toggle.isChecked(),
                    show_grid=self.grid_toggle.isChecked(),
                )
                self._state.scene_input = scene_input
                self._state.scene_state = scene_state
                self._adapter.load_mesh(mesh, scene_input, scene_state)
        self._populate_scalar_selector(mesh)
        self._populate_vector_selector(mesh)
        self._set_controls_enabled(True)
        self._sync_interactive_result_binding()
        self._refresh_binding_status()
        self._render_state()

    def set_selected_selection_ids(self, selection_ids: object) -> None:
        """Record selected NamedSelection ids for the next preview build."""
        self._state.selected_selection_ids = tuple(str(item) for item in selection_ids)
        if isinstance(self._adapter, ActiveSceneController):
            self._adapter.set_active_named_selection_ids(self._state.selected_selection_ids)

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
        self._result_vector_field_lookup = dict(self._result_field_lookup)
        self.result_dataset_selector.blockSignals(True)
        self.result_dataset_selector.clear()
        if result_dataset is None:
            self.result_dataset_selector.addItem("(no result dataset)")
        else:
            metadata = getattr(result_dataset, "metadata", {}) or {}
            title = str(metadata.get("title", "") or "") if isinstance(metadata, Mapping) else ""
            self.result_dataset_selector.addItem(
                title or self._result_dataset_ref or "Result dataset",
                self._result_dataset_ref,
            )
        self.result_dataset_selector.blockSignals(False)
        self._populate_scalar_selector(self._state.mesh)
        self._populate_vector_selector(self._state.mesh)
        self._populate_deformation_fields()
        self._sync_interactive_result_binding()
        self._refresh_binding_status()
        self._render_state()

    def set_result_binding(
        self,
        binding: object | None,
        *,
        result_ref_id: str = "",
    ) -> None:
        """Attach one persisted binding to the transient controller projection."""

        self._result_binding = binding
        self._result_ref_id = str(result_ref_id or "")
        self._sync_interactive_result_binding()
        if self.selected_result_field_id() is not None:
            self._apply_interactive_scalar_result(allow_render=False)
        self._render_interactive_result_state()

    def probe_result_entity(
        self,
        association: str,
        stable_entity_key: int | str,
    ) -> object | None:
        """Display one exact stored value for a stable selected entity."""

        if not isinstance(self._adapter, ActiveSceneController):
            return None
        field_name = self.selected_result_field_id()
        component = self.scalar_component_selector.currentText()
        fingerprint = self._adapter.current_mesh_fingerprint
        if field_name is None or not component or fingerprint is None:
            return None
        result = self._adapter.probe_result(
            ResultProbeRequest(
                dataset_id=self._result_dataset_ref,
                field_name=field_name,
                component=component,
                association=association,
                stable_entity_key=stable_entity_key,
                mesh_fingerprint=fingerprint.digest,
            )
        )
        self._render_interactive_result_state()
        return result

    def set_selected_result_entities(
        self,
        association: str,
        stable_entity_keys: Sequence[int | str],
    ) -> object | None:
        """Display a bounded exact-value table for stable selected entities."""

        if not isinstance(self._adapter, ActiveSceneController):
            return None
        field_name = self.selected_result_field_id()
        component = self.scalar_component_selector.currentText()
        if field_name is None or not component:
            return None
        table = self._adapter.set_selected_result_table(
            field_name=field_name,
            component=component,
            association=association,
            stable_entity_keys=stable_entity_keys,
            limit=500,
        )
        self._render_interactive_result_state()
        return table

    def sync_result_selection(
        self,
        entity_kind: str,
        stable_entity_keys: Sequence[int | str],
    ) -> None:
        """Project the canonical scene selection into probe and table state."""

        if not isinstance(self._adapter, ActiveSceneController):
            return
        association = "point" if str(entity_kind) in {"node", "point"} else "cell"
        keys = tuple(stable_entity_keys)
        if not keys:
            self._render_interactive_result_state()
            return
        self.set_selected_result_entities(association, keys)
        self.probe_result_entity(association, keys[0])

    def set_bind_result_callback(self, callback: Callable[[], object] | None) -> None:
        """Connect the panel action to a MainWindow-owned confirmation flow."""
        self._bind_result_callback = callback

    def set_rebind_result_callback(
        self,
        callback: Callable[[], object] | None,
    ) -> None:
        """Connect the explicit stale/legacy replacement action."""

        self._rebind_result_callback = callback

    def set_capture_scene_screenshot_callback(
        self, callback: Callable[[], SceneScreenshotRecord | None] | None
    ) -> None:
        """Connect the capture button to a MainWindow-owned flow."""
        self._capture_scene_screenshot_callback = callback

    def set_scene_screenshot_candidates_provider(
        self, provider: Callable[[], Sequence[SceneScreenshotRecord]] | None
    ) -> None:
        """Connect a MainWindow-owned provider of staged screenshot candidates.

        The panel reads the current staged records through this provider; it does
        not own or store candidate state.
        """
        self._scene_screenshot_candidates_provider = provider
        self._render_screenshot_status()

    def set_clear_scene_screenshots_callback(self, callback: Callable[[], None] | None) -> None:
        """Connect the clear action to a MainWindow-owned clear flow."""
        self._clear_scene_screenshots_callback = callback
        self._render_screenshot_status()

    def set_edit_scene_screenshot_caption_callback(
        self, callback: Callable[[str, str], bool] | None
    ) -> None:
        """Connect the caption-edit action to a MainWindow-owned flow."""
        self._edit_scene_screenshot_caption_callback = callback
        self._render_screenshot_status()

    def set_remove_scene_screenshot_callback(self, callback: Callable[[str], bool] | None) -> None:
        """Connect the per-record remove action to a MainWindow-owned flow."""
        self._remove_scene_screenshot_callback = callback
        self._render_screenshot_status()

    def set_persist_scene_screenshots_callback(self, callback: Callable[[], object] | None) -> None:
        """Connect the persist action to a MainWindow-owned opt-in flow."""
        self._persist_scene_screenshots_callback = callback
        self._render_screenshot_status()

    def set_persisted_report_screenshots_provider(
        self, provider: Callable[[], Sequence[object]] | None
    ) -> None:
        """Connect the persisted count to the MainWindow-owned Project list."""
        self._persisted_report_screenshots_provider = provider
        self._render_screenshot_status()

    def set_open_persisted_report_screenshot_manager_callback(
        self, callback: Callable[[], object] | None
    ) -> None:
        """Connect the manager launcher to the MainWindow-owned dialog flow."""
        self._open_persisted_report_screenshot_manager_callback = callback
        self._render_screenshot_status()

    def set_restore_scene_from_capture_callback(
        self, callback: Callable[[object], object] | None
    ) -> None:
        self._restore_scene_from_capture_callback = callback
        self._render_screenshot_status()

    def set_clear_saved_active_scene_callback(
        self,
        callback: Callable[[], object] | None,
    ) -> None:
        self._clear_saved_active_scene_callback = callback

    def show_saved_active_scene_status(self, message: str) -> None:
        self.saved_scene_status_label.setText(str(message))

    def show_persisted_report_screenshot_status(self, message: str) -> None:
        """Display MainWindow-owned persisted-record action diagnostics."""
        self._state.status_message = str(message)
        self._render_state()

    def refresh_scene_screenshot_status(self) -> None:
        """Refresh the staged screenshot count/list from the injected provider."""
        self._render_screenshot_status()

    def current_result_dataset(self) -> object | None:
        return self._result_dataset

    def current_result_dataset_id(self) -> str:
        return self._result_dataset_ref

    def current_result_ref_id(self) -> str:
        return self._result_ref_id

    def selected_result_field_id(self) -> str | None:
        selected = self.scalar_selector.currentText()
        if selected.startswith(_RESULT_PREFIX):
            return selected[len(_RESULT_PREFIX) :] or None
        return None

    def select_result_field(self, field_id: str) -> bool:
        """Select one catalog field without implicitly creating a contour actor."""

        label = f"{_RESULT_PREFIX}{field_id}"
        index = self.scalar_selector.findText(label)
        if index < 0:
            return False
        self.scalar_selector.setCurrentIndex(index)
        return True

    def apply_selected_result_field(self) -> None:
        """Apply the already-selected field under the explicit contour policy."""

        self._apply_interactive_scalar_result()

    def set_interactive_result_state_changed_callback(
        self,
        callback: Callable[[], object] | None,
    ) -> None:
        self._interactive_result_state_changed_callback = callback

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
        clear = getattr(self._adapter, "clear", None)
        if callable(clear):
            clear()
        self._state = MeshViewerState(status_message=_NO_MESH_TEXT)
        self._populate_scalar_selector(None)
        self._populate_vector_selector(None)
        self._set_controls_enabled(False)
        self._result_binding = None
        self._refresh_interactive_result_controls()
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
        render_mesh, glyph_field, glyph_warnings = self._resolve_glyph_source(render_mesh)
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
            glyph_enabled=self.glyph_toggle.isChecked(),
            glyph_vector_field=glyph_field,
            glyph_scale=float(self.glyph_scale_input.value()),
            glyph_max_count=self._selected_glyph_max_count(),
            selected_selection_ids=self._state.selected_selection_ids,
        )
        self._state.scene_input = scene_input
        self._state.scene_state = scene_state

        try:
            result = self._adapter.load_mesh(render_mesh, scene_input, scene_state)
        except PyVistaUnavailableError as exc:
            self._state.pyvista_available = False
            self._state.status_message = _PYVISTA_MISSING_TEXT
            self._state.warning_messages = (str(exc), *field_warnings, *glyph_warnings)
            self._render_state()
            return None

        self._state.pyvista_available = True
        self._state.status_message = _PREVIEW_LOADED_TEXT
        self._state.warning_messages = (
            *tuple(getattr(result, "warnings", ()) or ()),
            *field_warnings,
            *glyph_warnings,
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
        if isinstance(self._adapter, ActiveSceneController):
            result = self._adapter.capture_active_scene_screenshot(
                ActiveSceneScreenshotRequest(
                    record_id=record_id,
                    output_path=str(target_path),
                    caption=caption or "",
                )
            )
            if result.record is None:
                if result.status == "BLOCKED":
                    self._state.pyvista_available = False
                self._state.status_message = (
                    result.diagnostics[0] if result.diagnostics else _PYVISTA_MISSING_TEXT
                )
                self._render_state()
                return None
            self._state.screenshot_record = result.record
            self._state.status_message = _CAPTURED_TEXT
            self._render_state()
            return result.record
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
        if self._capture_scene_screenshot_callback is None:
            self._state.status_message = _CAPTURE_SCREENSHOT_HANDLER_MISSING_TEXT
            self._render_state()
            return

        record = self._capture_scene_screenshot_callback()
        if record is None:
            if not self._state.status_message:
                self._state.status_message = _CAPTURED_TEXT
            self._render_state()
            return

        self._state.screenshot_record = record
        self._state.status_message = _CAPTURE_SCREENSHOT_STAGED_TEXT
        self._render_state()

    def _on_clear_screenshots_requested(self) -> None:
        if self._clear_scene_screenshots_callback is None:
            self._state.status_message = _CLEAR_SCREENSHOTS_HANDLER_MISSING_TEXT
            self._render_state()
            return
        if not self._staged_scene_screenshots():
            # Nothing staged to clear; keep the empty state friendly.
            self._render_screenshot_status()
            return
        self._clear_scene_screenshots_callback()
        self._state.status_message = _CLEARED_SCREENSHOTS_TEXT
        self._render_state()

    def _on_clear_saved_scene_requested(self) -> None:
        callback = self._clear_saved_active_scene_callback
        if callback is None:
            self.saved_scene_status_label.setText(_CLEAR_SAVED_SCENE_HANDLER_MISSING_TEXT)
            return
        callback()

    def _staged_scene_screenshots(self) -> tuple[SceneScreenshotRecord, ...]:
        provider = self._scene_screenshot_candidates_provider
        if provider is None:
            return ()
        return tuple(provider() or ())

    def _render_screenshot_status(self) -> None:
        records = self._staged_scene_screenshots()
        count = len(records)
        if count == 0:
            self.screenshot_status_label.setText(_NO_STAGED_SCREENSHOTS_TEXT)
        else:
            self.screenshot_status_label.setText(
                _STAGED_SCREENSHOTS_COUNT_TEMPLATE.format(count=count)
            )
        # Preserve the current selection across the list rebuild so the
        # edit/remove controls stay usable; block signals so the rebuild does
        # not recurse through currentRowChanged.
        previous_row = self.staged_screenshots_list.currentRow()
        self.staged_screenshots_list.blockSignals(True)
        self.staged_screenshots_list.clear()
        for row in _staged_screenshot_rows(records):
            self.staged_screenshots_list.addItem(row)
        if 0 <= previous_row < count:
            self.staged_screenshots_list.setCurrentRow(previous_row)
        self.staged_screenshots_list.blockSignals(False)
        persisted_count = len(self._persisted_report_screenshots())
        self.persisted_screenshots_status_label.setText(
            _PERSISTED_SCREENSHOTS_COUNT_TEMPLATE.format(count=persisted_count)
        )
        self._update_screenshot_action_buttons()

    def _update_screenshot_action_buttons(self) -> None:
        count = len(self._staged_scene_screenshots())
        has_selection = self._selected_staged_record() is not None
        self.clear_screenshots_button.setEnabled(
            count > 0 and self._clear_scene_screenshots_callback is not None
        )
        self.edit_caption_button.setEnabled(
            has_selection and self._edit_scene_screenshot_caption_callback is not None
        )
        self.remove_screenshot_button.setEnabled(
            has_selection and self._remove_scene_screenshot_callback is not None
        )
        self.persist_screenshots_button.setEnabled(
            count > 0 and self._persist_scene_screenshots_callback is not None
        )
        self.restore_capture_button.setEnabled(
            has_selection and self._restore_scene_from_capture_callback is not None
        )
        self.manage_persisted_screenshots_button.setEnabled(
            bool(self._persisted_report_screenshots())
            and self._open_persisted_report_screenshot_manager_callback is not None
        )

    def _persisted_report_screenshots(self) -> tuple[object, ...]:
        provider = self._persisted_report_screenshots_provider
        if provider is None:
            return ()
        return tuple(provider() or ())

    def _selected_staged_record(self) -> SceneScreenshotRecord | None:
        records = self._staged_scene_screenshots()
        row = self.staged_screenshots_list.currentRow()
        if 0 <= row < len(records):
            return records[row]
        return None

    def _prompt_scene_screenshot_caption(self, current: str) -> str | None:
        """Prompt for a caption; return the new text or None if cancelled.

        Overridable seam so tests drive caption editing without a live modal.
        """
        text, accepted = QtWidgets.QInputDialog.getText(
            self,
            _EDIT_CAPTION_PROMPT_TITLE,
            _EDIT_CAPTION_PROMPT_LABEL,
            text=current,
        )
        return text if accepted else None

    def _on_edit_caption_requested(self) -> None:
        if self._edit_scene_screenshot_caption_callback is None:
            self._state.status_message = _EDIT_CAPTION_HANDLER_MISSING_TEXT
            self._render_state()
            return
        record = self._selected_staged_record()
        if record is None:
            self._state.status_message = _NO_SCREENSHOT_SELECTED_TEXT
            self._render_state()
            return
        record_id = str(getattr(record, "id", "") or "")
        if not record_id:
            self._state.status_message = _UNIDENTIFIED_SCREENSHOT_TEXT
            self._render_state()
            return
        current = str(getattr(record, "caption", "") or "")
        new_caption = self._prompt_scene_screenshot_caption(current)
        if new_caption is None:
            return
        updated = bool(self._edit_scene_screenshot_caption_callback(record_id, new_caption))
        self._state.status_message = (
            _CAPTION_UPDATED_TEXT if updated else _UNIDENTIFIED_SCREENSHOT_TEXT
        )
        self._render_state()

    def _on_remove_screenshot_requested(self) -> None:
        if self._remove_scene_screenshot_callback is None:
            self._state.status_message = _REMOVE_SCREENSHOT_HANDLER_MISSING_TEXT
            self._render_state()
            return
        record = self._selected_staged_record()
        if record is None:
            self._state.status_message = _NO_SCREENSHOT_SELECTED_TEXT
            self._render_state()
            return
        record_id = str(getattr(record, "id", "") or "")
        if not record_id:
            self._state.status_message = _UNIDENTIFIED_SCREENSHOT_TEXT
            self._render_state()
            return
        removed = bool(self._remove_scene_screenshot_callback(record_id))
        self._state.status_message = (
            _SCREENSHOT_REMOVED_TEXT if removed else _UNIDENTIFIED_SCREENSHOT_TEXT
        )
        self._render_state()

    def _on_restore_capture_requested(self) -> None:
        if self._restore_scene_from_capture_callback is None:
            self._state.status_message = _RESTORE_CAPTURE_HANDLER_MISSING_TEXT
            self._render_state()
            return
        record = self._selected_staged_record()
        if record is None:
            self._state.status_message = _RESTORE_CAPTURE_NO_SELECTION_TEXT
            self._render_state()
            return
        result = self._restore_scene_from_capture_callback(record)
        status = str(getattr(result, "status", "") or "")
        if status in {"RESTORED", "PARTIAL"}:
            self._state.status_message = _RESTORE_CAPTURE_APPLIED_TEXT
        elif status == "STALE":
            self._state.status_message = _RESTORE_CAPTURE_STALE_TEXT
        else:
            self._state.status_message = _RESTORE_CAPTURE_FAILED_TEXT
        self._render_state()

    def _on_persist_screenshots_requested(self) -> None:
        if self._persist_scene_screenshots_callback is None:
            self._state.status_message = _PERSIST_HANDLER_MISSING_TEXT
            self._render_state()
            return
        result = self._persist_scene_screenshots_callback()
        count = int(result) if result is not None else 0
        if count > 0:
            self._state.status_message = _SCREENSHOTS_PERSISTED_TEMPLATE.format(count=count)
        elif count == 0:
            self._state.status_message = _NO_SCREENSHOTS_TO_PERSIST_TEXT
        # A negative count means the confirmation was declined; keep the status.
        self._render_state()

    def _on_manage_persisted_screenshots_requested(self) -> None:
        callback = self._open_persisted_report_screenshot_manager_callback
        if callback is None:
            self._state.status_message = _MANAGE_PERSISTED_HANDLER_MISSING_TEXT
            self._render_state()
            return
        callback()

    def _on_bind_result_requested(self) -> None:
        if self._bind_result_callback is None:
            self.show_result_mesh_binding_status(_BINDING_HANDLER_MISSING_TEXT)
            return
        self._bind_result_callback()

    def _on_rebind_result_requested(self) -> None:
        if self._rebind_result_callback is None:
            self.show_result_mesh_binding_status(_BINDING_HANDLER_MISSING_TEXT)
            return
        self._rebind_result_callback()

    def _on_scalar_selection_changed(self) -> None:
        self._populate_scalar_components()
        if self._result_dataset is None:
            return
        self._refresh_binding_status()
        self._refresh_interactive_result_controls()
        self._render_state()

    def _on_vector_glyph_controls_changed(self) -> None:
        if isinstance(self._adapter, ActiveSceneController) and not self.glyph_toggle.isChecked():
            self._adapter.clear_vector_result()
        self._set_vector_controls_enabled(self._state.mesh is not None)
        self._refresh_interactive_result_controls()
        self._render_state()

    def _sync_interactive_result_binding(self) -> None:
        if not isinstance(self._adapter, ActiveSceneController):
            self._refresh_interactive_result_controls()
            return
        self._adapter.set_interactive_result_dataset(
            self._result_dataset,
            self._result_binding,
            result_ref_id=self._result_ref_id,
        )
        self._populate_scalar_selector(self._state.mesh)
        self._populate_vector_selector(self._state.mesh)
        self._populate_deformation_fields()
        self._render_interactive_result_state()

    def _populate_scalar_components(self) -> None:
        current = self.scalar_component_selector.currentText()
        field_name = self.selected_result_field_id()
        field = self._result_field_lookup.get(field_name or "")
        components = tuple(str(item) for item in getattr(field, "components", ()) or ())
        if len(components) == 1:
            options = ("scalar", *components)
        elif len(components) == 3:
            options = ("x", "y", "z", "magnitude", *components)
        else:
            options = components
        self.scalar_component_selector.blockSignals(True)
        self.scalar_component_selector.clear()
        self.scalar_component_selector.addItems(tuple(dict.fromkeys(options)))
        if current in options:
            self.scalar_component_selector.setCurrentText(current)
        self.scalar_component_selector.blockSignals(False)
        association = str(getattr(field, "location", "") or "")
        self.result_association_label.setText(f"Association: {association or '—'}")

    def _populate_deformation_fields(self) -> None:
        current = self.deformation_field_selector.currentText()
        eligible: list[str] = []
        if isinstance(self._adapter, ActiveSceneController):
            catalog = self._adapter.interactive_result_field_catalog
            if catalog is not None:
                eligible = [
                    descriptor.field_id
                    for descriptor in catalog.fields
                    if descriptor.deformation_eligible
                ]
        self.deformation_field_selector.blockSignals(True)
        self.deformation_field_selector.clear()
        if eligible:
            self.deformation_field_selector.addItems(eligible)
            if current in eligible:
                self.deformation_field_selector.setCurrentText(current)
        else:
            self.deformation_field_selector.addItem("(no eligible displacement)")
        self.deformation_field_selector.blockSignals(False)

    def _apply_interactive_scalar_result(
        self,
        *,
        allow_render: bool = True,
    ) -> None:
        if not isinstance(self._adapter, ActiveSceneController):
            return
        field_name = self.selected_result_field_id()
        if field_name is None:
            self.result_status_label.setText("Select a result scalar field.")
            return
        if not self.contour_toggle.isChecked():
            self._adapter.clear_scalar_result()
            self.result_status_label.setText("Result contour is hidden.")
            self._render_interactive_result_state()
            return
        component = self.scalar_component_selector.currentText() or None
        manual_range = None
        if self.range_mode_selector.currentText() == "MANUAL":
            manual_range = (
                float(self.manual_min_input.value()),
                float(self.manual_max_input.value()),
            )
        result = self._adapter.set_scalar_result(
            field_name,
            component=component,
            range_mode=self.range_mode_selector.currentText(),
            manual_range=manual_range,
            colormap=self.colormap_selector.currentText(),
            colorbar_visible=self.colorbar_toggle.isChecked(),
            render=allow_render,
        )
        if result.data_range is not None:
            self.data_range_label.setText(_format_numeric_range(result.data_range))
        if result.display_range is not None:
            self.applied_range_label.setText(_format_numeric_range(result.display_range))
        self.result_status_label.setText(
            "Scalar result applied."
            if result.applied and allow_render
            else (
                "Scalar values are available; renderer backend is unavailable."
                if result.applied
                else "; ".join(result.diagnostics)
            )
        )
        statistics = result.statistics
        self.scalar_statistics_label.setText(
            "Scalar statistics: "
            f"finite {statistics.finite_count}, nonfinite {statistics.nonfinite_count}, "
            f"min {_format_optional_number(statistics.minimum)}, "
            f"max {_format_optional_number(statistics.maximum)}, "
            f"mean {_format_optional_number(statistics.mean)}, "
            f"median {_format_optional_number(statistics.median)}"
        )
        self._render_interactive_result_state()

    def _apply_interactive_vector_result(self) -> None:
        if not isinstance(self._adapter, ActiveSceneController):
            return
        selected = self.vector_selector.currentText()
        if not selected.startswith(_RESULT_VECTOR_PREFIX):
            self.result_status_label.setText("Select a result vector field.")
            return
        field_name = selected[len(_RESULT_VECTOR_PREFIX) :]
        result = self._adapter.set_vector_result(
            field_name,
            maximum_glyph_count=max(
                1,
                int(self.glyph_max_count_input.value()) or 500,
            ),
            scale=float(self.glyph_scale_input.value()),
            scale_mode=self.vector_scale_mode_selector.currentText(),
        )
        self.vector_count_label.setText(
            f"{result.candidate_count} / {result.sampled_count} / "
            f"{result.omitted_count} / {result.zero_vector_count}"
        )
        self.result_status_label.setText(
            "Vector result applied." if result.applied else "; ".join(result.diagnostics)
        )
        self._render_interactive_result_state()

    def _apply_interactive_deformation(self) -> None:
        if not isinstance(self._adapter, ActiveSceneController):
            return
        field_name = self.deformation_field_selector.currentText()
        if not field_name or field_name.startswith("("):
            self.result_status_label.setText(
                "No exact typed displacement field is eligible for deformation."
            )
            return
        manual_scale = (
            float(self.deformation_scale_input.value())
            if self.deformation_scale_mode_selector.currentText() == "MANUAL"
            else None
        )
        result = self._adapter.set_deformed_result(
            field_name,
            mode=self.deformation_mode_selector.currentText(),
            scale_mode=self.deformation_scale_mode_selector.currentText(),
            manual_scale=manual_scale,
        )
        self.result_status_label.setText(
            (f"Deformation {result.mode.value.lower()} applied at visual scale {result.scale:.6g}.")
            if result.applied
            else "; ".join(result.diagnostics)
        )
        self._render_interactive_result_state()

    def _reset_interactive_result_view(self) -> None:
        if isinstance(self._adapter, ActiveSceneController):
            self._adapter.clear_interactive_results()
        self.contour_toggle.blockSignals(True)
        self.contour_toggle.setChecked(False)
        self.contour_toggle.blockSignals(False)
        self.glyph_toggle.setChecked(False)
        self.deformation_mode_selector.setCurrentText("ORIGINAL")
        self.result_probe_label.setText("No result probe.")
        self.selected_result_table.setRowCount(0)
        self.scalar_statistics_label.setText("Scalar statistics: —")
        self.result_status_label.setText("Interactive result view reset.")
        self._refresh_interactive_result_controls()

    def _on_contour_toggled(self, checked: bool) -> None:
        if isinstance(self._adapter, ActiveSceneController) and not checked:
            self._adapter.clear_scalar_result()
            self._render_interactive_result_state()
        else:
            self._refresh_interactive_result_controls()

    def _refresh_interactive_result_controls(self) -> None:
        if not isinstance(self._adapter, ActiveSceneController):
            available = False
            state = "UNRESOLVED"
        else:
            view_model = self._adapter.interactive_results_view_model
            available = view_model.renderer_available
            state = view_model.binding_state
        resolved = state == "RESOLVED"
        has_scalar = self.selected_result_field_id() is not None
        has_vector = self.vector_selector.currentText().startswith(_RESULT_VECTOR_PREFIX)
        manual = self.range_mode_selector.currentText() == "MANUAL"
        manual_range_valid = not manual or float(self.manual_min_input.value()) < float(
            self.manual_max_input.value()
        )
        self.apply_scalar_button.setEnabled(
            resolved
            and available
            and has_scalar
            and self.contour_toggle.isChecked()
            and manual_range_valid
        )
        self.apply_vector_button.setEnabled(
            resolved and available and has_vector and self.glyph_toggle.isChecked()
        )
        self.manual_min_input.setEnabled(resolved and manual)
        self.manual_max_input.setEnabled(resolved and manual)
        vector_manual = self.vector_scale_mode_selector.currentText() == "MANUAL"
        self.glyph_scale_input.setEnabled(
            resolved and has_vector and self.glyph_toggle.isChecked() and vector_manual
        )
        deformation_available = (
            self.deformation_field_selector.count() > 0
            and not self.deformation_field_selector.currentText().startswith("(")
        )
        deformation_manual = self.deformation_scale_mode_selector.currentText() == "MANUAL"
        self.deformation_scale_input.setEnabled(
            resolved and deformation_available and deformation_manual
        )
        self.apply_deformation_button.setEnabled(resolved and available and deformation_available)
        self.result_dataset_selector.setEnabled(self._result_dataset is not None)
        self.contour_toggle.setEnabled(resolved and has_scalar)
        self.reset_result_view_button.setEnabled(self._result_dataset is not None)

    def _render_interactive_result_state(self) -> None:
        if not isinstance(self._adapter, ActiveSceneController):
            self.binding_schema_label.setText("")
            self.binding_state_label.setText("UNRESOLVED")
            self._refresh_interactive_result_controls()
            return
        view_model = self._adapter.interactive_results_view_model
        self.binding_schema_label.setText(view_model.binding_schema)
        self.binding_state_label.setText(view_model.binding_state)
        if view_model.scalar is not None:
            if view_model.scalar.data_range is not None:
                self.data_range_label.setText(_format_numeric_range(view_model.scalar.data_range))
            if view_model.scalar.display_range is not None:
                self.applied_range_label.setText(
                    _format_numeric_range(view_model.scalar.display_range)
                )
            statistics = view_model.scalar.statistics
            self.scalar_statistics_label.setText(
                "Scalar statistics: "
                f"finite {statistics.finite_count}, "
                f"nonfinite {statistics.nonfinite_count}, "
                f"min {_format_optional_number(statistics.minimum)}, "
                f"max {_format_optional_number(statistics.maximum)}, "
                f"mean {_format_optional_number(statistics.mean)}, "
                f"median {_format_optional_number(statistics.median)}"
            )
        if view_model.vector is not None:
            result = view_model.vector
            self.vector_count_label.setText(
                f"{result.candidate_count} / {result.sampled_count} / "
                f"{result.omitted_count} / {result.zero_vector_count}"
            )
        if view_model.probe is not None:
            probe = view_model.probe
            if probe.value is None:
                self.result_probe_label.setText(
                    f"{probe.entity_display_id}: {probe.display_value} ({probe.value_status.value})"
                )
            else:
                unit = f" {probe.unit}" if probe.unit else ""
                self.result_probe_label.setText(
                    f"{probe.entity_display_id}: {probe.value:.12g}{unit}"
                )
        self.selected_result_table.setRowCount(0)
        if view_model.table is not None:
            for row_index, row in enumerate(view_model.table.rows):
                self.selected_result_table.insertRow(row_index)
                values = (
                    row.entity_display_id,
                    (f"{view_model.table.field_name} / {view_model.table.component}"),
                    row.display_value,
                    row.unit,
                )
                for column, value in enumerate(values):
                    self.selected_result_table.setItem(
                        row_index,
                        column,
                        QtWidgets.QTableWidgetItem(value),
                    )
        if view_model.deformation is not None and view_model.deformation.applied:
            self.deformation_mode_selector.setCurrentText(view_model.deformation.mode.value)
        catalog = view_model.catalog
        field_name = self.selected_result_field_id()
        if catalog is not None and field_name:
            try:
                descriptor = catalog.field(field_name)
            except KeyError:
                pass
            else:
                self.result_association_label.setText(f"Association: {descriptor.association}")
        if view_model.binding_state != "RESOLVED":
            self.result_status_label.setText(view_model.binding_reason)
        elif not view_model.renderer_available:
            reason = view_model.backend_reason or "renderer backend unavailable"
            self.result_status_label.setText(
                f"Result values are available; rendering is unavailable: {reason}"
            )
        self._refresh_interactive_result_controls()
        callback = self._interactive_result_state_changed_callback
        if callback is not None:
            callback()

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
            f" field '{field_id}'" if field_id else "; select a result field before persisting"
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
        catalog = (
            self._adapter.interactive_result_field_catalog
            if isinstance(self._adapter, ActiveSceneController)
            else None
        )
        result_names = (
            tuple(descriptor.field_id for descriptor in catalog.fields)
            if catalog is not None and catalog.binding_status.value == "READY"
            else result_field_names(self._result_dataset)
        )
        for name in result_names:
            items.append(f"{_RESULT_PREFIX}{name}")
        self.scalar_selector.addItems(items)
        self.scalar_selector.setCurrentText(current if current in items else _NONE_FIELD)
        self.scalar_selector.blockSignals(False)
        self._populate_scalar_components()

    def _populate_vector_selector(self, mesh: MeshData | None) -> None:
        """Fill vector selector from existing mesh arrays and compatible result fields."""
        current = self.vector_selector.currentText()
        self.vector_selector.blockSignals(True)
        self.vector_selector.clear()
        items = [_NO_VECTOR_FIELD]
        for name in mesh_vector_field_names(mesh):
            items.append(name)
        if mesh is not None and self._result_dataset is not None:
            catalog = (
                self._adapter.interactive_result_field_catalog
                if isinstance(self._adapter, ActiveSceneController)
                else None
            )
            if catalog is not None and catalog.binding_status.value == "READY":
                names = tuple(
                    descriptor.field_id
                    for descriptor in catalog.fields
                    if descriptor.kind.value.endswith("VECTOR")
                )
            else:
                names = tuple(
                    name
                    for name in result_field_names(self._result_dataset)
                    if map_result_vector_field_to_mesh(
                        mesh,
                        self._result_dataset,
                        field=name,
                    ).applied
                )
            items.extend(f"{_RESULT_VECTOR_PREFIX}{name}" for name in names)
        self.vector_selector.addItems(items)
        self.vector_selector.setCurrentText(current if current in items else _NO_VECTOR_FIELD)
        self.vector_selector.blockSignals(False)
        self._set_vector_controls_enabled(mesh is not None)

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
            field_name = selected[len(_RESULT_PREFIX) :]
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

    def _resolve_glyph_source(self, mesh: MeshData) -> tuple[MeshData, str | None, tuple[str, ...]]:
        """Resolve the selected vector source to a render mesh plus glyph field."""
        if not self.glyph_toggle.isChecked():
            return mesh, None, ()

        selected = self.vector_selector.currentText()
        if not selected or selected == _NO_VECTOR_FIELD:
            return mesh, None, (_NO_VECTOR_FIELD_SELECTED_TEXT,)

        if selected.startswith(_RESULT_VECTOR_PREFIX):
            field_name = selected[len(_RESULT_VECTOR_PREFIX) :]
            result_field = self._result_vector_field_lookup.get(field_name)
            if result_field is None or self._result_dataset is None:
                return (
                    mesh,
                    None,
                    (f"Result vector field '{field_name}' is not available.",),
                )
            mapping = map_result_vector_field_to_mesh(
                mesh,
                self._result_dataset,
                field=field_name,
            )
            if not mapping.applied:
                return mesh, None, mapping.diagnostics
            return mapping.mesh_data, mapping.field_name, ()

        if selected not in mesh_vector_field_names(mesh):
            return mesh, None, (f"Vector field '{selected}' is not present on the mesh.",)
        return mesh, selected, ()

    def _selected_glyph_max_count(self) -> int | None:
        value = int(self.glyph_max_count_input.value())
        return value if value > 0 else None

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.load_button.setEnabled(enabled)
        self.capture_button.setEnabled(enabled)
        self.bind_result_button.setEnabled(enabled and self._result_dataset is not None)
        self.rebind_result_button.setEnabled(enabled and self._result_dataset is not None)
        self._set_vector_controls_enabled(enabled)

    def _set_vector_controls_enabled(self, enabled: bool) -> None:
        has_vector_options = self.vector_selector.count() > 1
        selected = self.vector_selector.currentText()
        glyph_available = enabled and has_vector_options and selected not in ("", _NO_VECTOR_FIELD)
        self.vector_selector.setEnabled(enabled and has_vector_options)
        self.glyph_toggle.setEnabled(glyph_available)
        self.glyph_scale_input.setEnabled(glyph_available and self.glyph_toggle.isChecked())
        self.glyph_max_count_input.setEnabled(glyph_available and self.glyph_toggle.isChecked())

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
        self.rebind_result_button.setEnabled(has_mesh and self._result_dataset is not None)

        self.diagnostics_list.clear()
        for warning in self._state.warning_messages:
            self.diagnostics_list.addItem(warning)

        self._render_interactive_result_state()
        self._render_screenshot_status()


def build_mesh_viewer_panel(
    parent: object | None = None,
    *,
    scene_adapter: SceneAdapterProtocol | None = None,
) -> object:
    """Factory mirroring the other GUI widget builders."""
    return MeshViewerPanel(parent, scene_adapter=scene_adapter)


def _format_numeric_range(value_range: tuple[float, float]) -> str:
    return f"{value_range[0]:.12g} / {value_range[1]:.12g}"


def _format_optional_number(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.12g}"


def _staged_screenshot_rows(
    records: Sequence[SceneScreenshotRecord],
) -> tuple[str, ...]:
    """Format staged screenshot records as deterministic display rows (pure)."""
    rows: list[str] = []
    for record in records:
        record_id = str(getattr(record, "id", "") or "scene-screenshot")
        caption = str(getattr(record, "caption", "") or "").strip() or "(no caption)"
        path = str(getattr(record, "path", "") or "")
        basename = path.replace("\\", "/").rsplit("/", 1)[-1] if path else "(no image path)"
        rows.append(f"{record_id} - {caption} - {basename}")
    return tuple(rows)


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
