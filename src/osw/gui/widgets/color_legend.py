"""Color legend overlay for the mock simulation viewport."""

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

LEGEND_TICKS = ("2.50e+08", "2.00e+08", "1.50e+08", "1.00e+08", "5.00e+07", "0.00e+00")
_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class ColorLegend(_BaseWidget):
    """Painted von Mises Stress legend."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswViewportLegend")
        self._tokens = DARK_TOKENS
        self._quantity = "von Mises Stress"
        self._unit = "Pa"
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.update()

    def set_result_quantity(self, name: str, unit: str = "Pa") -> None:
        self._quantity = name
        self._unit = unit
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        tokens = self._tokens
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(0, 0, -1, -1)
        panel = QtGui.QColor(tokens.bg_panel)
        panel.setAlpha(205)
        painter.setBrush(panel)
        painter.setPen(QtGui.QPen(QtGui.QColor(tokens.border), 1))
        painter.drawRoundedRect(rect, 5, 5)

        painter.setPen(QtGui.QColor(tokens.text_primary))
        title_font = painter.font()
        title_font.setPointSize(9)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(10, 22, self._quantity)
        painter.setPen(QtGui.QColor(tokens.text_secondary))
        painter.drawText(10, 42, f"({self._unit})")

        bar = QtCore.QRect(12, 62, 20, max(80, rect.height() - 82))
        gradient = QtGui.QLinearGradient(bar.topLeft(), bar.bottomLeft())
        gradient.setColorAt(0.0, QtGui.QColor(tokens.contour_high))
        gradient.setColorAt(0.35, QtGui.QColor(tokens.warning))
        gradient.setColorAt(0.62, QtGui.QColor(tokens.contour_mid))
        gradient.setColorAt(1.0, QtGui.QColor(tokens.contour_low))
        painter.fillRect(bar, gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor(tokens.border_strong), 1))
        painter.drawRect(bar)

        painter.setPen(QtGui.QColor(tokens.text_secondary))
        font = painter.font()
        font.setPointSize(8)
        font.setBold(False)
        painter.setFont(font)
        step = bar.height() / (len(LEGEND_TICKS) - 1)
        for index, tick in enumerate(LEGEND_TICKS):
            y = int(bar.top() + index * step)
            painter.drawLine(bar.right() + 4, y, bar.right() + 9, y)
            painter.drawText(bar.right() + 12, y + 4, tick)
