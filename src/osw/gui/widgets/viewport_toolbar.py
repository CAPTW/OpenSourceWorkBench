"""Toolbar for the central mock simulation viewport."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

VIEWPORT_TOOL_ACTIONS = ("Select", "Orbit", "Pan", "Zoom", "Fit", "Section", "Camera")
VIEWPORT_ACTION_OBJECT_NAMES = {
    "Select": "oswViewportActionSelect",
    "Orbit": "oswViewportActionOrbit",
    "Pan": "oswViewportActionPan",
    "Zoom": "oswViewportActionZoom",
    "Fit": "oswViewportActionFit",
    "Section": "oswViewportActionSection",
    "Camera": "oswViewportActionCamera",
}
TOOL_GLYPHS = {
    "Select": "↖",
    "Orbit": "⟳",
    "Pan": "✥",
    "Zoom": "⌕",
    "Fit": "⛶",
    "Section": "▣",
    "Camera": "▤",
}

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class ViewportToolbar(_BaseWidget):
    """Compact, theme-aware viewport toolbar."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswViewportToolbar")
        self.tool_buttons: dict[str, object] = {}

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(6)
        label = QtWidgets.QLabel("View:", self)
        label.setObjectName("oswViewportViewLabel")
        self.view_selector = QtWidgets.QComboBox(self)
        self.view_selector.setObjectName("oswViewportViewSelector")
        self.view_selector.addItems(["von Mises Stress", "Temperature", "Velocity Magnitude"])
        layout.addWidget(label)
        layout.addWidget(self.view_selector, 0)
        for action in VIEWPORT_TOOL_ACTIONS:
            button = QtWidgets.QToolButton(self)
            button.setObjectName(VIEWPORT_ACTION_OBJECT_NAMES[action])
            button.setText(TOOL_GLYPHS[action])
            button.setToolTip(action)
            button.setAutoRaise(False)
            self.tool_buttons[action] = button
            layout.addWidget(button)
        layout.addStretch(1)
        self.set_theme_tokens(DARK_TOKENS)

    def action_labels(self) -> list[str]:
        return list(VIEWPORT_TOOL_ACTIONS)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            "QWidget#oswViewportToolbar {"
            f"background-color: {tokens.bg_header};"
            f"border-bottom: 1px solid {tokens.border};"
            "}"
            "QLabel#oswViewportViewLabel {"
            f"color: {tokens.text_secondary};"
            "font-weight: 600;"
            "}"
            "QComboBox#oswViewportViewSelector {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "padding: 3px 8px;"
            "min-width: 150px;"
            "}"
            "QToolButton {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "padding: 3px 7px;"
            "font-weight: 700;"
            "}"
            "QToolButton:hover {"
            f"background-color: {tokens.primary_hover};"
            f"border-color: {tokens.border_strong};"
            "}"
        )
