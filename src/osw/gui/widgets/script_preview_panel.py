"""Theme-aware read-only MATLAB/Octave script preview panel."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.scripts.mscript.script_model import ScriptPreview

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class ScriptPreviewPanel(_BaseWidget):
    """Read-only script metadata, safety finding, and plot hint preview."""

    if QtCore is not None:
        importRequested = QtCore.Signal()
        cancelRequested = QtCore.Signal()

    def __init__(
        self,
        preview: ScriptPreview | None = None,
        parent: object | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswScriptPreviewPanel")
        self._tokens = DARK_TOKENS
        self._preview: ScriptPreview | None = None
        self._build_layout()
        self.set_theme_tokens(self._tokens)
        if preview is not None:
            self.set_preview(preview)

    def set_preview(self, preview: ScriptPreview) -> None:
        self._preview = preview
        self.source_path_label.setText(preview.source_path)
        self.kind_label.setText(preview.kind.value)
        signature = preview.function_signature.raw_signature if preview.function_signature else ""
        self.signature_label.setText(signature or "No function signature")
        self.help_text.setPlainText(preview.help_text or preview.first_comment_block)
        self.code_text.setPlainText(_code_preview_text(preview))
        self._populate_safety_table(preview)
        self._populate_plot_table(preview)

    def current_preview(self) -> ScriptPreview | None:
        return self._preview

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswScriptPreviewPanel {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
            "QLabel[oswScriptMeta='true'] {"
            f"color: {tokens.text_secondary};"
            "font-weight: 600;"
            "}"
            "QPlainTextEdit, QTableWidget {"
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
        meta_grid.setHorizontalSpacing(8)
        meta_grid.setVerticalSpacing(5)
        self.source_path_label = QtWidgets.QLabel("", self)
        self.source_path_label.setObjectName("oswScriptPreviewSourcePath")
        self.kind_label = QtWidgets.QLabel("", self)
        self.kind_label.setObjectName("oswScriptPreviewKindLabel")
        self.signature_label = QtWidgets.QLabel("", self)
        self.signature_label.setObjectName("oswScriptPreviewSignatureLabel")
        for row, (label, widget) in enumerate(
            (
                ("Source", self.source_path_label),
                ("Kind", self.kind_label),
                ("Signature", self.signature_label),
            )
        ):
            meta = QtWidgets.QLabel(label, self)
            meta.setProperty("oswScriptMeta", True)
            meta_grid.addWidget(meta, row, 0)
            meta_grid.addWidget(widget, row, 1)
        layout.addLayout(meta_grid)

        self.help_text = QtWidgets.QPlainTextEdit(self)
        self.help_text.setObjectName("oswScriptPreviewHelpText")
        self.help_text.setReadOnly(True)
        self.help_text.setMaximumHeight(96)
        layout.addWidget(self.help_text)

        self.code_text = QtWidgets.QPlainTextEdit(self)
        self.code_text.setObjectName("oswScriptPreviewCodeText")
        self.code_text.setReadOnly(True)
        self.code_text.setMinimumHeight(140)
        layout.addWidget(self.code_text, 1)

        tables = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        self.safety_table = QtWidgets.QTableWidget(tables)
        self.safety_table.setObjectName("oswScriptSafetyFindingsTable")
        self.safety_table.setColumnCount(4)
        self.safety_table.setHorizontalHeaderLabels(["Severity", "Line", "Token", "Message"])
        self.plot_table = QtWidgets.QTableWidget(tables)
        self.plot_table.setObjectName("oswScriptPlotHintsTable")
        self.plot_table.setColumnCount(3)
        self.plot_table.setHorizontalHeaderLabels(["Command", "Line", "Context"])
        tables.addWidget(self.safety_table)
        tables.addWidget(self.plot_table)
        tables.setSizes([540, 360])
        layout.addWidget(tables)

        button_row = QtWidgets.QHBoxLayout()
        self.import_button = QtWidgets.QPushButton("Import Preview", self)
        self.import_button.setObjectName("oswScriptPreviewImportButton")
        self.cancel_button = QtWidgets.QPushButton("Cancel", self)
        self.cancel_button.setObjectName("oswScriptPreviewCancelButton")
        button_row.addStretch(1)
        button_row.addWidget(self.import_button)
        button_row.addWidget(self.cancel_button)
        layout.addLayout(button_row)
        self.import_button.clicked.connect(self.importRequested.emit)
        self.cancel_button.clicked.connect(self.cancelRequested.emit)

    def _populate_safety_table(self, preview: ScriptPreview) -> None:
        self.safety_table.setRowCount(len(preview.safety_findings))
        for row, finding in enumerate(preview.safety_findings):
            self.safety_table.setItem(row, 0, _readonly_item(finding.severity))
            self.safety_table.setItem(row, 1, _readonly_item(finding.line_no or ""))
            self.safety_table.setItem(row, 2, _readonly_item(finding.token))
            self.safety_table.setItem(row, 3, _readonly_item(finding.message))
        self.safety_table.resizeColumnsToContents()

    def _populate_plot_table(self, preview: ScriptPreview) -> None:
        self.plot_table.setRowCount(len(preview.plot_hints))
        for row, hint in enumerate(preview.plot_hints):
            self.plot_table.setItem(row, 0, _readonly_item(hint.command))
            self.plot_table.setItem(row, 1, _readonly_item(hint.line_no))
            self.plot_table.setItem(row, 2, _readonly_item(hint.context))
        self.plot_table.resizeColumnsToContents()


def _readonly_item(value: object) -> object:
    item = QtWidgets.QTableWidgetItem(str(value))
    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
    return item


def _code_preview_text(preview: ScriptPreview) -> str:
    excerpt = preview.metadata.get("source_excerpt")
    if isinstance(excerpt, str) and excerpt:
        return excerpt
    lines = [
        f"% Preview only: {preview.name}",
        f"% Lines: {preview.line_count}",
        f"% Safety: {preview.safety_summary()}",
    ]
    if preview.help_text:
        lines.append("% Help text extracted above.")
    return "\n".join(lines)
