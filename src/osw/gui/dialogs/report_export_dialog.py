"""Theme-aware report export dialog."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class ReportExportDialog(_BaseDialog):
    """Select a local report export path and lightweight format."""

    if QtCore is not None:
        reportExportRequested = QtCore.Signal(str, str)

    def __init__(
        self,
        parent: object | None = None,
        *,
        default_path: str | Path = "artifacts/report/report.html",
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswReportExportDialog")
        self.setWindowTitle("Export Report")
        self.resize(560, 160)
        self._tokens = theme_tokens or DARK_TOKENS

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        self.path_edit = QtWidgets.QLineEdit(str(default_path), self)
        self.path_edit.setObjectName("oswReportExportPathEdit")
        self.format_combo = QtWidgets.QComboBox(self)
        self.format_combo.setObjectName("oswReportExportFormatCombo")
        self.format_combo.addItems(["html", "markdown", "json_summary"])
        form.addRow("Path", self.path_edit)
        form.addRow("Format", self.format_combo)

        buttons = QtWidgets.QHBoxLayout()
        buttons.addStretch(1)
        self.export_button = QtWidgets.QPushButton("Export", self)
        self.export_button.setObjectName("oswReportExportConfirmButton")
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.setObjectName("oswReportExportCancelButton")
        buttons.addWidget(self.export_button)
        buttons.addWidget(self.cancel_button)

        layout.addLayout(form)
        layout.addLayout(buttons)
        self.export_button.clicked.connect(self._emit_export)
        self.cancel_button.clicked.connect(self.reject)
        self.set_theme_tokens(self._tokens)

    def selected_path(self) -> str:
        return self.path_edit.text()

    def selected_format(self) -> str:
        return self.format_combo.currentText()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QDialog#oswReportExportDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLineEdit#oswReportExportPathEdit, QComboBox#oswReportExportFormatCombo {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "padding: 4px;"
            "}"
        )

    def _emit_export(self) -> None:
        self.reportExportRequested.emit(self.selected_path(), self.selected_format())
        self.accept()
