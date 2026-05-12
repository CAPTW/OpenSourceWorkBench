"""Preview-only script panel for OSW GUI integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from osw.scripts.mscript.importer import import_mscript_preview
from osw.scripts.mscript.script_model import MScriptPreview

from .qt_compat import PySide6UnavailableError, pyside6_missing_message

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class ScriptPanel(_BaseWidget):
    """Display `.m` preview metadata without executing script code."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("scriptPanel")
        self.summary_label = QtWidgets.QLabel("No script loaded.", self)
        self.summary_label.setObjectName("scriptPreviewSummary")
        self.summary_label.setWordWrap(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Script Preview"))
        layout.addWidget(self.summary_label)
        layout.addStretch(1)

    def load_script_preview(self, path: str | Path) -> MScriptPreview:
        preview = import_mscript_preview(path)
        self.summary_label.setText(_preview_summary(preview))
        return preview


def build_script_panel(parent: object | None = None) -> object:
    return ScriptPanel(parent)


def _preview_summary(preview: MScriptPreview) -> str:
    warning_count = len(preview.safety.findings)
    return (
        f"Name: {preview.name}\n"
        f"Kind: {preview.kind.value}\n"
        f"Lines: {preview.line_count}\n"
        f"Executable lines: {preview.executable_line_count}\n"
        f"Safety findings: {warning_count}"
    )
