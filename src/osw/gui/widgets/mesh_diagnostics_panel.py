"""Thin transient Mesh Diagnostics controls and deterministic table."""

from __future__ import annotations

from math import isfinite

from PySide6 import QtCore, QtWidgets

from osw.gui.mesh_diagnostics_view_model import MeshDiagnosticsViewModel


class MeshDiagnosticsPanel(QtWidgets.QWidget):
    analyzeRequested = QtCore.Signal()
    thresholdChanged = QtCore.Signal(float)
    highlightToggled = QtCore.Signal(bool)
    isolateToggled = QtCore.Signal(bool)
    restoreRequested = QtCore.Signal()
    clearRequested = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("oswMeshDiagnosticsPanel")
        self._view_model: MeshDiagnosticsViewModel | None = None
        self._build_ui()
        self._connect()
        self.clear_view_model()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(QtWidgets.QLabel("Mesh Diagnostics", self))

        self.metric_label = QtWidgets.QLabel(
            "Edge aspect ratio preview",
            self,
        )
        self.metric_label.setObjectName("oswMeshDiagnosticsMetric")
        layout.addWidget(self.metric_label)
        self.metric_claim_label = QtWidgets.QLabel(
            "Preview-grade diagnostic only; not solver-certified mesh quality.",
            self,
        )
        self.metric_claim_label.setWordWrap(True)
        layout.addWidget(self.metric_claim_label)

        summary = QtWidgets.QFormLayout()
        self.mesh_label = QtWidgets.QLabel("active mesh", self)
        self.node_count_label = QtWidgets.QLabel("0", self)
        self.cell_count_label = QtWidgets.QLabel("0", self)
        self.cell_types_label = QtWidgets.QLabel("none", self)
        self.bounding_box_label = QtWidgets.QLabel("unavailable", self)
        self.evaluated_count_label = QtWidgets.QLabel("0", self)
        self.bad_count_label = QtWidgets.QLabel("0 (0.0%)", self)
        self.degenerate_count_label = QtWidgets.QLabel("0", self)
        self.invalid_count_label = QtWidgets.QLabel("0", self)
        self.unsupported_count_label = QtWidgets.QLabel("0", self)
        self.range_label = QtWidgets.QLabel("unavailable", self)
        summary.addRow("Mesh", self.mesh_label)
        summary.addRow("Nodes", self.node_count_label)
        summary.addRow("Cells", self.cell_count_label)
        summary.addRow("Cell types", self.cell_types_label)
        summary.addRow("Bounding box", self.bounding_box_label)
        summary.addRow("Evaluated", self.evaluated_count_label)
        summary.addRow("Bad / degenerate", self.bad_count_label)
        summary.addRow("Degenerate", self.degenerate_count_label)
        summary.addRow("Invalid", self.invalid_count_label)
        summary.addRow("Unsupported", self.unsupported_count_label)
        summary.addRow("Min / max / mean", self.range_label)
        layout.addLayout(summary)

        threshold_row = QtWidgets.QHBoxLayout()
        threshold_row.addWidget(QtWidgets.QLabel("Bad-cell threshold", self))
        self.threshold_edit = QtWidgets.QLineEdit("10", self)
        self.threshold_edit.setObjectName("oswMeshDiagnosticsThreshold")
        self.threshold_edit.setToolTip(
            "Enter a finite positive edge-aspect-ratio threshold."
        )
        self.apply_threshold_button = QtWidgets.QPushButton("Apply", self)
        threshold_row.addWidget(self.threshold_edit)
        threshold_row.addWidget(self.apply_threshold_button)
        layout.addLayout(threshold_row)

        action_row = QtWidgets.QHBoxLayout()
        self.analyze_button = QtWidgets.QPushButton("Analyze", self)
        self.highlight_check = QtWidgets.QCheckBox("Highlight bad cells", self)
        self.isolate_check = QtWidgets.QCheckBox("Isolate bad cells", self)
        self.restore_button = QtWidgets.QPushButton("Restore", self)
        self.clear_button = QtWidgets.QPushButton("Clear overlay", self)
        action_row.addWidget(self.analyze_button)
        action_row.addWidget(self.highlight_check)
        action_row.addWidget(self.isolate_check)
        action_row.addWidget(self.restore_button)
        action_row.addWidget(self.clear_button)
        layout.addLayout(action_row)

        filter_row = QtWidgets.QHBoxLayout()
        filter_row.addWidget(QtWidgets.QLabel("Table", self))
        self.table_filter = QtWidgets.QComboBox(self)
        self.table_filter.addItems(
            ("All", "Bad / degenerate", "Invalid / unsupported")
        )
        filter_row.addWidget(self.table_filter)
        layout.addLayout(filter_row)

        self.table = QtWidgets.QTableWidget(0, 6, self)
        self.table.setObjectName("oswMeshDiagnosticsTable")
        self.table.setHorizontalHeaderLabels(
            (
                "Stable cell",
                "Cell type",
                "Block / local",
                "Status",
                "Metric value",
                "Reason",
            )
        )
        self.table.setEditTriggers(
            QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.analysis_state_label = QtWidgets.QLabel("No mesh analysis.", self)
        self.analysis_state_label.setWordWrap(True)
        layout.addWidget(self.analysis_state_label)
        self.status_label = QtWidgets.QLabel("", self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        self.deferred_scope_label = QtWidgets.QLabel(
            "Read-only preview: no mesh repair, deletion, smoothing, refinement, "
            "NamedSelection creation, setup mutation, or solver execution.",
            self,
        )
        self.deferred_scope_label.setWordWrap(True)
        layout.addWidget(self.deferred_scope_label)

    def _connect(self) -> None:
        self.analyze_button.clicked.connect(self.analyzeRequested.emit)
        self.apply_threshold_button.clicked.connect(self._emit_threshold)
        self.highlight_check.toggled.connect(self.highlightToggled.emit)
        self.isolate_check.toggled.connect(self.isolateToggled.emit)
        self.restore_button.clicked.connect(self.restoreRequested.emit)
        self.clear_button.clicked.connect(self.clearRequested.emit)
        self.table_filter.currentTextChanged.connect(self._refresh_table)

    def clear_view_model(self) -> None:
        self._view_model = None
        self.mesh_label.setText("active mesh")
        for label in (
            self.node_count_label,
            self.cell_count_label,
            self.evaluated_count_label,
            self.degenerate_count_label,
            self.invalid_count_label,
            self.unsupported_count_label,
        ):
            label.setText("0")
        self.cell_types_label.setText("none")
        self.bounding_box_label.setText("unavailable")
        self.bad_count_label.setText("0 (0.0%)")
        self.range_label.setText("unavailable")
        self.table.setRowCount(0)
        self.analysis_state_label.setText("No mesh analysis.")
        self.status_label.setText("Load an in-memory mesh, then select Analyze.")
        self._set_overlay_actions(False, "Run analysis before using overlays.")

    def set_view_model(self, view_model: MeshDiagnosticsViewModel) -> None:
        self._view_model = view_model
        self.metric_label.setText(view_model.metric_label)
        self.mesh_label.setText(view_model.mesh_label)
        self.node_count_label.setText(str(view_model.node_count))
        self.cell_count_label.setText(str(view_model.cell_count))
        self.cell_types_label.setText(
            ", ".join(
                f"{cell_type}:{count}"
                for cell_type, count in view_model.cell_type_distribution
            )
            or "none"
        )
        self.bounding_box_label.setText(view_model.bounding_box_text)
        self.evaluated_count_label.setText(str(view_model.evaluated_count))
        self.bad_count_label.setText(
            f"{view_model.bad_count} ({view_model.bad_percentage:.1f}%)"
        )
        self.degenerate_count_label.setText(str(view_model.degenerate_count))
        self.invalid_count_label.setText(str(view_model.invalid_count))
        self.unsupported_count_label.setText(str(view_model.unsupported_count))
        self.range_label.setText(
            _range_text(view_model.minimum, view_model.maximum, view_model.mean)
        )
        self.threshold_edit.setText(f"{view_model.threshold:g}")
        self.analysis_state_label.setText(
            "Analysis ready."
            if view_model.analysis_available
            else "No mesh analysis."
        )
        if view_model.backend_diagnostic:
            self.status_label.setText(view_model.backend_diagnostic)
        elif view_model.diagnostics:
            self.status_label.setText(" ".join(view_model.diagnostics))
        else:
            self.status_label.setText("Mesh Diagnostics analysis is ready.")
        reason = (
            view_model.backend_diagnostic
            or "No highlightable bad or degenerate cells at this threshold."
        )
        self._set_overlay_actions(
            view_model.overlay_actions_enabled,
            reason,
        )
        highlight_blocker = QtCore.QSignalBlocker(self.highlight_check)
        isolate_blocker = QtCore.QSignalBlocker(self.isolate_check)
        self.highlight_check.setChecked(view_model.highlight_visible)
        self.isolate_check.setChecked(view_model.isolated)
        del highlight_blocker, isolate_blocker
        self.clear_button.setEnabled(view_model.analysis_available)
        self._refresh_table()

    def set_status(self, message: str) -> None:
        self.status_label.setText(str(message or ""))

    def _set_overlay_actions(self, enabled: bool, reason: str) -> None:
        for control in (
            self.highlight_check,
            self.isolate_check,
            self.restore_button,
        ):
            control.setEnabled(enabled)
            control.setToolTip("" if enabled else reason)
        self.clear_button.setEnabled(self._view_model is not None)

    def _emit_threshold(self) -> None:
        try:
            threshold = float(self.threshold_edit.text().strip())
        except ValueError:
            threshold = float("nan")
        if not isfinite(threshold) or threshold <= 0.0:
            self.status_label.setText(
                "Bad-cell threshold must be a finite positive number."
            )
            return
        self.thresholdChanged.emit(threshold)

    def _refresh_table(self) -> None:
        view_model = self._view_model
        rows = () if view_model is None else view_model.rows
        selected_filter = self.table_filter.currentText()
        if selected_filter == "Bad / degenerate":
            rows = tuple(row for row in rows if row.is_bad)
        elif selected_filter == "Invalid / unsupported":
            rows = tuple(
                row
                for row in rows
                if row.status in {"INVALID", "UNSUPPORTED"}
            )
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = (
                row.stable_cell_id,
                row.cell_type,
                f"{row.block_ordinal} / {row.cell_ordinal}",
                row.status,
                "—" if row.metric_value is None else f"{row.metric_value:.8g}",
                row.reason,
            )
            for column, value in enumerate(values):
                self.table.setItem(
                    row_index,
                    column,
                    QtWidgets.QTableWidgetItem(value),
                )


def _range_text(
    minimum: float | None,
    maximum: float | None,
    mean: float | None,
) -> str:
    if minimum is None or maximum is None or mean is None:
        return "unavailable"
    return f"{minimum:.8g} / {maximum:.8g} / {mean:.8g}"


__all__ = ["MeshDiagnosticsPanel"]
