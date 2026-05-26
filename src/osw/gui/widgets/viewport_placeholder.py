"""Central viewport panel for the OSW visual shell."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.mock_simulation_viewport import MockSimulationViewport
from osw.gui.widgets.viewport_toolbar import ViewportToolbar

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QFrame if QtWidgets is not None else object


class CentralViewportPanel(_BaseWidget):
    """Composite viewport toolbar plus mock simulation viewport."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswCentralViewportPanel")
        self.setMinimumSize(560, 360)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.toolbar = ViewportToolbar(self)
        self.viewport = MockSimulationViewport(self)
        layout.addWidget(self.toolbar, 0)
        layout.addWidget(self.viewport, 1)
        self.set_theme_tokens(DARK_TOKENS)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            "QFrame#oswCentralViewportPanel {"
            f"background-color: {tokens.bg_viewport};"
            f"border: 1px solid {tokens.border};"
            "}"
        )
        self.toolbar.set_theme_tokens(tokens)
        self.viewport.set_theme_tokens(tokens)


ViewportPlaceholder = CentralViewportPanel
