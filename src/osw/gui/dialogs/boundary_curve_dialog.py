"""Theme-aware BoundaryCurve preview dialog."""

from __future__ import annotations

from typing import Any

from osw.core.boundary_curve import BoundaryCurve
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.boundary_curve_panel import BoundaryCurvePanel

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseDialog: Any = QtWidgets.QDialog if QtWidgets is not None else object


class BoundaryCurveDialog(_BaseDialog):
    """Preview a BoundaryCurve before attaching it to a project."""

    if QtCore is not None:
        boundaryCurveAccepted = QtCore.Signal(object)

    def __init__(
        self,
        curve: BoundaryCurve | None = None,
        parent: object | None = None,
        *,
        theme_tokens: ThemeTokens | None = None,
    ) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswBoundaryCurveDialog")
        self.setWindowTitle("Boundary Curve Preview")
        self.resize(820, 620)
        self._tokens = theme_tokens or DARK_TOKENS

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.preview_panel = BoundaryCurvePanel(curve=curve, parent=self)
        layout.addWidget(self.preview_panel)
        self.preview_panel.createRequested.connect(self._accept_curve)
        self.preview_panel.cancelRequested.connect(self.reject)
        self.set_theme_tokens(self._tokens)

    def current_curve(self) -> BoundaryCurve | None:
        return self.preview_panel.current_curve()

    def set_curve(self, curve: BoundaryCurve) -> None:
        self.preview_panel.set_curve(curve)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.preview_panel.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QDialog#oswBoundaryCurveDialog {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_primary};"
            "}"
        )

    def _accept_curve(self, curve: object) -> None:
        if curve is not None:
            self.boundaryCurveAccepted.emit(curve)
        self.accept()
