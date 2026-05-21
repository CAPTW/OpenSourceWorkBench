"""Table viewer for structured OSW metadata and result previews."""

from __future__ import annotations

from typing import Any

from osw.post.table_model import TablePreview

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class TableViewer(_BaseWidget):
    """Small table viewer used by import previews, diagnostics, and report data."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("tableViewer")
        self.summary_label = QtWidgets.QLabel("No table data loaded.", self)
        self.summary_label.setObjectName("tableViewerSummary")
        self.table = QtWidgets.QTableWidget(self)
        self.table.setObjectName("tableViewerGrid")

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.table)

    def load_table_preview(self, preview: TablePreview) -> None:
        self.table.clear()
        self.table.setColumnCount(len(preview.columns))
        self.table.setRowCount(len(preview.rows))
        self.table.setHorizontalHeaderLabels(list(preview.columns))
        for row_index, row in enumerate(preview.rows):
            for column_index, value in enumerate(row):
                self.table.setItem(row_index, column_index, QtWidgets.QTableWidgetItem(value))
        title = preview.title or "Table preview"
        self.summary_label.setText(
            f"{title}: {len(preview.rows)} row(s), {len(preview.columns)} column(s)"
        )
        self.table.resizeColumnsToContents()


def build_table_viewer(parent: object | None = None) -> object:
    return TableViewer(parent)
