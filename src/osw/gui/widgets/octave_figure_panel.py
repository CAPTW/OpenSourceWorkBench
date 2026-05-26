"""Mock Octave / MATLAB figure pane for the OSW run monitor."""

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

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

OCTAVE_FIGURE_DEFAULTS = {
    "title": "Temperature Along Centreline",
    "subtitle": "y = 0, z = 0",
    "x_axis": "x (mm)",
    "y_axis": "Temperature (°C)",
}
DEFAULT_OCTAVE_COMMAND = ">> plot(centreline_x, T_center, '-o')"
DEMO_CENTRELINE_X = (0, 12, 25, 38, 50, 62, 75, 88, 100)
DEMO_CENTRELINE_T = (38, 42, 50, 61, 72, 82, 90, 96, 101)


class OctaveFigureChart(_BaseWidget):
    """Small QPainter line plot used by the mock Octave figure panel."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswOctaveFigureChart")
        self.setMinimumSize(220, 150)
        self._tokens = DARK_TOKENS
        self._x = list(DEMO_CENTRELINE_X)
        self._y = list(DEMO_CENTRELINE_T)
        self._x_axis = OCTAVE_FIGURE_DEFAULTS["x_axis"]
        self._y_axis = OCTAVE_FIGURE_DEFAULTS["y_axis"]

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def x_axis_label(self) -> str:
        return self._x_axis

    def y_axis_label(self) -> str:
        return self._y_axis

    def set_plot_data(self, x: list[float], y: list[float]) -> None:
        self._x = list(x)
        self._y = list(y)
        self.update()

    def reset_demo_data(self) -> None:
        self._x = list(DEMO_CENTRELINE_X)
        self._y = list(DEMO_CENTRELINE_T)
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

        chart_rect = rect.adjusted(42, 18, -14, -32)
        if chart_rect.width() < 60 or chart_rect.height() < 50:
            return

        self._draw_grid(painter, chart_rect)
        self._draw_line(painter, chart_rect)
        self._draw_labels(painter, chart_rect)

    def _draw_grid(self, painter: object, chart_rect: object) -> None:
        painter.setFont(QtGui.QFont("Segoe UI", 7))
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.chart_grid), 1))
        for index in range(5):
            y = chart_rect.top() + chart_rect.height() * index / 4
            painter.drawLine(
                QtCore.QPointF(chart_rect.left(), y),
                QtCore.QPointF(chart_rect.right(), y),
            )
        for index in range(5):
            x = chart_rect.left() + chart_rect.width() * index / 4
            painter.drawLine(
                QtCore.QPointF(x, chart_rect.top()),
                QtCore.QPointF(x, chart_rect.bottom()),
            )
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.chart_axis), 1))
        painter.drawRect(chart_rect)

    def _draw_line(self, painter: object, chart_rect: object) -> None:
        if not self._x or not self._y:
            return

        path = QtGui.QPainterPath()
        points = [self._map_point(x, y, chart_rect) for x, y in zip(self._x, self._y, strict=False)]
        for index, point in enumerate(points):
            if index == 0:
                path.moveTo(point)
            else:
                path.lineTo(point)

        line_color = QtGui.QColor(self._tokens.accent)
        painter.setPen(QtGui.QPen(line_color, 2))
        painter.drawPath(path)
        painter.setBrush(QtGui.QBrush(line_color))
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.bg_viewport), 1))
        for point in points:
            painter.drawEllipse(point, 3.2, 3.2)

    def _draw_labels(self, painter: object, chart_rect: object) -> None:
        painter.setFont(QtGui.QFont("Segoe UI", 7))
        painter.setPen(QtGui.QColor(self._tokens.chart_axis))
        painter.drawText(
            QtCore.QRectF(chart_rect.left(), chart_rect.bottom() + 16, chart_rect.width(), 14),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            self._x_axis,
        )
        painter.save()
        painter.translate(10, chart_rect.center().y())
        painter.rotate(-90)
        painter.drawText(
            QtCore.QRectF(-chart_rect.height() / 2, 0, chart_rect.height(), 14),
            QtCore.Qt.AlignmentFlag.AlignCenter,
            self._y_axis,
        )
        painter.restore()

    def _map_point(self, x_value: float, y_value: float, rect: object) -> object:
        x_min, x_max = min(self._x), max(self._x)
        y_min, y_max = min(self._y), max(self._y)
        x_span = max(1.0, x_max - x_min)
        y_span = max(1.0, y_max - y_min)
        x = rect.left() + rect.width() * (x_value - x_min) / x_span
        y = rect.bottom() - rect.height() * (y_value - y_min) / y_span
        return QtCore.QPointF(x, y)


class OctaveFigurePanel(_BaseWidget):
    """Mock Octave / MATLAB figure card with title, plot, and command line."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswOctaveFigurePanel")
        self._tokens = DARK_TOKENS

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(5)
        self.header_label = QtWidgets.QLabel("OCTAVE / MATLAB FIGURE", self)
        self.title_label = QtWidgets.QLabel(OCTAVE_FIGURE_DEFAULTS["title"], self)
        self.subtitle_label = QtWidgets.QLabel(OCTAVE_FIGURE_DEFAULTS["subtitle"], self)
        self.chart = OctaveFigureChart(self)
        self.command_line = QtWidgets.QLineEdit(DEFAULT_OCTAVE_COMMAND, self)
        self.command_line.setObjectName("oswOctaveCommandLine")
        self.command_line.setReadOnly(True)

        layout.addWidget(self.header_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.subtitle_label)
        layout.addWidget(self.chart, 1)
        layout.addWidget(self.command_line)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def title(self) -> str:
        return self.title_label.text()

    def subtitle(self) -> str:
        return self.subtitle_label.text()

    def command(self) -> str:
        return self.command_line.text()

    def x_axis_label(self) -> str:
        return self.chart.x_axis_label()

    def y_axis_label(self) -> str:
        return self.chart.y_axis_label()

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_subtitle(self, subtitle: str) -> None:
        self.subtitle_label.setText(subtitle)

    def set_command(self, command: str) -> None:
        self.command_line.setText(command)

    def set_plot_data(self, x: list[float], y: list[float]) -> None:
        self.chart.set_plot_data(x, y)

    def reset_demo_data(self) -> None:
        self.set_title(OCTAVE_FIGURE_DEFAULTS["title"])
        self.set_subtitle(OCTAVE_FIGURE_DEFAULTS["subtitle"])
        self.set_command(DEFAULT_OCTAVE_COMMAND)
        self.chart.reset_demo_data()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.chart.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QWidget#oswOctaveFigurePanel {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel {"
            f"color: {tokens.text_secondary};"
            "background: transparent;"
            "}"
            "QLineEdit#oswOctaveCommandLine {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.accent};"
            f"border: 1px solid {tokens.border};"
            "font-family: Consolas, 'Cascadia Mono', Menlo, monospace;"
            "font-size: 8pt;"
            "}"
        )
