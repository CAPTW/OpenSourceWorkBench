"""Tests for the UI-007 right properties inspector panel."""

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


def test_properties_panel_contract_is_import_safe_without_pyside6() -> None:
    from osw.gui.widgets.boundary_conditions_table import (
        BOUNDARY_CONDITION_COLUMNS,
        DEMO_BOUNDARY_ROWS,
    )
    from osw.gui.widgets.material_section import (
        DEFAULT_MATERIAL,
        DEFAULT_MATERIAL_LIBRARY,
        MATERIAL_LIBRARY_OPTIONS,
        MATERIAL_OPTIONS,
    )
    from osw.gui.widgets.plugins_section import DEMO_PLUGIN_ROWS
    from osw.gui.widgets.properties_panel import PROPERTY_TAB_TITLES
    from osw.gui.widgets.solver_settings_section import DEMO_SOLVER_SETTINGS

    assert PROPERTY_TAB_TITLES == ("Properties", "Materials", "BCS", "Advanced")
    assert DEFAULT_MATERIAL_LIBRARY == "builtin"
    assert DEFAULT_MATERIAL == "Aluminum 6061"
    assert MATERIAL_LIBRARY_OPTIONS == ("builtin", "project", "user")
    assert "Aluminum 6061" in MATERIAL_OPTIONS
    assert BOUNDARY_CONDITION_COLUMNS == ("Name", "Type", "Value")
    assert DEMO_BOUNDARY_ROWS == (
        ("inlet", "Velocity Inlet", "3.0 m/s"),
        ("outlet", "Pressure Outlet", "0 Pa"),
        ("wall_heatsink", "Wall (No Slip)", "—"),
        ("base_bottom", "Heat Flux", "1.0e5 W/m²"),
        ("symmetry", "Symmetry", "—"),
    )
    assert DEMO_SOLVER_SETTINGS == {
        "Solver": "chtSolver",
        "Time Scheme": "Steady-State",
        "Linear Solver": "GMRES",
        "Preconditioner": "AMG",
        "Convergence Tol.": "1.0e-06",
        "Advanced Options": "collapsed",
    }
    assert DEMO_PLUGIN_ROWS == (
        ("Octave / MATLAB Interface", True),
        ("ParaView Catalyst", True),
        ("Mesh Quality Checker", True),
        ("Report Generator", True),
    )


@pytest.fixture
def app() -> object:
    if not PYSIDE6_AVAILABLE:
        pytest.skip("PySide6 optional GUI extra is not installed.")
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_properties_panel_instantiates_with_reference_tabs(app: object) -> None:
    from osw.gui.widgets.properties_panel import PROPERTY_TAB_TITLES, PropertiesPanel

    panel = PropertiesPanel()

    assert panel.objectName() == "oswPropertiesPanel"
    assert panel.tabs.objectName() == "oswPropertiesTabs"
    assert panel.tab_titles() == list(PROPERTY_TAB_TITLES)
    assert panel.tabs.currentIndex() == 0
    assert panel.tabs.tabText(panel.tabs.currentIndex()) == "Properties"
    assert panel.properties_tab.objectName() == "oswPropertiesTabProperties"
    assert panel.materials_tab.objectName() == "oswPropertiesTabMaterials"
    assert panel.bcs_tab.objectName() == "oswPropertiesTabBCS"
    assert panel.advanced_tab.objectName() == "oswPropertiesTabAdvanced"


def test_material_section_contains_reference_values(app: object) -> None:
    from osw.gui.widgets.properties_panel import PropertiesPanel

    panel = PropertiesPanel()
    section = panel.material_section

    assert section.objectName() == "oswMaterialSection"
    assert section.title() == "MATERIAL"
    assert section.library_combo.objectName() == "oswMaterialLibraryCombo"
    assert section.material_combo.objectName() == "oswMaterialCombo"
    assert section.edit_button.objectName() == "oswEditMaterialButton"
    assert section.current_material_library() == "builtin"
    assert section.current_material() == "Aluminum 6061"
    assert section.edit_button.text() == "Edit Material..."


