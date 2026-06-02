"""PySide6 field metadata and optional render control panel."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.post.field_dataset import FieldRenderRequest, FieldRenderResult
from osw.post.field_view_model import FieldViewModel
from osw.post.pyvista_scene import render_field_view

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class FieldViewerPanel(_BaseWidget):
    """ResultViewer subpanel for field arrays and optional PyVista rendering."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswFieldViewerPanel")
        self._view_model: FieldViewModel | None = None
        self._last_render_result: FieldRenderResult | None = None

        self.summary_label = QtWidgets.QLabel("No field dataset loaded.", self)
        self.summary_label.setObjectName("oswFieldSummaryLabel")
        self.summary_label.setWordWrap(True)
        self.empty_state = QtWidgets.QLabel("No mesh field arrays are available.", self)
        self.empty_state.setObjectName("oswFieldEmptyState")
        self.empty_state.setWordWrap(True)

        self.scalar_selector = QtWidgets.QComboBox(self)
        self.scalar_selector.setObjectName("oswFieldScalarSelector")
        self.render_button = QtWidgets.QPushButton("Render Scalar", self)
        self.render_button.setObjectName("oswFieldRenderButton")
        self.screenshot_button = QtWidgets.QPushButton("Export Screenshot", self)
        self.screenshot_button.setObjectName("oswFieldScreenshotButton")
        self.render_status = QtWidgets.QLabel("Rendering not requested.", self)
        self.render_status.setObjectName("oswFieldRenderStatus")
        self.render_status.setWordWrap(True)

        self.array_table = QtWidgets.QTableWidget(self)
        self.array_table.setObjectName("oswFieldArrayTable")
        self.array_table.setColumnCount(6)
        self.array_table.setHorizontalHeaderLabels(
            ["Name", "Location", "Type", "Components", "Values", "Unit"]
        )

        self.artifact_table = QtWidgets.QTableWidget(self)
        self.artifact_table.setObjectName("oswFieldArtifactTable")
        self.artifact_table.setColumnCount(5)
        self.artifact_table.setHorizontalHeaderLabels(
            ["Role", "Path", "Format", "Exists", "Size"]
        )

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswFieldDiagnosticsList")

        controls = QtWidgets.QHBoxLayout()
        controls.addWidget(self.scalar_selector)
        controls.addWidget(self.render_button)
        controls.addWidget(self.screenshot_button)
        controls.addStretch(1)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.empty_state)
        layout.addLayout(controls)
        layout.addWidget(self.render_status)
        layout.addWidget(self.array_table)
        layout.addWidget(self.artifact_table)
        layout.addWidget(self.diagnostics_list)

        self.render_button.clicked.connect(lambda _checked=False: self.render_preview())
        self.screenshot_button.clicked.connect(
            lambda _checked=False: self._on_screenshot_requested()
        )
        self._set_controls_enabled(False)

    def set_field_view_model(self, view_model: FieldViewModel) -> None:
        self._view_model = view_model
        self._last_render_result = None
        self.summary_label.setText(
            f"{view_model.title}\n"
            f"Source: {view_model.source or 'Not recorded'}\n"
            f"Fields: {len(view_model.arrays)} | Artifacts: {len(view_model.artifacts)}"
        )
        self.empty_state.setText(view_model.empty_state_message)
        self.empty_state.setVisible(bool(view_model.empty_state_message))
        self._populate_scalar_selector(view_model)
        self._populate_arrays(view_model)
        self._populate_artifacts(view_model)
        self._populate_diagnostics(view_model)
        self.render_status.setText("Rendering not requested.")
        self._set_controls_enabled(bool(view_model.scalar_fields or view_model.vector_fields))

    def current_field_view_model(self) -> FieldViewModel | None:
        return self._view_model

    def last_render_result(self) -> FieldRenderResult | None:
        return self._last_render_result

    def render_preview(
        self,
        *,
        loader: Callable[[], Any] | None = None,
        pyvista_module: Any | None = None,
    ) -> FieldRenderResult:
        if self._view_model is None:
            result = FieldRenderResult(
                status="placeholder",
                message="No field dataset is loaded.",
            )
            self._record_render_result(result)
            return result
        request = self._current_render_request()
        result = render_field_view(
            self._view_model,
            request,
            loader=loader,
            pyvista_module=pyvista_module,
        )
        self._record_render_result(result)
        return result

    def export_screenshot(
        self,
        target_path: str | Path,
        *,
        loader: Callable[[], Any] | None = None,
        pyvista_module: Any | None = None,
    ) -> FieldRenderResult:
        if self._view_model is None:
            result = FieldRenderResult(status="placeholder", message="No field dataset is loaded.")
            self._record_render_result(result)
            return result
        request = self._current_render_request(screenshot_path=str(target_path))
        result = render_field_view(
            self._view_model,
            request,
            loader=loader,
            pyvista_module=pyvista_module,
        )
        self._record_render_result(result)
        return result

    def _current_render_request(self, *, screenshot_path: str = "") -> FieldRenderRequest:
        assert self._view_model is not None
        base = self._view_model.default_render_request
        selected_scalar = self.scalar_selector.currentText() or base.scalar_field
        return FieldRenderRequest(
            dataset_id=self._view_model.dataset_id,
            scalar_field=selected_scalar,
            vector_field="" if selected_scalar else base.vector_field,
            mode="scalar" if selected_scalar else base.mode,
            artifact_path=base.artifact_path,
            screenshot_path=screenshot_path,
            off_screen=True,
        )

    def _populate_scalar_selector(self, view_model: FieldViewModel) -> None:
        self.scalar_selector.blockSignals(True)
        self.scalar_selector.clear()
        for field_name in view_model.scalar_fields:
            self.scalar_selector.addItem(field_name)
        self.scalar_selector.blockSignals(False)

    def _populate_arrays(self, view_model: FieldViewModel) -> None:
        self.array_table.setRowCount(len(view_model.arrays))
        for row, array in enumerate(view_model.arrays):
            values = (
                array.name,
                array.location,
                array.field_type,
                ", ".join(array.components),
                str(array.value_count),
                array.unit,
            )
            for column, value in enumerate(values):
                self.array_table.setItem(row, column, QtWidgets.QTableWidgetItem(value))
        self.array_table.resizeColumnsToContents()

    def _populate_artifacts(self, view_model: FieldViewModel) -> None:
        self.artifact_table.setRowCount(len(view_model.artifacts))
        for row, artifact in enumerate(view_model.artifacts):
            values = (
                artifact.role,
                artifact.path,
                artifact.format,
                "yes" if artifact.exists else "missing",
                "" if artifact.size_bytes is None else str(artifact.size_bytes),
            )
            for column, value in enumerate(values):
                self.artifact_table.setItem(row, column, QtWidgets.QTableWidgetItem(value))
        self.artifact_table.resizeColumnsToContents()

    def _populate_diagnostics(self, view_model: FieldViewModel) -> None:
        self.diagnostics_list.clear()
        diagnostics = view_model.diagnostics or ("No field diagnostics.",)
        for diagnostic in diagnostics:
            self.diagnostics_list.addItem(diagnostic)

    def _record_render_result(self, result: FieldRenderResult) -> None:
        self._last_render_result = result
        self.render_status.setText(result.message)
        if result.diagnostics:
            for diagnostic in result.diagnostics:
                self.diagnostics_list.addItem(diagnostic)

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.scalar_selector.setEnabled(enabled)
        self.render_button.setEnabled(enabled)
        self.screenshot_button.setEnabled(enabled)

    def _on_screenshot_requested(self) -> None:
        result = FieldRenderResult(
            status="placeholder",
            message="Screenshot export requires a target path from the caller.",
        )
        self._record_render_result(result)


def build_field_viewer_panel(parent: object | None = None) -> object:
    return FieldViewerPanel(parent)
