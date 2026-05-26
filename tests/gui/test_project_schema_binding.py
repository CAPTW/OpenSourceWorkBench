"""GUI binding tests for ProjectSchema-backed HeatSink_Flow data."""

from __future__ import annotations

import importlib.util
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _tree_labels(tree: object) -> list[str]:
    labels: list[str] = []

    def visit(item: object) -> None:
        labels.append(item.text(0))
        for index in range(item.childCount()):
            visit(item.child(index))

    for top_index in range(tree.topLevelItemCount()):
        visit(tree.topLevelItem(top_index))
    return labels


def test_main_window_starts_with_demo_project(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.current_project.metadata.name == "HeatSink_Flow"
    assert window.project_tree_panel.current_project() is window.current_project
    assert window.properties_panel.current_project() is window.current_project


def test_project_tree_panel_populates_from_project_schema(app: object) -> None:
    from osw.core.demo_project import create_heatsink_flow_demo_project
    from osw.gui.widgets.project_tree_panel import ProjectTreePanel

    project = create_heatsink_flow_demo_project()
    panel = ProjectTreePanel()
    panel.set_project(project)

    labels = _tree_labels(panel.tree)
    assert "HeatSink_Flow" in labels
    assert "heatsink.step" in labels
    assert "mesh.msh" in labels
    assert "run_0001" in labels
    assert "report.pdf" in labels
    assert panel.footer_label.text() == "Active Project: HeatSink_Flow"


def test_properties_panel_populates_from_project_schema(app: object) -> None:
    from osw.core.demo_project import create_heatsink_flow_demo_project
    from osw.gui.widgets.properties_panel import PropertiesPanel

    project = create_heatsink_flow_demo_project()
    panel = PropertiesPanel()
    panel.set_project(project)

    assert panel.material_section.current_material_library() == "builtin"
    assert panel.material_section.current_material() == "Aluminum 6061"
    assert panel.boundary_conditions_section.boundary_rows() == [
        {"Name": "inlet", "Type": "Velocity Inlet", "Value": "3.0 m/s"},
        {"Name": "outlet", "Type": "Pressure Outlet", "Value": "0 Pa"},
        {"Name": "wall_heatsink", "Type": "Wall (No Slip)", "Value": "—"},
        {"Name": "base_bottom", "Type": "Heat Flux", "Value": "1.0e5 W/m²"},
        {"Name": "symmetry", "Type": "Symmetry", "Value": "—"},
    ]
    assert panel.solver_settings_section.solver_settings()["Solver"] == "chtSolver"
    assert panel.solver_settings_section.solver_settings()["Convergence Tol."] == "1.0e-06"
    assert panel.report_preview_panel.report_title() == "HeatSink_Flow Simulation Report"


def test_baseline_object_names_remain_present_after_schema_binding(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.top_region.objectName() == "oswTopRegion"
    assert window.workflow_stepper.objectName() == "oswWorkflowStepper"
    assert window.project_tree_panel.objectName() == "oswProjectTreePanel"
    assert window.central_viewport_panel.objectName() == "oswCentralViewportPanel"
    assert window.run_monitor.objectName() == "oswRunMonitorPanel"
    assert window.properties_panel.objectName() == "oswPropertiesPanel"
    assert window.statusBar().objectName() == "oswStatusBar"


def test_theme_switching_still_works_after_project_binding(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    window.theme_manager.set_mode("dark", save=False)
    window.theme_manager.apply_to_app(app)
    window.theme_manager.set_mode("light", save=False)
    window.theme_manager.apply_to_app(app)
    window.theme_manager.set_mode("system", save=False)
    window.theme_manager.apply_to_app(app)

    assert window.current_project.metadata.name == "HeatSink_Flow"
