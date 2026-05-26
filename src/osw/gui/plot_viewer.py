"""Plot viewer for FigureDataset previews."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.scripts.mscript.figure_dataset import FigureDataset, FigureRecord

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtGui = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class PlotViewer(_BaseWidget):
    """PySide6 panel that lists captured FigureDataset records."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswPlotViewer")
        self._tokens = DARK_TOKENS
        self._dataset: FigureDataset | None = None
        self.summary_label = QtWidgets.QLabel("No figures loaded.", self)
        self.summary_label.setObjectName("plotViewerSummary")
        self.summary_label.setWordWrap(True)
        self.figure_list = QtWidgets.QListWidget(self)
        self.figure_list.setObjectName("oswFigureList")
        self.image_view = QtWidgets.QLabel("No figure selected.", self)
        self.image_view.setObjectName("oswFigureImageView")
        self.image_view.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_view.setMinimumSize(260, 180)
        self.image_view.setWordWrap(True)
        self.metadata_panel = QtWidgets.QPlainTextEdit(self)
        self.metadata_panel.setObjectName("oswFigureMetadataPanel")
        self.metadata_panel.setReadOnly(True)
        self.workspace_table = QtWidgets.QTableWidget(self)
        self.workspace_table.setObjectName("oswWorkspaceVariablesTable")
        self.workspace_table.setColumnCount(5)
        self.workspace_table.setHorizontalHeaderLabels(
            ["Name", "Type", "Shape", "DType", "Source"]
        )
        self.export_button = QtWidgets.QPushButton("Export FigureDataset", self)
        self.export_button.setObjectName("oswExportFigureDatasetButton")
        self.export_button.setEnabled(False)

        left = QtWidgets.QVBoxLayout()
        left.addWidget(self.summary_label)
        left.addWidget(self.figure_list, 1)
        left.addWidget(self.export_button)
        right = QtWidgets.QVBoxLayout()
        right.addWidget(self.image_view, 2)
        right.addWidget(self.metadata_panel, 1)
        right.addWidget(self.workspace_table, 1)
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addLayout(left, 1)
        layout.addLayout(right, 2)

        self.figure_list.currentRowChanged.connect(self._on_current_row_changed)
        self.set_theme_tokens(self._tokens)

    def load_figure_dataset(self, dataset: FigureDataset) -> None:
        self.set_figure_dataset(dataset)

    def set_figure_dataset(self, dataset: FigureDataset) -> None:
        self._dataset = dataset
        self.figure_list.clear()
        for row in figure_display_rows(dataset):
            self.figure_list.addItem(row)
        self.summary_label.setText(
            f"Dataset: {dataset.dataset_id}\n"
            f"Figures: {len(dataset.figures)}\n"
            f"Workspace variables: {len(dataset.workspace_variables)}"
        )
        self.export_button.setEnabled(True)
        self._populate_workspace_table(dataset)
        if dataset.figures:
            self.figure_list.setCurrentRow(0)
        else:
            self.image_view.setText("No figure artifacts in dataset.")
            self.metadata_panel.setPlainText("")

    def current_dataset(self) -> FigureDataset | None:
        return self._dataset

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswPlotViewer {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QListWidget, QPlainTextEdit, QTableWidget, QLabel#oswFigureImageView {"
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

    def _on_current_row_changed(self, row: int) -> None:
        dataset = self._dataset
        if dataset is None or row < 0 or row >= len(dataset.figures):
            return
        self._show_record(dataset.figures[row])

    def _show_record(self, record: FigureRecord) -> None:
        self.metadata_panel.setPlainText(_record_metadata_text(record))
        image_path = record.image_path or record.vector_path or record.thumbnail_path
        if image_path is None:
            self.image_view.setPixmap(QtGui.QPixmap())
            self.image_view.setText(f"No direct image preview for {record.figure_id}.")
            return
        if image_path.suffix.lower() == ".svg":
            self.image_view.setPixmap(QtGui.QPixmap())
            self.image_view.setText(f"SVG artifact: {image_path}")
            return
        pixmap = QtGui.QPixmap(str(image_path))
        if pixmap.isNull():
            self.image_view.setPixmap(QtGui.QPixmap())
            self.image_view.setText(f"Image preview unavailable: {image_path}")
            return
        self.image_view.setText("")
        self.image_view.setPixmap(
            pixmap.scaled(
                self.image_view.size(),
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
        )

    def _populate_workspace_table(self, dataset: FigureDataset) -> None:
        self.workspace_table.setRowCount(len(dataset.workspace_variables))
        for row, variable in enumerate(dataset.workspace_variables):
            values = (
                variable.name,
                variable.type_name,
                "x".join(str(item) for item in variable.shape),
                variable.dtype,
                variable.source,
            )
            for column, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                self.workspace_table.setItem(row, column, item)
        self.workspace_table.resizeColumnsToContents()


def build_plot_viewer(parent: object | None = None) -> object:
    return PlotViewer(parent)


def figure_display_rows(dataset: FigureDataset) -> tuple[str, ...]:
    return tuple(
        f"{record.figure_id} | {record.title} | {record.image_format}"
        for record in dataset.figures
    )


def _record_metadata_text(record: FigureRecord) -> str:
    path = record.primary_path
    axes = ", ".join(axis.display_label() for axis in record.axes) or "None"
    return "\n".join(
        (
            f"ID: {record.figure_id}",
            f"Title: {record.title}",
            f"Format: {record.image_format}",
            f"Path: {Path(path) if path is not None else 'N/A'}",
            f"Source script: {record.source_script or 'N/A'}",
            f"Run ID: {record.source_run_id or 'N/A'}",
            f"Axes: {axes}",
        )
    )
