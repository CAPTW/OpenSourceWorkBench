"""Compact bottom status bar for the OpenSolver Workbench visual shell."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtGui = None
    QtWidgets = None

_BaseStatusBar: Any = QtWidgets.QStatusBar if QtWidgets is not None else object
_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

DEFAULT_SOLVER_NAME = "chtSolver"
DEFAULT_MEMORY_USAGE = (6.2, 15.9)
DEFAULT_CORE_USAGE = (12, 16)
DEFAULT_READY_TEXT = "Ready"


class StatusIndicator(_BaseWidget):
    """Small painted status dot."""

    def __init__(self, object_name: str, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName(object_name)
        self.setFixedSize(10, 10)
        self._tokens = DARK_TOKENS
        self._active = True

    def set_active(self, active: bool) -> None:
        self._active = active
        self.update()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        color = QtGui.QColor(self._tokens.success if self._active else self._tokens.warning)
        painter.setBrush(color)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawEllipse(QtCore.QRectF(1, 1, 8, 8))


class CompactUsageBar(_BaseWidget):
    """Tiny theme-aware usage bar for static memory/core status."""

    def __init__(self, object_name: str, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName(object_name)
        self.setFixedSize(72, 9)
        self._tokens = DARK_TOKENS
        self._used = 0.0
        self._total = 1.0

    def set_usage(self, used: float, total: float) -> None:
        self._used = float(used)
        self._total = max(0.001, float(total))
        self.update()

    def ratio(self) -> float:
        return max(0.0, min(1.0, self._used / self._total))

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.border), 1))
        painter.setBrush(QtGui.QColor(self._tokens.bg_viewport))
        painter.drawRoundedRect(rect, 2, 2)
        fill = QtCore.QRectF(rect)
        fill.setWidth(rect.width() * self.ratio())
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.setBrush(QtGui.QColor(self._tokens.primary))
        painter.drawRoundedRect(fill, 2, 2)


class OswStatusBar(_BaseStatusBar):
    """Compact status bar matching the reference shell data."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswStatusBar")
        self.setSizeGripEnabled(False)
        self._tokens = DARK_TOKENS
        self._solver_name = DEFAULT_SOLVER_NAME
        self._memory_usage = DEFAULT_MEMORY_USAGE
        self._core_usage = DEFAULT_CORE_USAGE
        self._ready_text = DEFAULT_READY_TEXT

        self.solver_indicator = StatusIndicator("oswStatusSolverIndicator", self)
        self.solver_label = QtWidgets.QLabel(f"Solver: {self._solver_name}", self)
        self.solver_label.setObjectName("oswStatusSolverLabel")
        self.memory_label = QtWidgets.QLabel(self._memory_text(), self)
        self.memory_label.setObjectName("oswStatusMemoryLabel")
        self.memory_bar = CompactUsageBar("oswStatusMemoryBar", self)
        self.memory_bar.set_usage(*self._memory_usage)
        self.cores_label = QtWidgets.QLabel(self._core_text(), self)
        self.cores_label.setObjectName("oswStatusCoresLabel")
        self.cores_bar = CompactUsageBar("oswStatusCoresBar", self)
        self.cores_bar.set_usage(*self._core_usage)
        self.ready_indicator = StatusIndicator("oswStatusReadyIndicator", self)
        self.ready_label = QtWidgets.QLabel(self._ready_text, self)
        self.ready_label.setObjectName("oswStatusReadyLabel")

        for widget in (
            self.solver_indicator,
            self.solver_label,
            self.memory_label,
            self.memory_bar,
            self.cores_label,
            self.cores_bar,
        ):
            self.addWidget(widget)
        self.addPermanentWidget(self.ready_indicator)
        self.addPermanentWidget(self.ready_label)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def solver_name(self) -> str:
        return self._solver_name

    def memory_usage(self) -> tuple[float, float]:
        return self._memory_usage

    def core_usage(self) -> tuple[int, int]:
        return self._core_usage

    def ready_text(self) -> str:
        return self._ready_text

    def set_solver_status(self, name: str, ready: bool = True) -> None:
        self._solver_name = name
        self.solver_label.setText(f"Solver: {name}")
        self.solver_indicator.set_active(ready)

    def set_memory_usage(self, used_gb: float, total_gb: float) -> None:
        self._memory_usage = (float(used_gb), float(total_gb))
        self.memory_label.setText(self._memory_text())
        self.memory_bar.set_usage(*self._memory_usage)

    def set_core_usage(self, used: int, total: int) -> None:
        self._core_usage = (int(used), int(total))
        self.cores_label.setText(self._core_text())
        self.cores_bar.set_usage(float(used), float(total))

    def set_ready_text(self, text: str) -> None:
        self._ready_text = text
        self.ready_label.setText(text)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        for child in (
            self.solver_indicator,
            self.memory_bar,
            self.cores_bar,
            self.ready_indicator,
        ):
            child.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QStatusBar#oswStatusBar {"
            f"background-color: {tokens.bg_header};"
            f"color: {tokens.text_secondary};"
            f"border-top: 1px solid {tokens.border};"
            "min-height: 26px;"
            "}"
            "QStatusBar#oswStatusBar QLabel {"
            f"color: {tokens.text_secondary};"
            "padding: 0 6px;"
            "font-size: 8pt;"
            "}"
        )

    def _memory_text(self) -> str:
        used, total = self._memory_usage
        return f"Memory: {used:.1f} GB / {total:.1f} GB"

    def _core_text(self) -> str:
        used, total = self._core_usage
        return f"Cores: {used} / {total}"
