"""Tests for the UI-006 run monitor and chart panels."""

from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtCore, QtGui, QtWidgets
else:
    QtCore = None
    QtGui = None
    QtWidgets = None


def test_run_monitor_contract_is_import_safe_without_pyside6() -> None:
    from osw.gui.widgets.octave_figure_panel import (
        DEFAULT_OCTAVE_COMMAND,
        OCTAVE_FIGURE_DEFAULTS,
    )
    from osw.gui.widgets.residuals_chart import RESIDUAL_SERIES_NAMES
    from osw.gui.widgets.run_monitor_panel import DEMO_RUN_LOG_LINES, RUN_MONITOR_PANES
    from osw.gui.widgets.warnings_progress_panel import (
        DEFAULT_PROGRESS_PERCENT,
        DEMO_WARNINGS,
    )

    assert RUN_MONITOR_PANES == (
        "LOG",
        "RESIDUALS",
        "WARNINGS",
        "OCTAVE / MATLAB FIGURE",
    )
    assert "HeatSink_Flow" in "\n".join(DEMO_RUN_LOG_LINES)
    assert "chtSolver" in "\n".join(DEMO_RUN_LOG_LINES)
    assert "Run completed successfully." in "\n".join(DEMO_RUN_LOG_LINES)
    assert RESIDUAL_SERIES_NAMES == ("p", "T", "Ux", "Uy", "Uz")
    assert DEMO_WARNINGS == (
        "Mesh skewness is high in 142 cells",
        "Non-orthogonal faces detected (max 68°)",
        "Using default turbulent Prandtl number (0.85)",
    )
    assert DEFAULT_PROGRESS_PERCENT == 100
    assert OCTAVE_FIGURE_DEFAULTS["title"] == "Temperature Along Centreline"
    assert OCTAVE_FIGURE_DEFAULTS["subtitle"] == "y = 0, z = 0"
    assert OCTAVE_FIGURE_DEFAULTS["x_axis"] == "x (mm)"
    assert OCTAVE_FIGURE_DEFAULTS["y_axis"] == "Temperature (°C)"
    assert DEFAULT_OCTAVE_COMMAND == ">> plot(centreline_x, T_center, '-o')"


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_run_monitor_panel_instantiates_with_four_panes(app: object) -> None:
    from osw.gui.widgets.run_monitor_panel import RUN_MONITOR_PANES, RunMonitorPanel

    panel = RunMonitorPanel()

    assert panel.objectName() == "oswRunMonitorPanel"
    assert panel.header_label.objectName() == "oswRunMonitorHeader"
    assert panel.pane_titles() == list(RUN_MONITOR_PANES)
    assert panel.log_panel.objectName() == "oswRunLogPanel"
    assert panel.residuals_panel.objectName() == "oswResidualsPanel"
    assert panel.warnings_progress_panel.objectName() == "oswWarningsProgressPanel"
    assert panel.octave_panel.objectName() == "oswOctaveFigurePanel"


def test_log_panel_contains_demo_run_and_appends_lines(app: object) -> None:
    from osw.gui.widgets.run_monitor_panel import RunMonitorPanel

    panel = RunMonitorPanel()

    assert panel.log_panel.log_text.objectName() == "oswRunLogText"
    assert "HeatSink_Flow" in panel.toPlainText()
    assert "chtSolver" in panel.toPlainText()
    assert "Run completed successfully." in panel.toPlainText()

    panel.append_log("Post-run handoff ready", level="info")
    assert "Post-run handoff ready" in panel.toPlainText()


def test_residuals_chart_defaults_to_reference_series(app: object) -> None:
    from osw.gui.widgets.residuals_chart import RESIDUAL_SERIES_NAMES, ResidualsChart

    chart = ResidualsChart()

    assert chart.objectName() == "oswResidualsChart"
    assert chart.series_names() == list(RESIDUAL_SERIES_NAMES)
    assert chart.iterations() == [0, 25, 50, 75, 100, 122]


def test_warnings_progress_panel_defaults_and_safe_button(app: object) -> None:
    from osw.gui.widgets.warnings_progress_panel import (
        DEFAULT_PROGRESS_PERCENT,
        DEMO_WARNINGS,
        WarningsProgressPanel,
    )

    panel = WarningsProgressPanel()

    assert panel.objectName() == "oswWarningsProgressPanel"
    assert panel.warnings_list.objectName() == "oswWarningsList"
    assert panel.progress_panel.objectName() == "oswRunProgressPanel"
    assert panel.progress_bar.objectName() == "oswRunProgressBar"
    assert panel.open_results_button.objectName() == "oswOpenResultsFolderButton"
    assert panel.warning_messages() == list(DEMO_WARNINGS)
    assert panel.progress_percent() == DEFAULT_PROGRESS_PERCENT

    panel.open_results_button.click()
    assert panel.last_open_results_request == "placeholder"


def test_octave_figure_panel_contains_reference_labels_and_command(app: object) -> None:
    from osw.gui.widgets.octave_figure_panel import (
        DEFAULT_OCTAVE_COMMAND,
        OCTAVE_FIGURE_DEFAULTS,
        OctaveFigurePanel,
    )

    panel = OctaveFigurePanel()

    assert panel.objectName() == "oswOctaveFigurePanel"
    assert panel.chart.objectName() == "oswOctaveFigureChart"
    assert panel.command_line.objectName() == "oswOctaveCommandLine"
    assert panel.title() == OCTAVE_FIGURE_DEFAULTS["title"]
    assert panel.subtitle() == OCTAVE_FIGURE_DEFAULTS["subtitle"]
    assert panel.x_axis_label() == OCTAVE_FIGURE_DEFAULTS["x_axis"]
    assert panel.y_axis_label() == OCTAVE_FIGURE_DEFAULTS["y_axis"]
    assert panel.command() == DEFAULT_OCTAVE_COMMAND


def test_run_monitor_widgets_accept_dark_and_light_tokens(app: object) -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.widgets.run_monitor_panel import RunMonitorPanel

    panel = RunMonitorPanel()
    manager = ThemeManager(auto_load=False)

    manager.set_mode("dark", save=False)
    panel.set_theme_tokens(manager.current_tokens)
    manager.set_mode("light", save=False)
    panel.set_theme_tokens(manager.current_tokens)

    assert panel.current_tokens is manager.current_tokens


def test_run_monitor_charts_render_non_null_pixmaps(app: object) -> None:
    assert QtCore is not None
    assert QtGui is not None
    from osw.gui.widgets.octave_figure_panel import OctaveFigureChart
    from osw.gui.widgets.residuals_chart import ResidualsChart

    for chart in (ResidualsChart(), OctaveFigureChart()):
        chart.resize(420, 220)
        pixmap = QtGui.QPixmap(chart.size())
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        chart.render(pixmap)
        assert not pixmap.isNull()


def test_main_window_uses_run_monitor_panel(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.top_region.objectName() == "oswTopRegion"
    assert window.workflow_stepper.objectName() == "oswWorkflowStepper"
    assert window.project_tree_panel.objectName() == "oswProjectTreePanel"
    assert window.central_viewport_panel.objectName() == "oswCentralViewportPanel"
    assert window.run_monitor.objectName() == "oswRunMonitorPanel"
    assert window.properties_panel.objectName() == "oswPropertiesPanel"
    assert window.statusBar().objectName() == "oswStatusBar"
