"""Thin Qt surface for deterministic Scaled Jacobian mesh diagnostics."""

from __future__ import annotations

from math import isfinite

from PySide6 import QtCore, QtWidgets

from osw.gui.mesh_diagnostics_view_model import MeshDiagnosticsViewModel


class MeshDiagnosticsPanel(QtWidgets.QWidget):
    analyzeRequested = QtCore.Signal()
    thresholdChanged = QtCore.Signal(float)
    rangeChanged = QtCore.Signal(str, object)
    coloringToggled = QtCore.Signal(bool)
    highlightToggled = QtCore.Signal(bool)
    filterModeChanged = QtCore.Signal(str)
    # Compatibility signals retained for the existing shell wiring.
    isolateToggled = QtCore.Signal(bool)
    restoreRequested = QtCore.Signal()
    selectBadRequested = QtCore.Signal()
    createNamedSelectionRequested = QtCore.Signal(str)
    exportJsonRequested = QtCore.Signal()
    exportCsvRequested = QtCore.Signal()
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

        self.metric_label = QtWidgets.QLabel("Scaled Jacobian", self)
        self.metric_label.setObjectName("oswMeshDiagnosticsMetric")
        layout.addWidget(self.metric_label)
        self.metric_claim_label = QtWidgets.QLabel(
            "Higher is better; negative values indicate inverted orientation for "
            "topology where orientation is defined; values near zero indicate "
            "degeneracy or severe distortion. The threshold is a user review "
            "threshold, not a universal solver-acceptance standard.",
            self,
        )
        self.metric_claim_label.setWordWrap(True)
        layout.addWidget(self.metric_claim_label)

        summary = QtWidgets.QFormLayout()
        self.mesh_label = QtWidgets.QLabel("active mesh", self)
        self.node_count_label = QtWidgets.QLabel("0", self)
        self.cell_count_label = QtWidgets.QLabel("0", self)
        self.block_count_label = QtWidgets.QLabel("0", self)
        self.cell_types_label = QtWidgets.QLabel("none", self)
        self.provider_label = QtWidgets.QLabel("not evaluated", self)
        self.coverage_label = QtWidgets.QLabel("0 / 0 (0.0%)", self)
        self.bounding_box_label = QtWidgets.QLabel("unavailable", self)
        self.extents_label = QtWidgets.QLabel("unavailable", self)
        self.evaluated_count_label = QtWidgets.QLabel("0", self)
        self.bad_count_label = QtWidgets.QLabel("0 (0.0%)", self)
        self.degenerate_count_label = QtWidgets.QLabel("0", self)
        self.inverted_count_label = QtWidgets.QLabel("0", self)
        self.invalid_count_label = QtWidgets.QLabel("0", self)
        self.unsupported_count_label = QtWidgets.QLabel("0", self)
        self.orphan_count_label = QtWidgets.QLabel("0", self)
        self.range_label = QtWidgets.QLabel("unavailable", self)
        for name, widget in (
            ("Mesh", self.mesh_label),
            ("Nodes", self.node_count_label),
            ("Cells", self.cell_count_label),
            ("Blocks", self.block_count_label),
            ("Cell types", self.cell_types_label),
            ("Provider", self.provider_label),
            ("Coverage", self.coverage_label),
            ("Bounding box", self.bounding_box_label),
            ("Extents", self.extents_label),
            ("Covered", self.evaluated_count_label),
            ("Bad", self.bad_count_label),
            ("Inverted", self.inverted_count_label),
            ("Degenerate", self.degenerate_count_label),
            ("Invalid", self.invalid_count_label),
            ("Uncovered", self.unsupported_count_label),
            ("Orphan points", self.orphan_count_label),
            ("Min / max / mean / median", self.range_label),
        ):
            summary.addRow(name, widget)
        layout.addLayout(summary)

        threshold_row = QtWidgets.QHBoxLayout()
        threshold_row.addWidget(QtWidgets.QLabel("Bad when ≤", self))
        self.threshold_edit = QtWidgets.QLineEdit("0", self)
        self.threshold_edit.setObjectName("oswMeshDiagnosticsThreshold")
        self.threshold_edit.setToolTip(
            "Scaled Jacobian review threshold within [-1, 1]; default 0."
        )
        self.apply_threshold_button = QtWidgets.QPushButton("Apply", self)
        threshold_row.addWidget(self.threshold_edit)
        threshold_row.addWidget(self.apply_threshold_button)
        layout.addLayout(threshold_row)

        range_row = QtWidgets.QHBoxLayout()
        self.range_mode = QtWidgets.QComboBox(self)
        self.range_mode.setObjectName("oswMeshDiagnosticsRangeMode")
        self.range_mode.addItems(("Auto", "Manual"))
        self.range_min_edit = QtWidgets.QLineEdit("-1", self)
        self.range_max_edit = QtWidgets.QLineEdit("1", self)
        self.apply_range_button = QtWidgets.QPushButton("Apply range", self)
        range_row.addWidget(self.range_mode)
        range_row.addWidget(self.range_min_edit)
        range_row.addWidget(self.range_max_edit)
        range_row.addWidget(self.apply_range_button)
        layout.addLayout(range_row)

        action_row = QtWidgets.QHBoxLayout()
        self.analyze_button = QtWidgets.QPushButton("Analyze", self)
        self.quality_check = QtWidgets.QCheckBox("Quality colors + legend", self)
        self.highlight_check = QtWidgets.QCheckBox("Highlight bad", self)
        self.filter_combo = QtWidgets.QComboBox(self)
        self.filter_combo.addItems(("Clear filter", "Hide bad", "Isolate bad"))
        self.isolate_check = QtWidgets.QCheckBox("Isolate bad cells", self)
        self.isolate_check.setVisible(False)
        self.restore_button = QtWidgets.QPushButton("Restore", self)
        self.clear_button = QtWidgets.QPushButton("Clear diagnostics", self)
        for widget in (
            self.analyze_button,
            self.quality_check,
            self.highlight_check,
            self.filter_combo,
            self.restore_button,
            self.clear_button,
        ):
            action_row.addWidget(widget)
        layout.addLayout(action_row)

        selection_row = QtWidgets.QHBoxLayout()
        self.select_bad_button = QtWidgets.QPushButton("Select bad elements", self)
        self.named_selection_name = QtWidgets.QLineEdit("Bad elements", self)
        self.named_selection_name.setObjectName("oswMeshDiagnosticsNamedSelectionName")
        self.create_named_selection_button = QtWidgets.QPushButton(
            "Create NamedSelection",
            self,
        )
        self.export_json_button = QtWidgets.QPushButton("Export JSON", self)
        self.export_csv_button = QtWidgets.QPushButton("Export CSV", self)
        for widget in (
            self.select_bad_button,
            self.named_selection_name,
            self.create_named_selection_button,
            self.export_json_button,
            self.export_csv_button,
        ):
            selection_row.addWidget(widget)
        layout.addLayout(selection_row)

        filter_row = QtWidgets.QHBoxLayout()
        filter_row.addWidget(QtWidgets.QLabel("Table", self))
        self.table_filter = QtWidgets.QComboBox(self)
        self.table_filter.addItems(("All", "Bad", "Invalid / uncovered"))
        filter_row.addWidget(self.table_filter)
        layout.addLayout(filter_row)

        self.table = QtWidgets.QTableWidget(0, 7, self)
        self.table.setObjectName("oswMeshDiagnosticsTable")
        self.table.setHorizontalHeaderLabels(
            (
                "Stable cell",
                "Cell type",
                "Block / local",
                "Status",
                "Category",
                "Scaled Jacobian",
                "Reason",
            )
        )
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.analysis_state_label = QtWidgets.QLabel("No mesh analysis.", self)
        self.analysis_state_label.setWordWrap(True)
        self.status_label = QtWidgets.QLabel("", self)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.analysis_state_label)
        layout.addWidget(self.status_label)
        self.deferred_scope_label = QtWidgets.QLabel(
            "Read-only diagnostics: no mesh repair, deletion, smoothing, refinement, "
            "solver execution, or automatic Project/file mutation.",
            self,
        )
        self.deferred_scope_label.setWordWrap(True)
        layout.addWidget(self.deferred_scope_label)

    def _connect(self) -> None:
        self.analyze_button.clicked.connect(self.analyzeRequested.emit)
        self.apply_threshold_button.clicked.connect(self._emit_threshold)
        self.apply_range_button.clicked.connect(self._emit_range)
        self.range_mode.currentTextChanged.connect(self._update_range_apply_enabled)
        self.range_min_edit.textChanged.connect(self._update_range_apply_enabled)
        self.range_max_edit.textChanged.connect(self._update_range_apply_enabled)
        self.quality_check.toggled.connect(self.coloringToggled.emit)
        self.highlight_check.toggled.connect(self.highlightToggled.emit)
        self.filter_combo.currentTextChanged.connect(self._emit_filter_mode)
        self.isolate_check.toggled.connect(self.isolateToggled.emit)
        self.restore_button.clicked.connect(self.restoreRequested.emit)
        self.select_bad_button.clicked.connect(self.selectBadRequested.emit)
        self.create_named_selection_button.clicked.connect(
            lambda: self.createNamedSelectionRequested.emit(
                self.named_selection_name.text().strip()
            )
        )
        self.export_json_button.clicked.connect(self.exportJsonRequested.emit)
        self.export_csv_button.clicked.connect(self.exportCsvRequested.emit)
        self.clear_button.clicked.connect(self.clearRequested.emit)
        self.table_filter.currentTextChanged.connect(self._refresh_table)

    def clear_view_model(self) -> None:
        self._view_model = None
        self.mesh_label.setText("active mesh")
        for label in (
            self.node_count_label,
            self.cell_count_label,
            self.block_count_label,
            self.evaluated_count_label,
            self.degenerate_count_label,
            self.inverted_count_label,
            self.invalid_count_label,
            self.unsupported_count_label,
            self.orphan_count_label,
        ):
            label.setText("0")
        self.cell_types_label.setText("none")
        self.provider_label.setText("not evaluated")
        self.coverage_label.setText("0 / 0 (0.0%)")
        self.bounding_box_label.setText("unavailable")
        self.extents_label.setText("unavailable")
        self.bad_count_label.setText("0 (0.0%)")
        self.range_label.setText("unavailable")
        self.table.setRowCount(0)
        self.analysis_state_label.setText("No mesh analysis.")
        self.status_label.setText("Load an in-memory mesh, then select Analyze.")
        self._set_actions(False, "Run analysis before using diagnostics actions.")
        self._update_range_apply_enabled()

    def set_view_model(self, view_model: MeshDiagnosticsViewModel) -> None:
        self._view_model = view_model
        self.metric_label.setText(view_model.metric_label)
        self.metric_claim_label.setText(
            f"{view_model.metric_semantics} The threshold is a user review "
            "threshold, not a universal solver-acceptance standard."
        )
        self.mesh_label.setText(view_model.mesh_label)
        self.node_count_label.setText(str(view_model.node_count))
        self.cell_count_label.setText(str(view_model.cell_count))
        self.block_count_label.setText(str(view_model.block_count))
        self.cell_types_label.setText(
            ", ".join(f"{name}:{count}" for name, count in view_model.cell_type_distribution)
            or "none"
        )
        self.provider_label.setText(
            f"{view_model.provider_schema or 'unavailable'} / "
            f"{view_model.provider_version or 'unavailable'}"
        )
        self.coverage_label.setText(
            f"{view_model.covered_count} / {view_model.cell_count} "
            f"({100.0 * view_model.coverage_ratio:.1f}%)"
        )
        self.bounding_box_label.setText(view_model.bounding_box_text)
        self.extents_label.setText(view_model.extents_text)
        self.evaluated_count_label.setText(str(view_model.covered_count))
        self.bad_count_label.setText(f"{view_model.bad_count} ({view_model.bad_percentage:.1f}%)")
        self.degenerate_count_label.setText(str(view_model.degenerate_count))
        self.inverted_count_label.setText(str(view_model.inverted_count))
        self.invalid_count_label.setText(str(view_model.invalid_count))
        self.unsupported_count_label.setText(str(view_model.unsupported_count))
        self.orphan_count_label.setText(str(view_model.orphan_point_count))
        self.range_label.setText(
            _range_text(
                view_model.minimum,
                view_model.maximum,
                view_model.mean,
                view_model.median,
            )
        )
        self.threshold_edit.setText(f"{view_model.threshold:g}")
        self.range_mode.setCurrentText(view_model.range_mode.title())
        self.range_min_edit.setText(f"{view_model.display_range[0]:g}")
        self.range_max_edit.setText(f"{view_model.display_range[1]:g}")
        self._update_range_apply_enabled()
        self.analysis_state_label.setText(_analysis_state_text(view_model))
        if view_model.backend_diagnostic:
            self.status_label.setText(view_model.backend_diagnostic)
        elif view_model.diagnostics:
            self.status_label.setText(" ".join(view_model.diagnostics))
        else:
            self.status_label.setText("Mesh Diagnostics analysis is ready.")
        reason = view_model.backend_diagnostic or "No applicable diagnostic cells."
        self._set_actions(view_model.overlay_actions_enabled, reason)
        blockers = (
            QtCore.QSignalBlocker(self.quality_check),
            QtCore.QSignalBlocker(self.highlight_check),
            QtCore.QSignalBlocker(self.filter_combo),
            QtCore.QSignalBlocker(self.isolate_check),
        )
        self.quality_check.setChecked(view_model.quality_coloring_visible)
        self.highlight_check.setChecked(view_model.highlight_visible)
        filter_labels = {
            "clear": "Clear filter",
            "hide_bad": "Hide bad",
            "isolate_bad": "Isolate bad",
        }
        self.filter_combo.setCurrentText(filter_labels.get(view_model.filter_mode, "Clear filter"))
        self.isolate_check.setChecked(view_model.isolated)
        del blockers
        bad_actions_enabled = bool(view_model.overlay_actions_enabled and view_model.bad_cell_keys)
        self.select_bad_button.setEnabled(bad_actions_enabled)
        self.create_named_selection_button.setEnabled(bad_actions_enabled)
        self.export_json_button.setEnabled(view_model.analysis_available)
        self.export_csv_button.setEnabled(view_model.analysis_available)
        self.clear_button.setEnabled(view_model.analysis_available)
        self._refresh_table()

    def set_running(self, running: bool) -> None:
        self.analyze_button.setEnabled(not running)
        if running:
            self.analysis_state_label.setText("Analysis running…")
            self.status_label.setText(
                "Computing Scaled Jacobian in a background worker for the exact mesh fingerprint."
            )

    def set_status(self, message: str) -> None:
        self.status_label.setText(str(message or ""))

    def _set_actions(self, enabled: bool, reason: str) -> None:
        for control in (
            self.quality_check,
            self.highlight_check,
            self.filter_combo,
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
        if not isfinite(threshold) or not -1.0 <= threshold <= 1.0:
            self.status_label.setText("Bad-cell threshold must be finite and within [-1, 1].")
            return
        self.thresholdChanged.emit(threshold)

    def _emit_range(self) -> None:
        mode = self.range_mode.currentText().lower()
        if mode == "auto":
            self.rangeChanged.emit("auto", None)
            return
        try:
            minimum = float(self.range_min_edit.text().strip())
            maximum = float(self.range_max_edit.text().strip())
        except ValueError:
            minimum = maximum = float("nan")
        if not isfinite(minimum) or not isfinite(maximum) or minimum >= maximum:
            self.status_label.setText("Manual range requires finite minimum < maximum.")
            return
        self.rangeChanged.emit("manual", (minimum, maximum))

    def _update_range_apply_enabled(self, *_args: object) -> None:
        enabled = bool(self._view_model is not None and self._view_model.analysis_available)
        if enabled and self.range_mode.currentText().casefold() == "manual":
            try:
                minimum = float(self.range_min_edit.text().strip())
                maximum = float(self.range_max_edit.text().strip())
            except ValueError:
                enabled = False
            else:
                enabled = isfinite(minimum) and isfinite(maximum) and minimum < maximum
        self.apply_range_button.setEnabled(enabled)
        self.apply_range_button.setToolTip(
            "" if enabled else "Manual range requires finite minimum < maximum."
        )

    def _emit_filter_mode(self, label: str) -> None:
        modes = {
            "Clear filter": "clear",
            "Hide bad": "hide_bad",
            "Isolate bad": "isolate_bad",
        }
        self.filterModeChanged.emit(modes.get(label, "clear"))

    def _refresh_table(self) -> None:
        view_model = self._view_model
        rows = () if view_model is None else view_model.rows
        selected_filter = self.table_filter.currentText()
        if selected_filter == "Bad":
            rows = tuple(row for row in rows if row.is_bad)
        elif selected_filter == "Invalid / uncovered":
            rows = tuple(row for row in rows if row.category in {"invalid", "uncovered"})
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = (
                row.stable_cell_id,
                row.cell_type,
                f"{row.block_ordinal} / {row.cell_ordinal}",
                row.status,
                row.category,
                "—" if row.metric_value is None else f"{row.metric_value:.8g}",
                row.reason,
            )
            for column, value in enumerate(values):
                self.table.setItem(row_index, column, QtWidgets.QTableWidgetItem(value))


def _range_text(
    minimum: float | None,
    maximum: float | None,
    mean: float | None,
    median: float | None,
) -> str:
    if minimum is None or maximum is None or mean is None or median is None:
        return "unavailable"
    return f"{minimum:.8g} / {maximum:.8g} / {mean:.8g} / {median:.8g}"


def _analysis_state_text(view_model: MeshDiagnosticsViewModel) -> str:
    if not view_model.analysis_available:
        return "Not evaluated."
    labels = {
        "idle": "Not evaluated",
        "running": "Running",
        "ready": "Invalid" if view_model.invalid_count else "Complete",
        "partial_coverage": "Partial",
        "stale": "Stale",
        "unavailable_optional_dependency": "Unavailable",
        "failed": "Failed",
        "cancelled": "Cancelled",
    }
    label = labels.get(view_model.status, view_model.status.replace("_", " ").title())
    return (
        f"{label}: {view_model.covered_count}/{view_model.cell_count} cells covered; "
        f"{view_model.bad_count} bad, {view_model.invalid_count} invalid, "
        f"{view_model.unsupported_count} uncovered."
    )


__all__ = ["MeshDiagnosticsPanel"]