def test_boundary_conditions_table_contains_reference_rows_and_buttons(app: object) -> None:
    from osw.gui.widgets.boundary_conditions_table import DEMO_BOUNDARY_ROWS
    from osw.gui.widgets.properties_panel import PropertiesPanel

    panel = PropertiesPanel()
    section = panel.boundary_conditions_section

    assert section.objectName() == "oswBoundaryConditionsSection"
    assert section.table.objectName() == "oswBoundaryConditionsTable"
    assert section.column_labels() == ["Name", "Type", "Value"]
    assert section.boundary_rows() == [
        {"Name": name, "Type": kind, "Value": value}
        for name, kind, value in DEMO_BOUNDARY_ROWS
    ]
    assert section.add_button.objectName() == "oswBoundaryAddButton"
    assert section.edit_button.objectName() == "oswBoundaryEditButton"
    assert section.copy_button.objectName() == "oswBoundaryCopyButton"
    assert section.remove_button.objectName() == "oswBoundaryRemoveButton"
    assert [button.text() for button in section.action_buttons()] == [
        "Add",
        "Edit",
        "Copy",
        "Remove",
    ]


def test_solver_settings_section_contains_reference_values(app: object) -> None:
    from osw.gui.widgets.properties_panel import PropertiesPanel

    panel = PropertiesPanel()
    section = panel.solver_settings_section

    assert section.objectName() == "oswSolverSettingsSection"
    assert section.solver_combo.objectName() == "oswSolverCombo"
    assert section.time_scheme_combo.objectName() == "oswTimeSchemeCombo"
    assert section.linear_solver_combo.objectName() == "oswLinearSolverCombo"
    assert section.preconditioner_combo.objectName() == "oswPreconditionerCombo"
    assert section.tolerance_edit.objectName() == "oswConvergenceToleranceEdit"
    assert section.advanced_toggle.objectName() == "oswAdvancedOptionsToggle"
    assert section.solver_settings() == {
        "Solver": "chtSolver",
        "Time Scheme": "Steady-State",
        "Linear Solver": "GMRES",
        "Preconditioner": "AMG",
        "Convergence Tol.": "1.0e-06",
        "Advanced Options": "collapsed",
    }
    assert "Advanced Options" in section.advanced_toggle.text()


def test_plugins_section_contains_reference_enabled_rows(app: object) -> None:
    from osw.gui.widgets.properties_panel import PropertiesPanel

    panel = PropertiesPanel()
    section = panel.plugins_section

    assert section.objectName() == "oswPluginsSection"
    assert section.plugin_rows() == [
        {"name": "Octave / MATLAB Interface", "enabled": True},
        {"name": "ParaView Catalyst", "enabled": True},
        {"name": "Mesh Quality Checker", "enabled": True},
        {"name": "Report Generator", "enabled": True},
    ]
    assert section.plugin_widgets["Octave / MATLAB Interface"].objectName() == (
        "oswPluginOctaveMatlab"
    )
    assert section.plugin_widgets["ParaView Catalyst"].objectName() == (
        "oswPluginParaViewCatalyst"
    )
    assert section.plugin_widgets["Mesh Quality Checker"].objectName() == (
        "oswPluginMeshQualityChecker"
    )
    assert section.plugin_widgets["Report Generator"].objectName() == (
        "oswPluginReportGenerator"
    )
    assert section.manage_report_button.objectName() == "oswManageReportButton"
    assert section.manage_report_button.text() == "Manage Report..."


def test_properties_panel_accepts_dark_and_light_tokens(app: object) -> None:
    from osw.gui.theme import ThemeManager
    from osw.gui.widgets.properties_panel import PropertiesPanel

    panel = PropertiesPanel()
    manager = ThemeManager(auto_load=False)

    manager.set_mode("dark", save=False)
    panel.set_theme_tokens(manager.current_tokens)
    manager.set_mode("light", save=False)
    panel.set_theme_tokens(manager.current_tokens)

    assert panel.current_tokens is manager.current_tokens


def test_main_window_uses_properties_panel(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    assert window.top_region.objectName() == "oswTopRegion"
    assert window.workflow_stepper.objectName() == "oswWorkflowStepper"
    assert window.project_tree_panel.objectName() == "oswProjectTreePanel"
    assert window.central_viewport_panel.objectName() == "oswCentralViewportPanel"
    assert window.run_monitor.objectName() == "oswRunMonitorPanel"
    assert window.properties_panel.objectName() == "oswPropertiesPanel"
    assert window.statusBar().objectName() == "oswStatusBar"
