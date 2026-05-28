"""Theme-aware MATLAB MAT data preview dialog."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.mat_preview_panel import MatPreviewPanel
from osw.scripts.mscript.mat_model import MatReadResult

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class MatPreviewDialog(_BaseDialog):
    """Read-only preview dialog for untrusted MATLAB MAT data files."""

    if QtCore is not None:
        matPreviewAccepted = QtCore.Signal(object)

    def __init__(
        self,
        result: MatReadResult | None = None,
        parent: object | None = None,
        *,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswMatPreviewDialog")
        self.setWindowTitle("MATLAB MAT Data Preview")
        self.resize(980, 660)
        self._tokens = theme_tokens or DARK_TOKENS

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.preview_panel = MatPreviewPanel(result=result, parent=self)
        layout.addWidget(self.preview_panel)
        self.preview_panel.importRequested.connect(self._accept_preview)
        self.preview_panel.cancelRequested.connect(self.reject)
        self.set_theme_tokens(self._tokens)

    def current_result(self) -> MatReadResult | None:
        return self.preview_panel.current_result()

    def set_result(self, result: MatReadResult) -> None:
        self.preview_panel.set_result(result)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.preview_panel.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QDialog#oswMatPreviewDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
        )

    def _accept_preview(self, result: object) -> None:
        if result is not None:
            self.matPreviewAccepted.emit(result)
        self.accept()
