"""QPainter-based mock heat-sink simulation viewport."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.color_legend import ColorLegend

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtGui = None
    QtWidgets = None

DEFAULT_RESULT_QUANTITY = "von Mises Stress"
DEFAULT_RESULT_UNIT = "Pa"
VIEWPORT_FEATURE_FLAGS = {
    "has_color_legend": True,
    "has_orientation_cube": True,
    "has_axis_triad": True,
    "has_scale_bar": True,
    "has_mesh_overlay": True,
}

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object


class MockSimulationViewport(_BaseWidget):
    """Mock 3D result viewport with heat sink, mesh, contours, and annotations."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())
        super().__init__(parent)
        self.setObjectName("oswMockSimulationViewport")
        self.setMinimumSize(560, 360)
        self._tokens = DARK_TOKENS
        self._result_quantity = DEFAULT_RESULT_QUANTITY
        self._result_unit = DEFAULT_RESULT_UNIT
        self.has_color_legend = True
        self.has_orientation_cube = True
        self.has_axis_triad = True
        self.has_scale_bar = True
        self.has_mesh_overlay = True
        self.legend = ColorLegend(self)
        self.legend.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def result_quantity(self) -> str:
        return self._result_quantity

    def result_unit(self) -> str:
        return self._result_unit

    def set_result_quantity(self, name: str, unit: str = "Pa") -> None:
        self._result_quantity = name
        self._result_unit = unit
        self.legend.set_result_quantity(name, unit)
        self.update()

    def set_show_mesh_overlay(self, enabled: bool) -> None:
        self.has_mesh_overlay = enabled
        self.update()

    def set_show_legend(self, enabled: bool) -> None:
        self.has_color_legend = enabled
        self.legend.setVisible(enabled)
        self.update()

    def set_show_orientation_cube(self, enabled: bool) -> None:
        self.has_orientation_cube = enabled
        self.update()

    def set_show_scale_bar(self, enabled: bool) -> None:
        self.has_scale_bar = enabled
        self.update()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.legend.set_theme_tokens(tokens)
        self.update()

    def resizeEvent(self, event: object) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.legend.setGeometry(18, 54, 142, min(246, max(188, self.height() - 170)))

    def paintEvent(self, _event: object) -> None:  # noqa: N802
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self._draw_background(painter)
        model = self._model_geometry()
        self._draw_pipe(painter, model)
        self._draw_heat_sink(painter, model)
        self._draw_contours(painter, model)
        if self.has_mesh_overlay:
            self._draw_mesh_overlay(painter, model)
        if self.has_orientation_cube:
            self._draw_orientation_cube(painter)
        if self.has_axis_triad:
            self._draw_axis_triad(painter)
        if self.has_scale_bar:
            self._draw_scale_bar(painter)

    def _draw_background(self, painter: object) -> None:
        rect = self.rect()
        gradient = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, QtGui.QColor(self._tokens.bg_viewport))
        gradient.setColorAt(1.0, QtGui.QColor(self._tokens.bg_app))
        painter.fillRect(rect, gradient)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.chart_grid), 1))
        for x in range(0, rect.width(), 42):
            painter.drawLine(x, rect.height(), x + 120, 0)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.border), 1))
        painter.drawRect(rect.adjusted(0, 0, -1, -1))

    def _model_geometry(self) -> dict[str, object]:
        w = self.width()
        h = self.height()
        cx = int(w * 0.53)
        cy = int(h * 0.55)
        width = int(w * 0.44)
        depth = int(h * 0.30)
        skew = int(w * 0.10)
        top_left = QtCore.QPoint(cx - width // 2, cy - depth // 2)
        top_right = QtCore.QPoint(cx + width // 2, cy - depth // 2 - skew // 3)
        bottom_right = QtCore.QPoint(cx + width // 2 + skew, cy + depth // 2)
        bottom_left = QtCore.QPoint(cx - width // 2 + skew, cy + depth // 2 + skew // 3)
        return {
            "base": QtGui.QPolygon([top_left, top_right, bottom_right, bottom_left]),
            "top_left": top_left,
            "top_right": top_right,
            "bottom_left": bottom_left,
            "bottom_right": bottom_right,
            "width": width,
            "depth": depth,
            "skew": skew,
            "cx": cx,
            "cy": cy,
        }

    def _draw_heat_sink(self, painter: object, model: dict[str, object]) -> None:
        base_color = QtGui.QColor(self._tokens.contour_low)
        base_color.setAlpha(225)
        painter.setBrush(base_color)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.mesh_line), 2))
        painter.drawPolygon(model["base"])

        top_left = model["top_left"]
        top_right = model["top_right"]
        bottom_left = model["bottom_left"]
        fin_count = 9
        for index in range(fin_count):
            t = (index + 0.5) / fin_count
            x_top = top_left.x() + int((top_right.x() - top_left.x()) * t)
            y_top = top_left.y() + int((top_right.y() - top_left.y()) * t)
            x_bot = bottom_left.x() + int((model["bottom_right"].x() - bottom_left.x()) * t)
            y_bot = bottom_left.y() + int((model["bottom_right"].y() - bottom_left.y()) * t)
            fin_height = int(self.height() * 0.23)
            fin_width = max(10, int(self.width() * 0.018))
            fin = QtGui.QPolygon(
                [
                    QtCore.QPoint(x_top - fin_width, y_top - fin_height),
                    QtCore.QPoint(x_top + fin_width, y_top - fin_height - 8),
                    QtCore.QPoint(x_bot + fin_width, y_bot - 16),
                    QtCore.QPoint(x_bot - fin_width, y_bot - 7),
                ]
            )
            shade = QtGui.QColor(self._tokens.contour_low)
            shade.setAlpha(210)
            painter.setBrush(shade)
            painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.mesh_line), 1))
            painter.drawPolygon(fin)

    def _draw_pipe(self, painter: object, model: dict[str, object]) -> None:
        left = model["top_left"]
        center = QtCore.QPoint(
            left.x() - int(self.width() * 0.08),
            left.y() + int(self.height() * 0.12),
        )
        radius = max(22, int(self.height() * 0.055))
        body_rect = QtCore.QRect(
            center.x(),
            center.y() - radius,
            int(self.width() * 0.14),
            radius * 2,
        )
        color = QtGui.QColor(self._tokens.contour_low)
        color.setAlpha(215)
        painter.setBrush(color)
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.mesh_line), 2))
        painter.drawRect(body_rect.adjusted(0, 5, 0, -5))
        painter.drawEllipse(
            QtCore.QRect(
                center.x() - radius,
                center.y() - radius,
                radius * 2,
                radius * 2,
            )
        )

    def _draw_contours(self, painter: object, model: dict[str, object]) -> None:
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        cx = model["cx"]
        cy = model["cy"]
        for color_name, scale, alpha in (
            (self._tokens.contour_mid, 0.34, 150),
            (self._tokens.warning, 0.22, 165),
            (self._tokens.contour_high, 0.12, 185),
        ):
            color = QtGui.QColor(color_name)
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.drawEllipse(
                QtCore.QPoint(cx, cy - int(self.height() * 0.03)),
                int(self.width() * scale),
                int(self.height() * scale * 0.55),
            )
        root_color = QtGui.QColor(self._tokens.contour_high)
        root_color.setAlpha(150)
        painter.setBrush(root_color)
        for offset in (-90, -45, 0, 45, 90):
            painter.drawEllipse(
                QtCore.QPoint(cx + offset, cy - int(self.height() * 0.18)),
                22,
                70,
            )

    def _draw_mesh_overlay(self, painter: object, model: dict[str, object]) -> None:
        pen = QtGui.QPen(QtGui.QColor(self._tokens.mesh_line), 1)
        pen.setCosmetic(True)
        painter.setPen(pen)
        base = model["base"].boundingRect()
        for x in range(base.left(), base.right(), 24):
            painter.drawLine(x, base.top(), x + int(self.width() * 0.11), base.bottom())
            painter.drawLine(x, base.bottom(), x + int(self.width() * 0.08), base.top())
        for y in range(base.top(), base.bottom(), 20):
            painter.drawLine(base.left(), y, base.right(), y - int(self.width() * 0.05))

    def _draw_orientation_cube(self, painter: object) -> None:
        x = self.width() - 138
        y = 42
        front = QtGui.QPolygon(
            [
                QtCore.QPoint(x, y + 34),
                QtCore.QPoint(x + 44, y + 48),
                QtCore.QPoint(x + 44, y + 92),
                QtCore.QPoint(x, y + 74),
            ]
        )
        right = QtGui.QPolygon(
            [
                QtCore.QPoint(x + 44, y + 48),
                QtCore.QPoint(x + 82, y + 28),
                QtCore.QPoint(x + 82, y + 70),
                QtCore.QPoint(x + 44, y + 92),
            ]
        )
        top = QtGui.QPolygon(
            [
                QtCore.QPoint(x, y + 34),
                QtCore.QPoint(x + 38, y + 14),
                QtCore.QPoint(x + 82, y + 28),
                QtCore.QPoint(x + 44, y + 48),
            ]
        )
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.border_strong), 1))
        for poly, label in ((top, "TOP"), (front, "FRONT"), (right, "RIGHT")):
            color = QtGui.QColor(self._tokens.bg_panel_alt)
            color.setAlpha(205)
            painter.setBrush(color)
            painter.drawPolygon(poly)
            painter.setPen(QtGui.QColor(self._tokens.text_secondary))
            painter.drawText(poly.boundingRect(), QtCore.Qt.AlignmentFlag.AlignCenter, label)
            painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.border_strong), 1))
        self._draw_axes(painter, QtCore.QPoint(x + 22, y + 112), 28)

    def _draw_axis_triad(self, painter: object) -> None:
        self._draw_axes(painter, QtCore.QPoint(74, self.height() - 76), 34)

    def _draw_axes(self, painter: object, origin: object, length: int) -> None:
        axes = (
            ("X", QtGui.QColor("#ff4b4b"), QtCore.QPoint(length, 16)),
            ("Y", QtGui.QColor("#7ee35b"), QtCore.QPoint(length, -8)),
            ("Z", QtGui.QColor("#2f8cff"), QtCore.QPoint(0, -length)),
        )
        for label, color, delta in axes:
            painter.setPen(QtGui.QPen(color, 2))
            end = origin + delta
            painter.drawLine(origin, end)
            painter.setPen(color)
            painter.drawText(end + QtCore.QPoint(4, 4), label)

    def _draw_scale_bar(self, painter: object) -> None:
        width = 220
        x = self.width() - width - 36
        y = self.height() - 48
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.text_secondary), 1))
        painter.drawLine(x, y, x + width, y)
        labels = ("0", "25", "50", "75", "100 mm")
        for index, label in enumerate(labels):
            tick_x = x + int(width * index / (len(labels) - 1))
            painter.drawLine(tick_x, y - 5, tick_x, y + 5)
            painter.drawText(
                tick_x - 16,
                y - 10,
                44,
                12,
                QtCore.Qt.AlignmentFlag.AlignCenter,
                label,
            )
