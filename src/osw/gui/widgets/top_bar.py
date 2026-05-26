"""Top title, visual toolbar, utility actions, and workflow region."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.workflow_stepper import WorkflowStepper

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

APP_TITLE = "OpenSolver Workbench"
APP_SUBTITLE = "Open Source CAE / CFD / CHM / MATLAB-Octave"
TOOLBAR_ACTION_LABELS = ("New", "Open", "Save", "Save As", "Import", "Export")
UTILITY_ACTION_LABELS = ("Terminal", "Preferences", "Help", "About")
TOP_BAR_ACTION_LABELS = TOOLBAR_ACTION_LABELS + UTILITY_ACTION_LABELS
ACTION_OBJECT_NAMES = {
    "New": "oswActionNew",
    "Open": "oswActionOpen",
    "Save": "oswActionSave",
    "Save As": "oswActionSaveAs",
    "Import": "oswActionImport",
    "Export": "oswActionExport",
    "Terminal": "oswActionTerminal",
    "Preferences": "oswActionPreferences",
    "Help": "oswActionHelp",
    "About": "oswActionAbout",
}

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class TopBar(_BaseWidget):
    """Integrated top region for title, toolbar, utilities, and workflow."""

    if QtCore is not None:
        actionTriggered = QtCore.Signal(str)

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswTopRegion")
        self.setMinimumHeight(104)
        self.setMaximumHeight(124)
        self.action_buttons: dict[str, object] = {}

        outer = QtWidgets.QVBoxLayout(self)
        outer.setContentsMargins(12, 8, 12, 8)
        outer.setSpacing(8)

        top_row = QtWidgets.QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(16)

        title_column = QtWidgets.QVBoxLayout()
        title_column.setContentsMargins(0, 0, 0, 0)
        title_column.setSpacing(1)
        self.title_label = QtWidgets.QLabel(APP_TITLE, self)
        self.title_label.setObjectName("oswAppTitle")
        self.subtitle_label = QtWidgets.QLabel(APP_SUBTITLE, self)
        self.subtitle_label.setObjectName("oswAppSubtitle")
        title_column.addWidget(self.title_label)
        title_column.addWidget(self.subtitle_label)

        self.main_toolbar = QtWidgets.QFrame(self)
        self.main_toolbar.setObjectName("oswMainToolBar")
        toolbar_layout = QtWidgets.QHBoxLayout(self.main_toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(6)
        for label in TOOLBAR_ACTION_LABELS:
            toolbar_layout.addWidget(self._create_button(label))

        self.utility_actions = QtWidgets.QFrame(self)
        self.utility_actions.setObjectName("oswTopUtilityActions")
        utility_layout = QtWidgets.QHBoxLayout(self.utility_actions)
        utility_layout.setContentsMargins(0, 0, 0, 0)
        utility_layout.setSpacing(6)
        for label in UTILITY_ACTION_LABELS:
            utility_layout.addWidget(self._create_button(label))

        top_row.addLayout(title_column, 0)
        top_row.addWidget(self.main_toolbar, 0)
        top_row.addStretch(1)
        top_row.addWidget(self.utility_actions, 0)

        self.workflow_stepper = WorkflowStepper(self)
        outer.addLayout(top_row)
        outer.addWidget(self.workflow_stepper, 0)
        self.set_theme_tokens(DARK_TOKENS)

    def action_labels(self) -> list[str]:
        return list(TOP_BAR_ACTION_LABELS)

    def trigger_action(self, label: str) -> None:
        if label not in self.action_buttons:
            raise ValueError(f"Unknown top bar action {label!r}.")
        self.action_buttons[label].click()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self.setStyleSheet(
            "QWidget#oswTopRegion {"
            f"background-color: {tokens.bg_header};"
            f"border-bottom: 1px solid {tokens.border};"
            "}"
            "QLabel#oswAppTitle {"
            f"color: {tokens.text_primary};"
            "font-size: 17pt;"
            "font-weight: 700;"
            "}"
            "QLabel#oswAppSubtitle {"
            f"color: {tokens.text_secondary};"
            "font-size: 9pt;"
            "}"
            "QFrame#oswMainToolBar, QFrame#oswTopUtilityActions {"
            "background: transparent;"
            "border: none;"
            "}"
            "QToolButton {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "padding: 4px 8px;"
            "font-size: 9pt;"
            "font-weight: 600;"
            "}"
            "QToolButton:hover {"
            f"background-color: {tokens.primary_hover};"
            f"border-color: {tokens.border_strong};"
            "}"
            "QToolButton:pressed {"
            f"background-color: {tokens.primary};"
            "}"
        )
        self.workflow_stepper.set_theme_tokens(tokens)

    def _create_button(self, label: str) -> object:
        button = QtWidgets.QToolButton(self)
        button.setObjectName(ACTION_OBJECT_NAMES[label])
        button.setText(label)
        button.setToolTip(label)
        button.setAutoRaise(False)
        button.clicked.connect(lambda _checked=False, text=label: self.actionTriggered.emit(text))
        self.action_buttons[label] = button
        return button
