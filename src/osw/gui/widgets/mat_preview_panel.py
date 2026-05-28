"""Theme-aware MATLAB MAT data preview panel."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.scripts.mscript.mat_model import MatReadResult

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class MatPreviewPanel(_BaseWidget):
    """Read-only MAT variable summary and table preview surface."""

    if QtCore is not None:
        importRequested = QtCore.Signal(object)
        cancelRequested = QtCore.Signal()

    def __init__(
        self,
        result: MatReadResult | None = None,
        parent: object | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswMatPreviewPanel")
        self._tokens = DARK_TOKENS
        self._result: MatReadResult | None = None
        self._build_layout()
        self.set_theme_tokens(self._tokens)
        if result is not None:
            self.set_result(result)

    def set_result(self, result: MatReadResult) -> None:
        self._result = result
        self.source_path_label.setText(result.source_path)
        self.version_label.setText(result.summary.version)
        self._populate_variables_table(result)
        self._populate_diagnostics(result)
        if result.variables:
            self.variables_table.selectRow(0)
            self._populate_preview_table(0)
        else:
            self.variable_preview_table.setRowCount(0)

    def current_result(self) -> MatReadResult | None:
        return self._result

    def selected_variable_name(self) -> str:
        row = self.variables_table.currentRow()
        if row < 0:
            return ""
        item = self.variables_table.item(row, 0)
        return item.text() if item is not None else ""

    def export_selected_csv(self, output_path: str | Path | None = None) -> object | None:
        result = self._result
        variable_name = self.selected_variable_name()
        if result is None or not variable_name:
            return None
        if output_path is None:
            selected, _filter = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Export MAT Variable CSV",
                f"{variable_name}.csv",
                "CSV files (*.csv)",
            )
            if not selected:
                return None
            output_path = selected
        from osw.scripts.mscript.mat_reader import export_variable_to_csv

        export_result = export_variable_to_csv(result.source_path, variable_name, output_path)
        self._append_diagnostics(export_result.diagnostics)
        return export_result

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswMatPreviewPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel[oswMatMeta='true'] {"
            f"color: {tokens.text_secondary};"
            "font-weight: 600;"
            "}"
            "QTableWidget, QListWidget {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "}"
            "QPushButton {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "padding: 5px 8px;"
            "border-radius: 3px;"
            "}"
        )

    def _build_layout(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        meta_grid = QtWidgets.QGridLayout()
        self.source_path_label = QtWidgets.QLabel("", self)
        self.source_path_label.setObjectName("oswMatPreviewSourcePath")
        self.version_label = QtWidgets.QLabel("", self)
        self.version_label.setObjectName("oswMatPreviewVersionLabel")
        for row, (label, widget) in enumerate(
            (("Source", self.source_path_label), ("Version", self.version_label))
        ):
            meta = QtWidgets.QLabel(label, self)
            meta.setProperty("oswMatMeta", True)
            meta_grid.addWidget(meta, row, 0)
            meta_grid.addWidget(widget, row, 1)
        layout.addLayout(meta_grid)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        self.variables_table = QtWidgets.QTableWidget(splitter)
        self.variables_table.setObjectName("oswMatVariablesTable")
        self.variables_table.setColumnCount(5)
        self.variables_table.setHorizontalHeaderLabels(
            ["Name", "Kind", "Shape", "Dtype", "Preview"]
        )
        self.variables_table.currentCellChanged.connect(
            lambda row, _col, _prev_row, _prev_col: self._populate_preview_table(row)
        )
        self.variable_preview_table = QtWidgets.QTableWidget(splitter)
        self.variable_preview_table.setObjectName("oswMatVariablePreviewTable")
        splitter.addWidget(self.variables_table)
        splitter.addWidget(self.variable_preview_table)
        splitter.setSizes([540, 420])
        layout.addWidget(splitter, 1)

        self.diagnostics_list = QtWidgets.QListWidget(self)
        self.diagnostics_list.setObjectName("oswMatDiagnosticsList")
        self.diagnostics_list.setMaximumHeight(110)
        layout.addWidget(self.diagnostics_list)

        button_row = QtWidgets.QHBoxLayout()
        self.export_csv_button = QtWidgets.QPushButton("Export CSV", self)
        self.export_csv_button.setObjectName("oswMatExportCsvButton")
        self.import_button = QtWidgets.QPushButton("Import Preview", self)
        self.import_button.setObjectName("oswMatImportButton")
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.setObjectName("oswMatCancelButton")
        button_row.addStretch(1)
        button_row.addWidget(self.export_csv_button)
        button_row.addWidget(self.import_button)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)
        self.export_csv_button.clicked.connect(lambda: self.export_selected_csv())
        self.import_button.clicked.connect(lambda: self.importRequested.emit(self._result))
        self.cancel_button.clicked.connect(self.cancelRequested.emit)

    def _populate_variables_table(self, result: MatReadResult) -> None:
        variables = result.variables
        self.variables_table.setRowCount(len(variables))
        for row, variable in enumerate(variables):
            values = (
                variable.name,
                variable.kind,
                variable.display_shape,
                variable.dtype,
                variable.preview,
            )
            for column, value in enumerate(values):
                self.variables_table.setItem(row, column, _readonly_item(value))
        self.variables_table.resizeColumnsToContents()

    def _populate_preview_table(self, row: int) -> None:
        result = self._result
        if result is None or row < 0 or row >= len(result.variables):
            self.variable_preview_table.setRowCount(0)
            return
        variable = result.variables[row]
        try:
            preview = result.table_preview(variable.name)
        except Exception:
            preview = None
        if preview is None:
            self.variable_preview_table.setColumnCount(1)
            self.variable_preview_table.setHorizontalHeaderLabels(["Preview"])
            self.variable_preview_table.setRowCount(1)
            self.variable_preview_table.setItem(0, 0, _readonly_item(variable.preview))
            return
        self.variable_preview_table.setColumnCount(len(preview.columns))
        self.variable_preview_table.setHorizontalHeaderLabels(list(preview.columns))
        self.variable_preview_table.setRowCount(len(preview.rows))
        for row_index, row_values in enumerate(preview.rows):
            for column, value in enumerate(row_values):
                self.variable_preview_table.setItem(row_index, column, _readonly_item(value))
        self.variable_preview_table.resizeColumnsToContents()

    def _populate_diagnostics(self, result: MatReadResult) -> None:
        self.diagnostics_list.clear()
        self._append_diagnostics(result.diagnostics)

    def _append_diagnostics(self, diagnostics: object) -> None:
        messages = getattr(diagnostics, "messages", ())
        for message in messages:
            severity = getattr(getattr(message, "severity", ""), "value", "")
            self.diagnostics_list.addItem(
                f"{severity.upper()} {getattr(message, 'code', '')}: "
                f"{getattr(message, 'message', '')}"
            )


def _readonly_item(value: object) -> object:
    item = QtWidgets.QTableWidgetItem(str(value))
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
    return item
