"""Report preview card for the OpenSolver Workbench right inspector."""

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

DEFAULT_REPORT_TITLE = "HeatSink_Flow Simulation Report"
DEFAULT_REPORT_RUN_LABEL = "Run 0001"
DEFAULT_REPORT_SECTIONS = ("Overview", "Key Results", "Summary")


class ReportPreviewThumbnail(_BaseWidget):
    """Small painted heat-sink contour thumbnail for the report preview card."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswReportPreviewThumbnail")
        self.setMinimumSize(112, 68)
        self._tokens = DARK_TOKENS

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

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

        body = rect.adjusted(13, 31, -10, -13)
        base = QtGui.QPainterPath()
        base.moveTo(body.left(), body.top() + 8)
        base.lineTo(body.right() - 10, body.top())
        base.lineTo(body.right(), body.bottom() - 6)
        base.lineTo(body.left() + 8, body.bottom())
        base.closeSubpath()
        painter.setBrush(QtGui.QColor(self._tokens.contour_low))
        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.mesh_line), 1))
        painter.drawPath(base)

        fin_count = 6
        fin_width = max(5.0, body.width() / 16)
        for index in range(fin_count):
            x = body.left() + 12 + index * (fin_width + 5)
            fin = QtCore.QRectF(x, rect.top() + 14, fin_width, body.height() + 7)
            painter.setBrush(QtGui.QColor(self._tokens.contour_low))
            painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.mesh_line), 0.8))
            painter.drawRoundedRect(fin, 1, 1)

        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        mid = QtGui.QColor(self._tokens.contour_mid)
        mid.setAlpha(160)
        hot = QtGui.QColor(self._tokens.contour_high)
        hot.setAlpha(180)
        warm = QtGui.QColor(self._tokens.warning)
        warm.setAlpha(170)
        painter.setBrush(mid)
        painter.drawEllipse(QtCore.QRectF(body.center().x() - 24, body.top() - 1, 48, 22))
        painter.setBrush(warm)
        painter.drawEllipse(QtCore.QRectF(body.center().x() - 15, body.top() + 5, 30, 16))
        painter.setBrush(hot)
        painter.drawEllipse(QtCore.QRectF(body.center().x() - 7, body.top() + 9, 14, 9))

        painter.setPen(QtGui.QPen(QtGui.QColor(self._tokens.mesh_line), 0.6))
        for offset in range(0, int(body.width()), 12):
            painter.drawLine(
                QtCore.QPointF(body.left() + offset, body.bottom()),
                QtCore.QPointF(body.left() + offset + 20, body.top()),
            )


class ReportPreviewPanel(_BaseWidget):
    """Static report preview card with a safe placeholder export action."""

    if QtCore is not None:
        exportRequested = QtCore.Signal()

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswReportPreviewPanel")
        self._tokens = DARK_TOKENS
        self._sections = list(DEFAULT_REPORT_SECTIONS)
        self.last_export_request: str | None = None
        self.last_report_summary: object | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 7, 8, 8)
        layout.setSpacing(6)
        self.header_label = QtWidgets.QLabel("REPORT PREVIEW", self)
        self.header_label.setObjectName("oswReportPreviewHeader")
        self.title_label = QtWidgets.QLabel(DEFAULT_REPORT_TITLE, self)
        self.title_label.setObjectName("oswReportPreviewTitle")
        self.run_label_widget = QtWidgets.QLabel(DEFAULT_REPORT_RUN_LABEL, self)
        self.run_label_widget.setObjectName("oswReportPreviewRunLabel")
        self.summary_status_label = QtWidgets.QLabel("Figures: 0 · Warnings: 0", self)
        self.summary_status_label.setObjectName("oswReportPreviewStatus")

        preview_row = QtWidgets.QHBoxLayout()
        preview_row.setContentsMargins(0, 0, 0, 0)
        preview_row.setSpacing(8)
        self.thumbnail = ReportPreviewThumbnail(self)
        self.sections_list = QtWidgets.QListWidget(self)
        self.sections_list.setObjectName("oswReportPreviewSections")
        self.sections_list.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.sections_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)
        self.sections_list.setFixedHeight(72)
        preview_row.addWidget(self.thumbnail)
        preview_row.addWidget(self.sections_list, 1)

        self.export_button = QtWidgets.QPushButton("Export Report...", self)
        self.export_button.setObjectName("oswExportReportButton")
        self.export_button.clicked.connect(self._record_export_request)

        layout.addWidget(self.header_label)
        layout.addWidget(self.title_label)
        layout.addWidget(self.run_label_widget)
        layout.addWidget(self.summary_status_label)
        layout.addLayout(preview_row)
        layout.addWidget(self.export_button)
        self.set_sections(self._sections)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def report_title(self) -> str:
        return self.title_label.text()

    def run_label(self) -> str:
        return self.run_label_widget.text()

    def report_sections(self) -> list[str]:
        return list(self._sections)

    def report_status_text(self) -> str:
        return self.summary_status_label.text()

    def set_report_title(self, title: str) -> None:
        self.title_label.setText(title)

    def set_run_label(self, label: str) -> None:
        self.run_label_widget.setText(label)

    def set_sections(self, sections: list[str] | tuple[str, ...]) -> None:
        self._sections = list(sections)
        self.sections_list.clear()
        for index, section in enumerate(self._sections, start=1):
            self.sections_list.addItem(f"{index}. {section}")

    def set_export_enabled(self, enabled: bool) -> None:
        self.export_button.setEnabled(enabled)

    def set_report_summary(self, summary: object) -> None:
        """Bind a report summary without executing solver or script workflows."""

        self.last_report_summary = summary
        title = str(getattr(summary, "title", "") or DEFAULT_REPORT_TITLE)
        run_label = str(getattr(summary, "run_label", "") or DEFAULT_REPORT_RUN_LABEL)
        sections = [
            str(getattr(section, "title", section))
            for section in getattr(summary, "sections", ()) or ()
        ]
        figure_count = int(
            getattr(summary, "figure_count", len(getattr(summary, "figures", ())))
        )
        warning_count = int(
            getattr(summary, "warning_count", len(getattr(summary, "warnings", ())))
        )
        self.set_report_title(title)
        self.set_run_label(run_label)
        self.set_sections(sections or list(DEFAULT_REPORT_SECTIONS))
        self.summary_status_label.setText(f"Figures: {figure_count} · Warnings: {warning_count}")

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.thumbnail.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QWidget#oswReportPreviewPanel {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswReportPreviewHeader {"
            f"color: {tokens.accent};"
            "font-weight: 800;"
            "background: transparent;"
            "border: none;"
            "}"
            "QLabel#oswReportPreviewTitle {"
            f"color: {tokens.text_primary};"
            "font-weight: 700;"
            "background: transparent;"
            "border: none;"
            "}"
            "QLabel#oswReportPreviewRunLabel {"
            f"color: {tokens.text_muted};"
            "background: transparent;"
            "border: none;"
            "}"
            "QLabel#oswReportPreviewStatus {"
            f"color: {tokens.text_muted};"
            "background: transparent;"
            "border: none;"
            "font-size: 8pt;"
            "}"
            "QListWidget#oswReportPreviewSections {"
            f"background-color: {tokens.bg_panel};"
            f"color: {tokens.text_secondary};"
            f"border: 1px solid {tokens.border};"
            "font-size: 8pt;"
            "}"
        )

    def _record_export_request(self) -> None:
        self.last_export_request = "placeholder"
        if hasattr(self, "exportRequested"):
            self.exportRequested.emit()
