"""Tests for UI-008 report preview and status bar widgets."""

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


def test_report_preview_and_status_contracts_are_import_safe_without_pyside6() -> None:
    from osw.gui.widgets.report_preview_panel import (
        DEFAULT_REPORT_RUN_LABEL,
        DEFAULT_REPORT_SECTIONS,
        DEFAULT_REPORT_TITLE,
    )
    from osw.gui.widgets.status_bar import (
        DEFAULT_CORE_USAGE,
        DEFAULT_MEMORY_USAGE,
        DEFAULT_READY_TEXT,
        DEFAULT_SOLVER_NAME,
    )

    assert DEFAULT_REPORT_TITLE == "HeatSink_Flow Simulation Report"
    assert DEFAULT_REPORT_RUN_LABEL == "Run 0001"
    assert DEFAULT_REPORT_SECTIONS == ("Overview", "Key Results", "Summary")
    assert DEFAULT_SOLVER_NAME == "chtSolver"
    assert DEFAULT_MEMORY_USAGE == (6.2, 15.9)
    assert DEFAULT_CORE_USAGE == (12, 16)
    assert DEFAULT_READY_TEXT == "Ready"


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_report_preview_panel_contains_reference_content(app: object) -> None:
    from osw.gui.widgets.report_preview_panel import ReportPreviewPanel

    panel = ReportPreviewPanel()

    assert panel.objectName() == "oswReportPreviewPanel"
    assert panel.header_label.objectName() == "oswReportPreviewHeader"
    assert panel.title_label.objectName() == "oswReportPreviewTitle"
    assert panel.run_label_widget.objectName() == "oswReportPreviewRunLabel"
    assert panel.sections_list.objectName() == "oswReportPreviewSections"
    assert panel.thumbnail.objectName() == "oswReportPreviewThumbnail"
    assert panel.export_button.objectName() == "oswExportReportButton"
    assert panel.report_title() == "HeatSink_Flow Simulation Report"
    assert panel.run_label() == "Run 0001"
    assert panel.report_sections() == ["Overview", "Key Results", "Summary"]
    assert panel.export_button.text() == "Export Report..."


def test_report_preview_export_button_is_safe_placeholder(app: object) -> None:
    from osw.gui.widgets.report_preview_panel import ReportPreviewPanel

    panel = ReportPreviewPanel()

    panel.export_button.click()
    assert panel.last_export_request == "placeholder"


def test_report_preview_panel_accepts_real_report_summary(app: object) -> None:
    from osw.core.demo_project import create_heatsink_flow_demo_project
    from osw.gui.widgets.report_preview_panel import ReportPreviewPanel
    from osw.post.report_sections import build_report_summary

    panel = ReportPreviewPanel()
    summary = build_report_summary(create_heatsink_flow_demo_project())

    panel.set_report_summary(summary)

    assert panel.report_title() == "HeatSink_Flow Simulation Report"
    assert panel.run_label() == "Run 0001"
    assert "Project Metadata" in panel.report_sections()
    assert "Figures:" in panel.report_status_text()
    assert panel.last_report_summary is summary


def test_status_bar_contains_reference_values_and_ratios(app: object) -> None:
    from osw.gui.widgets.status_bar import OswStatusBar

    status_bar = OswStatusBar()

    assert status_bar.objectName() == "oswStatusBar"
    assert status_bar.solver_label.objectName() == "oswStatusSolverLabel"
    assert status_bar.solver_indicator.objectName() == "oswStatusSolverIndicator"
    assert status_bar.memory_label.objectName() == "oswStatusMemoryLabel"
    assert status_bar.memory_bar.objectName() == "oswStatusMemoryBar"
    assert status_bar.cores_label.objectName() == "oswStatusCoresLabel"
    assert status_bar.cores_bar.objectName() == "oswStatusCoresBar"
    assert status_bar.ready_label.objectName() == "oswStatusReadyLabel"
    assert status_bar.ready_indicator.objectName() == "oswStatusReadyIndicator"
    assert status_bar.solver_name() == "chtSolver"
    assert status_bar.memory_usage() == (6.2, 15.9)
    assert status_bar.core_usage() == (12, 16)
    assert status_bar.ready_text() == "Ready"
    assert status_bar.memory_bar.ratio() == pytest.approx(6.2 / 15.9)
    assert status_bar.cores_bar.ratio() == pytest.approx(12 / 16)


def test_report_preview_and_status_accept_dark_and_light_tokens(app: object) -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.widgets.report_preview_panel import ReportPreviewPanel
    from osw.gui.widgets.status_bar import OswStatusBar

    manager = ThemeManager(auto_load=False)
    report_preview = ReportPreviewPanel()
    status_bar = OswStatusBar()

    manager.set_mode("dark", save=False)
    report_preview.set_theme_tokens(manager.current_tokens)
    status_bar.set_theme_tokens(manager.current_tokens)
    manager.set_mode("light", save=False)
    report_preview.set_theme_tokens(manager.current_tokens)
    status_bar.set_theme_tokens(manager.current_tokens)

    assert report_preview.current_tokens is manager.current_tokens
    assert status_bar.current_tokens is manager.current_tokens


def test_properties_panel_contains_report_preview(app: object) -> None:
    from osw.gui.widgets.properties_panel import PropertiesPanel

    panel = PropertiesPanel()

    assert panel.report_preview_panel.objectName() == "oswReportPreviewPanel"
    assert panel.report_preview_panel.report_title() == "HeatSink_Flow Simulation Report"
    assert panel.report_preview_panel.run_label() == "Run 0001"


def test_main_window_contains_enriched_status_bar_and_major_regions(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.top_region.objectName() == "oswTopRegion"
    assert window.workflow_stepper.objectName() == "oswWorkflowStepper"
    assert window.project_tree_panel.objectName() == "oswProjectTreePanel"
    assert window.central_viewport_panel.objectName() == "oswCentralViewportPanel"
    assert window.run_monitor.objectName() == "oswRunMonitorPanel"
    assert window.properties_panel.objectName() == "oswPropertiesPanel"
    assert window.statusBar().objectName() == "oswStatusBar"
    assert window.statusBar().solver_name() == "chtSolver"
    assert "Generate Report" in window.menu_actions
    assert "Export Report" in window.menu_actions


def test_thumbnail_and_status_bar_render_non_null_pixmaps(app: object) -> None:
    assert QtCore is not None
    assert QtGui is not None
    from osw.gui.widgets.report_preview_panel import ReportPreviewThumbnail
    from osw.gui.widgets.status_bar import OswStatusBar

    for widget in (ReportPreviewThumbnail(), OswStatusBar()):
        widget.resize(320, 80)
        pixmap = QtGui.QPixmap(widget.size())
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        widget.render(pixmap)
        assert not pixmap.isNull()
