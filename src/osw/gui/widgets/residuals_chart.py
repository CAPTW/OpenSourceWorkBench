"""QPainter-based residual convergence chart for the OSW run monitor."""

from __future__ import annotations

import math
from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtGui = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

RESIDUAL_SERIES_NAMES = ("p", "T", "Ux", "Uy", "Uz")
DEMO_ITERATIONS = (0, 25, 50, 75, 100, 122)
DEMO_RESIDUAL_SERIES = {
    "p": (1.0, 2.2e-2, 4.8e-4, 3.8e-5, 3.1e-6, 8.0e-7),
    "T": (8.5e-1, 7.4e-3, 1.2e-4, 1.6e-5, 9.5e-7, 4.4e-7),
    "Ux": (6.0e-1, 1.0e-2, 7.5e-4, 8.8e-5, 6.5e-6, 1.8e-6),
    "Uy": (4.5e-1, 6.6e-3, 5.2e-4, 4.1e-5, 4.8e-6, 1.2e-6),
    "Uz": (3.5e-1, 4.3e-3, 2.8e-4, 2.9e-5, 3.4e-6, 9.0e-7),
}
Y_AXIS_LABELS = ("1e+00", "1e-01", "1e-02", "1e-03", "1e-04", "1e-05", "1e-06")
X_AXIS_TICKS = (0, 25, 50, 75, 100, 125)


class ResidualsChart(_BaseWidget):
    """Responsive mock residual chart with deterministic convergence curves."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswResidualsChart")
        self.setMinimumSize(260, 180)
        self._tokens = DARK_TOKENS
        self._iterations = list(DEMO_ITERATIONS)
        self._series = {name: list(values) for name, values in DEMO_RESIDUAL_SERIES.items()}
        self._log_scale = True

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def series_names(self) -> list[str]:
        return list(self._series)

    def iterations(self) -> list[int]:
        return list(self._iterations)

    def set_series_data(self, name: str, values: list[float]) -> None:
        self._series[name] = list(values)
        self.update()

    def set_iterations(self, iterations: list[int]) -> None:
        self._iterations = list(iterations)
        self.update()

    def set_log_scale(self, enabled: bool) -> None:
        self._log_scale = enabled
        self.update()

    def reset_demo_data(self) -> None:
        self._iterations = list(DEMO_ITERATIONS)
        self._series = {name: list(values) for name, values in DEMO_RESIDUAL_SERIES.items()}
        self._log_scale = True
        self.update()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.update()

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        rect = QtCore.QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        painter.fillRect(rect, QtGui.QColor(self._tokens.bg_viewport))
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.border), 1))
        painter.drawRoundedRect(rect, 4, 4)

        chart_rect = rect.adjusted(48, 18, -68, -34)
        if chart_rect.width() < 80 or chart_rect.height() < 70:
            return

        self._draw_grid(painter, chart_rect)
        self._draw_series(painter, chart_rect)
        self._draw_axes(painter, chart_rect)
        self._draw_legend(painter, rect)

    def _draw_grid(self, painter: object, chart_rect: object) -> None:
        grid_pen = QtGui.QPen(QtGui.QColor(self._tokens.chart_grid), 1)
        axis_pen = QtGui.QPen(QtGui.QColor(self._tokens.chart_axis), 1)
        painter.setFont(QtGui.QFont("Segoe UI", 7))

        for index, label in enumerate(Y_AXIS_LABELS):
            y = chart_rect.top() + (chart_rect.height() * index / (len(Y_AXIS_LABELS) - 1))
            painter.setPen(grid_pen)
            painter.drawLine(
                QtCore.QPointF(chart_rect.left(), y),
                QtCore.QPointF(chart_rect.right(), y),
            )
            painter.setPen(QtGui.QColor(self._tokens.chart_axis))
            painter.drawText(
                QtCore.QRectF(2, y - 8, chart_rect.left() - 8, 16),
                QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter,
                label,
            )

        max_tick = max(X_AXIS_TICKS)
        for tick in X_AXIS_TICKS:
            x = chart_rect.left() + chart_rect.width() * tick / max_tick
            painter.setPen(grid_pen)
            painter.drawLine(
                QtCore.QPointF(x, chart_rect.top()),
                QtCore.QPointF(x, chart_rect.bottom()),
            )
            painter.setPen(QtGui.QColor(self._tokens.chart_axis))
            painter.drawText(
                QtCore.QRectF(x - 16, chart_rect.bottom() + 4, 32, 16),
                QtCore.Qt.AlignmentFlag.AlignCenter,
                str(tick),
            )

        painter.setPen(axis_pen)
        painter.drawRect(chart_rect)

    def _draw_series(self, painter: object, chart_rect: object) -> None:
        colors = self._series_colors()
        for name, values in self._series.items():
            if not values or not self._iterations:
                continue
            path = QtGui.QPainterPath()
            for index, value in enumerate(values):
                iteration = self._iterations[min(index, len(self._iterations) - 1)]
                point = self._map_point(iteration, value, chart_rect)
                if index == 0:
                    path.moveTo(point)
                else:
                    path.lineTo(point)
            painter.setPen(QtGui.QPen(colors.get(name, QtGui.QColor(self._tokens.info)), 2))
            painter.drawPath(path)

    def _draw_axes(self, painter: object, chart_rect: object) -> None:
        painter.setPen(QtGui.QColor(self._tokens.text_muted))
        painter.setFont(QtGui.QFont("Segoe UI", 7))
        painter.drawText(
            QtCore.QRectF(chart_rect.left(), chart_rect.bottom() + 18, chart_rect.width(), 14),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            "Iterations",
        )

    def _draw_legend(self, painter: object, rect: object) -> None:
        colors = self._series_colors()
        painter.setFont(QtGui.QFont("Segoe UI", 8))
        legend_x = rect.right() - 56
        legend_y = rect.top() + 24
        for index, name in enumerate(self._series):
            y = legend_y + index * 18
            painter.setPen(QtGui.QPen(colors.get(name, QtGui.QColor(self._tokens.info)), 2))
            painter.drawLine(QtCore.QPointF(legend_x, y + 7), QtCore.QPointF(legend_x + 18, y + 7))
            painter.setPen(QtGui.QColor(self._tokens.text_secondary))
            painter.drawText(QtCore.QRectF(legend_x + 24, y, 30, 14), name)

    def _series_colors(self) -> dict[str, object]:
        return {
            "p": QtGui.QColor(self._tokens.primary),
            "T": QtGui.QColor(self._tokens.warning),
            "Ux": QtGui.QColor(self._tokens.success),
            "Uy": QtGui.QColor(self._tokens.accent),
            "Uz": QtGui.QColor(self._tokens.info),
        }

    def _map_point(self, iteration: int, value: float, rect: object) -> object:
        max_iteration = 125
        x = rect.left() + rect.width() * max(0, min(iteration, max_iteration)) / max_iteration
        if self._log_scale:
            log_value = math.log10(max(value, 1.0e-6))
            y_fraction = (0.0 - max(-6.0, min(0.0, log_value))) / 6.0
        else:
            y_fraction = 1.0 - max(0.0, min(1.0, value))
        y = rect.top() + rect.height() * y_fraction
        return QtCore.QPointF(x, y)
