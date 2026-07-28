"""Toolbar for the central interactive-or-fallback 3D workspace viewport."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

VIEWPORT_TOOL_ACTIONS = ("Select", "Orbit", "Pan", "Zoom", "Fit", "Section", "Camera")
CAMERA_PRESETS = (
    "Isometric",
    "Front",
    "Back",
    "Left",
    "Right",
    "Top",
    "Bottom",
)
REPRESENTATION_MODES = (
    ("Surface", "surface"),
    ("Wireframe", "wireframe"),
    ("Surface + Edges", "surface_with_edges"),
)
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

    if QtCore is not None:
        commandRequested = QtCore.Signal(str)
        cameraPresetRequested = QtCore.Signal(str)
        representationRequested = QtCore.Signal(str)
        axesToggled = QtCore.Signal(bool)
        actorVisibilityRequested = QtCore.Signal(str, bool)
        actorIsolationRequested = QtCore.Signal(str)
        showAllActorsRequested = QtCore.Signal()
        clippingToggled = QtCore.Signal(bool)
        clippingUpdated = QtCore.Signal(str, float)

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
            if action == "Section":
                button.setCheckable(True)
            self.tool_buttons[action] = button
            layout.addWidget(button)

        self.camera_selector = QtWidgets.QComboBox(self)
        self.camera_selector.setObjectName("oswViewportCameraPreset")
        self.camera_selector.addItems(CAMERA_PRESETS)
        self.camera_selector.setToolTip("Camera preset")
        layout.addWidget(self.camera_selector)

        self.representation_selector = QtWidgets.QComboBox(self)
        self.representation_selector.setObjectName("oswViewportRepresentation")
        for label_text, value in REPRESENTATION_MODES:
            self.representation_selector.addItem(label_text, value)
        layout.addWidget(self.representation_selector)

        self.axes_button = QtWidgets.QToolButton(self)
        self.axes_button.setObjectName("oswViewportAxesToggle")
        self.axes_button.setText("Axes")
        self.axes_button.setCheckable(True)
        self.axes_button.setChecked(True)
        layout.addWidget(self.axes_button)

        self.actor_selector = QtWidgets.QComboBox(self)
        self.actor_selector.setObjectName("oswViewportActorSelector")
        self.actor_selector.addItem("Base mesh", "base_mesh")
        self.actor_selector.addItem("Wireframe", "wireframe")
        layout.addWidget(self.actor_selector)

        self.actor_visibility_button = QtWidgets.QToolButton(self)
        self.actor_visibility_button.setObjectName("oswViewportActorVisibility")
        self.actor_visibility_button.setText("Visible")
        self.actor_visibility_button.setCheckable(True)
        self.actor_visibility_button.setChecked(True)
        layout.addWidget(self.actor_visibility_button)

        self.isolate_button = QtWidgets.QToolButton(self)
        self.isolate_button.setObjectName("oswViewportActorIsolate")
        self.isolate_button.setText("Isolate")
        layout.addWidget(self.isolate_button)

        self.show_all_button = QtWidgets.QToolButton(self)
        self.show_all_button.setObjectName("oswViewportActorShowAll")
        self.show_all_button.setText("Show all")
        layout.addWidget(self.show_all_button)

        self.clip_axis_selector = QtWidgets.QComboBox(self)
        self.clip_axis_selector.setObjectName("oswViewportClipAxis")
        self.clip_axis_selector.addItems(["X", "Y", "Z"])
        layout.addWidget(self.clip_axis_selector)

        self.clip_origin_input = QtWidgets.QDoubleSpinBox(self)
        self.clip_origin_input.setObjectName("oswViewportClipOrigin")
        self.clip_origin_input.setRange(-1.0e12, 1.0e12)
        self.clip_origin_input.setDecimals(6)
        self.clip_origin_input.setSingleStep(0.1)
        layout.addWidget(self.clip_origin_input)
        layout.addStretch(1)
        self._connect_controls()
        self.set_theme_tokens(DARK_TOKENS)

    def action_labels(self) -> list[str]:
        return list(VIEWPORT_TOOL_ACTIONS)

    def interactive_control_widgets(self) -> tuple[object, ...]:
        return (
            *tuple(
                self.tool_buttons[action]
                for action in ("Orbit", "Pan", "Zoom", "Fit", "Section", "Camera")
            ),
            self.camera_selector,
            self.representation_selector,
            self.axes_button,
            self.actor_selector,
            self.actor_visibility_button,
            self.isolate_button,
            self.show_all_button,
            self.clip_axis_selector,
            self.clip_origin_input,
        )

    def set_interactive_enabled(self, enabled: bool) -> None:
        for widget in self.interactive_control_widgets():
            widget.setEnabled(bool(enabled))

    def selected_actor_id(self) -> str:
        return str(self.actor_selector.currentData())

    def selected_clip_axis(self) -> str:
        return self.clip_axis_selector.currentText().lower()

    def _connect_controls(self) -> None:
        for action in ("Orbit", "Pan", "Zoom", "Fit"):
            self.tool_buttons[action].clicked.connect(
                lambda _checked=False, name=action: self.commandRequested.emit(
                    name.lower()
                )
            )
        self.tool_buttons["Camera"].clicked.connect(
            lambda _checked=False: self.cameraPresetRequested.emit(
                self.camera_selector.currentText().lower()
            )
        )
        self.tool_buttons["Section"].toggled.connect(self.clippingToggled.emit)
        self.camera_selector.currentTextChanged.connect(
            lambda text: self.cameraPresetRequested.emit(text.lower())
        )
        self.representation_selector.currentIndexChanged.connect(
            lambda _index: self.representationRequested.emit(
                str(self.representation_selector.currentData())
            )
        )
        self.axes_button.toggled.connect(self.axesToggled.emit)
        self.actor_visibility_button.toggled.connect(
            lambda visible: self.actorVisibilityRequested.emit(
                self.selected_actor_id(),
                visible,
            )
        )
        self.isolate_button.clicked.connect(
            lambda _checked=False: self.actorIsolationRequested.emit(
                self.selected_actor_id()
            )
        )
        self.show_all_button.clicked.connect(
            lambda _checked=False: self.showAllActorsRequested.emit()
        )
        self.clip_axis_selector.currentTextChanged.connect(
            lambda _text: self.clippingUpdated.emit(
                self.selected_clip_axis(),
                float(self.clip_origin_input.value()),
            )
        )
        self.clip_origin_input.valueChanged.connect(
            lambda value: self.clippingUpdated.emit(
                self.selected_clip_axis(),
                float(value),
            )
        )

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
            "QComboBox {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "padding: 3px 8px;"
            "}"
            "QComboBox#oswViewportViewSelector { min-width: 150px; }"
            "QDoubleSpinBox {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "padding: 3px;"
            "max-width: 90px;"
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
