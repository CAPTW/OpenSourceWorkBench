"""Theme-aware MATLAB/Octave script preview dialog."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.script_preview_panel import ScriptPreviewPanel
from osw.scripts.mscript.script_model import ScriptPreview

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class ScriptPreviewDialog(_BaseDialog):
    """Read-only preview dialog for untrusted MATLAB/Octave source files."""

    if QtCore is not None:
        previewAccepted = QtCore.Signal(object)

    def __init__(
        self,
        preview: ScriptPreview | None = None,
        parent: object | None = None,
        *,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswScriptPreviewDialog")
        self.setWindowTitle("MATLAB/Octave Script Preview")
        self.resize(980, 720)
        self._tokens = theme_tokens or DARK_TOKENS

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.preview_panel = ScriptPreviewPanel(preview=preview, parent=self)
        layout.addWidget(self.preview_panel)

        self.preview_panel.importRequested.connect(self._accept_preview)
        self.preview_panel.cancelRequested.connect(self.reject)
        self.set_theme_tokens(self._tokens)

    def current_preview(self) -> ScriptPreview | None:
        return self.preview_panel.current_preview()

    def set_preview(self, preview: ScriptPreview) -> None:
        self.preview_panel.set_preview(preview)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.preview_panel.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QDialog#oswScriptPreviewDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
        )

    def _accept_preview(self) -> None:
        preview = self.current_preview()
        if preview is not None:
            self.previewAccepted.emit(preview)
        self.accept()
