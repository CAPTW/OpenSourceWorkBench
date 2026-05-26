"""Bottom run monitor panel for the OpenSolver Workbench visual shell."""

from __future__ import annotations

from typing import Any

from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.octave_figure_panel import OctaveFigurePanel
from osw.gui.widgets.residuals_chart import ResidualsChart
from osw.gui.widgets.warnings_progress_panel import WarningsProgressPanel

try:
    from PySide6 import QtCore, QtGui, QtWidgets
except ModuleNotFoundError:
    QtCore = None
    QtGui = None
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

RUN_MONITOR_PANES = ("LOG", "RESIDUALS", "WARNINGS", "OCTAVE / MATLAB FIGURE")
DEMO_RUN_LOG_LINES = (
    "[12:41:02] OpenSolver 2.1.0 starting run...",
    "[12:41:02] Case : HeatSink_Flow",
    "[12:41:02] Mesh : mesh.msh (1.2M cells, 3.8M faces)",
    "[12:41:02] Solver: chtSolver",
    "[12:41:03] Reading material properties...",
    "[12:41:03] Aluminum 6061 assigned to heatsink",
    "[12:41:04] Initializing conjugate heat transfer model",
    "[12:41:05] Starting steady-state iterations",
    "[12:41:08] Iteration 025: residual p=2.2e-03, T=7.4e-04",
    "[12:41:13] Iteration 050: residual p=4.8e-04, T=1.2e-04",
    "[12:41:19] Iteration 100: residual p=3.1e-06, T=9.5e-07",
    "[12:41:26] Converged in 122 iterations.",
    "[12:41:26] Writing results...",
    "[12:41:28] Run completed successfully.",
)


class RunLogPanel(_BaseWidget):
    """Read-only mock run log pane with compatibility append helpers."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtGui is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswRunLogPanel")
        self._tokens = DARK_TOKENS
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(5)
        self.header_label = QtWidgets.QLabel("LOG", self)
        self.header_label.setObjectName("oswRunLogHeader")
        self.log_text = QtWidgets.QPlainTextEdit(self)
        self.log_text.setObjectName("oswRunLogText")
        self.log_text.setReadOnly(True)
        self.log_text.setLineWrapMode(QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap)
        self.log_text.setFont(QtGui.QFont("Consolas", 8))
        layout.addWidget(self.header_label)
        layout.addWidget(self.log_text, 1)
        self.set_log_lines(DEMO_RUN_LOG_LINES)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def set_log_lines(self, lines: tuple[str, ...] | list[str]) -> None:
        self.log_text.setPlainText("\n".join(lines))

    def append_log_line(self, line: str) -> None:
        self.log_text.appendPlainText(line)

    def append_log(self, message: str, *, level: str = "info") -> None:
        self.append_log_line(f"[{level.upper()}] {message}")

    def clear_log(self) -> None:
        self.log_text.clear()

    def toPlainText(self) -> str:  # noqa: N802
        return self.log_text.toPlainText()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.setStyleSheet(
            "QWidget#oswRunLogPanel {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswRunLogHeader {"
            f"color: {tokens.text_secondary};"
            "font-weight: 700;"
            "}"
            "QPlainTextEdit#oswRunLogText {"
            f"background-color: {tokens.bg_viewport};"
            f"color: {tokens.text_secondary};"
            f"border: 1px solid {tokens.border};"
            "font-family: Consolas, 'Cascadia Mono', Menlo, monospace;"
            "font-size: 8pt;"
            "}"
        )


class ResidualsPanel(_BaseWidget):
    """Framed residual chart pane."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswResidualsPanel")
        self._tokens = DARK_TOKENS
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(5)
        self.header_label = QtWidgets.QLabel("RESIDUALS", self)
        self.header_label.setObjectName("oswResidualsHeader")
        self.chart = ResidualsChart(self)
        layout.addWidget(self.header_label)
        layout.addWidget(self.chart, 1)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        self.chart.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QWidget#oswResidualsPanel {"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "}"
            "QLabel#oswResidualsHeader {"
            f"color: {tokens.text_secondary};"
            "font-weight: 700;"
            "}"
        )


class RunMonitorPanel(_BaseWidget):
    """Four-pane bottom monitor with mock log, charts, warnings, and figure data."""

    def __init__(self, parent: object | None = None) -> None:
        if QtCore is None or QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswRunMonitorPanel")
        self.setMinimumHeight(300)
        self._tokens = DARK_TOKENS

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)
        self.header_label = QtWidgets.QLabel("RUN MONITOR", self)
        self.header_label.setObjectName("oswRunMonitorHeader")

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal, self)
        self.splitter.setObjectName("oswRunMonitorSplitter")
        self.log_panel = RunLogPanel(self.splitter)
        self.residuals_panel = ResidualsPanel(self.splitter)
        self.residuals_chart = self.residuals_panel.chart
        self.warnings_progress_panel = WarningsProgressPanel(self.splitter)
        self.octave_panel = OctaveFigurePanel(self.splitter)

        self.splitter.addWidget(self.log_panel)
        self.splitter.addWidget(self.residuals_panel)
        self.splitter.addWidget(self.warnings_progress_panel)
        self.splitter.addWidget(self.octave_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)
        self.splitter.setStretchFactor(2, 2)
        self.splitter.setStretchFactor(3, 2)
        self.splitter.setSizes([420, 340, 280, 340])

        layout.addWidget(self.header_label)
        layout.addWidget(self.splitter, 1)
        self.set_theme_tokens(self._tokens)

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def pane_titles(self) -> list[str]:
        return list(RUN_MONITOR_PANES)

    def reset_demo_data(self) -> None:
        self.log_panel.set_log_lines(DEMO_RUN_LOG_LINES)
        self.residuals_chart.reset_demo_data()
        self.warnings_progress_panel.set_warnings(
            self.warnings_progress_panel.warning_messages()
        )
        self.warnings_progress_panel.set_progress(100)
        self.octave_panel.reset_demo_data()

    def set_log_lines(self, lines: tuple[str, ...] | list[str]) -> None:
        self.log_panel.set_log_lines(lines)

    def append_log_line(self, line: str) -> None:
        self.log_panel.append_log_line(line)

    def append_log(self, message: str, *, level: str = "info") -> None:
        self.log_panel.append_log(message, level=level)

    def clear_log(self) -> None:
        self.log_panel.clear_log()

    def toPlainText(self) -> str:  # noqa: N802
        return self.log_panel.toPlainText()

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        for child in (
            self.log_panel,
            self.residuals_panel,
            self.warnings_progress_panel,
            self.octave_panel,
        ):
            child.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QWidget#oswRunMonitorPanel {"
            f"background-color: {tokens.bg_panel};"
            f"border-top: 1px solid {tokens.border};"
            "}"
            "QLabel#oswRunMonitorHeader {"
            f"color: {tokens.text_secondary};"
            "font-weight: 800;"
            "letter-spacing: 0px;"
            "}"
            "QSplitter#oswRunMonitorSplitter::handle {"
            f"background-color: {tokens.border};"
            "}"
        )
