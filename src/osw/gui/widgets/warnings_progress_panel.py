"""Warnings and progress pane for the OSW run monitor."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

DEMO_WARNINGS = (
    "Mesh skewness is high in 142 cells",
    "Non-orthogonal faces detected (max 68°)",
    "Using default turbulent Prandtl number (0.85)",
)
DEFAULT_RUN_LABEL = "Run 0001 (steady-state)"
DEFAULT_ELAPSED = "00:00:26"
DEFAULT_REMAINING = "00:00:00"
DEFAULT_PROGRESS_PERCENT = 100


class WarningsProgressPanel(_BaseWidget):
    """Stacked warning cards and a safe mock progress control."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswWarningsProgressPanel")
        self._tokens = DARK_TOKENS
        self._warnings = list(DEMO_WARNINGS)
        self._run_label = DEFAULT_RUN_LABEL
        self._elapsed = DEFAULT_ELAPSED
        self._remaining = DEFAULT_REMAINING
        self.last_open_results_request: str | None = None
        self._warning_rows: list[object] = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(8)

        self.header_label = QtWidgets.QLabel("WARNINGS", self)
        self.header_label.setObjectName("oswWarningsHeader")
        layout.addWidget(self.header_label)

        self.warnings_list = QtWidgets.QWidget(self)
        self.warnings_list.setObjectName("oswWarningsList")
        self.warnings_layout = QtWidgets.QVBoxLayout(self.warnings_list)
        self.warnings_layout.setContentsMargins(0, 0, 0, 0)
        self.warnings_layout.setSpacing(5)
        layout.addWidget(self.warnings_list)

        self.progress_panel = QtWidgets.QFrame(self)
        self.progress_panel.setObjectName("oswRunProgressPanel")
        progress_layout = QtWidgets.QVBoxLayout(self.progress_panel)
        progress_layout.setContentsMargins(8, 8, 8, 8)
        progress_layout.setSpacing(5)
        self.progress_header = QtWidgets.QLabel("PROGRESS", self.progress_panel)
        self.run_label = QtWidgets.QLabel(self._run_label, self.progress_panel)
        self.elapsed_label = QtWidgets.QLabel(f"Elapsed {self._elapsed}", self.progress_panel)
        self.remaining_label = QtWidgets.QLabel(
            f"Remaining {self._remaining}",
            self.progress_panel,
        )
        self.progress_bar = QtWidgets.QProgressBar(self.progress_panel)
        self.progress_bar.setObjectName("oswRunProgressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(DEFAULT_PROGRESS_PERCENT)
        self.progress_bar.setFormat("%p%")
        self.open_results_button = QtWidgets.QPushButton(
            "Open Results Folder",
            self.progress_panel,
        )
        self.open_results_button.setObjectName("oswOpenResultsFolderButton")
        self.open_results_button.clicked.connect(self._record_open_results_request)

        for widget in (
            self.progress_header,
            self.run_label,
            self.elapsed_label,
            self.remaining_label,
            self.progress_bar,
            self.open_results_button,
        ):
            progress_layout.addWidget(widget)

        layout.addWidget(self.progress_panel)
        layout.addStretch(1)
        self.set_warnings(self._warnings)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def warning_messages(self) -> list[str]:
        return list(self._warnings)

    def progress_percent(self) -> int:
        return self.progress_bar.value()

    def set_warnings(self, warnings: tuple[str, ...] | list[str]) -> None:
        self._warnings = list(warnings)
        for row in self._warning_rows:
            row.setParent(None)
        self._warning_rows = []
        for warning in self._warnings:
            row = QtWidgets.QFrame(self.warnings_list)
            row.setProperty("oswWarningCard", True)
            row_layout = QtWidgets.QHBoxLayout(row)
            row_layout.setContentsMargins(7, 5, 7, 5)
            row_layout.setSpacing(6)
            marker = QtWidgets.QLabel("!", row)
            marker.setObjectName("oswWarningMarker")
            label = QtWidgets.QLabel(warning, row)
            label.setWordWrap(True)
            row_layout.addWidget(marker)
            row_layout.addWidget(label, 1)
            self.warnings_layout.addWidget(row)
            self._warning_rows.append(row)
        self.set_theme_tokens(self._tokens)

    def set_progress(self, percent: int) -> None:
        self.progress_bar.setValue(max(0, min(100, int(percent))))

    def set_run_label(self, label: str) -> None:
        self._run_label = label
        self.run_label.setText(label)

    def set_elapsed(self, text: str) -> None:
        self._elapsed = text
        self.elapsed_label.setText(f"Elapsed {text}")

    def set_remaining(self, text: str) -> None:
        self._remaining = text
        self.remaining_label.setText(f"Remaining {text}")

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswWarningsProgressPanel {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswWarningsHeader {"
            f"color: {tokens.text_secondary};"
            "font-weight: 700;"
            "}"
            "QFrame[oswWarningCard='true'] {"
            f"background-color: {tokens.bg_viewport};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswWarningMarker {"
            f"color: {tokens.warning};"
            "font-weight: 800;"
            "}"
            "QFrame#oswRunProgressPanel {"
            f"background-color: {tokens.bg_panel};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel {"
            f"color: {tokens.text_secondary};"
            "}"
            "QPushButton#oswOpenResultsFolderButton {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border_strong};"
            f"color: {tokens.text_primary};"
            "padding: 4px 6px;"
            "}"
        )

    def _record_open_results_request(self) -> None:
        self.last_open_results_request = "placeholder"
