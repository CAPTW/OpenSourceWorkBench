"""Right properties inspector panel for the OpenSolver Workbench visual shell."""

from __future__ import annotations

from typing import Any

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.project_schema import Project
from osw.gui.qt_compat import PySide6UnavailableError, pyside6_missing_message
from osw.gui.theme_tokens import DARK_TOKENS, ThemeTokens
from osw.gui.widgets.boundary_conditions_table import BoundaryConditionsSection
from osw.gui.widgets.material_section import MaterialSection
from osw.gui.widgets.plugins_section import PluginsSection
from osw.gui.widgets.report_preview_panel import ReportPreviewPanel
from osw.gui.widgets.solver_settings_section import SolverSettingsSection

try:
    from PySide6 import QtWidgets
except ModuleNotFoundError:
    QtWidgets = None

_BaseWidget: Any = QtWidgets.QWidget if QtWidgets is not None else object

PROPERTY_TAB_TITLES = ("Properties", "Materials", "BCS", "Advanced")
PROPERTY_TAB_OBJECT_NAMES = {
    "Properties": "oswPropertiesTabProperties",
    "Materials": "oswPropertiesTabMaterials",
    "BCS": "oswPropertiesTabBCS",
    "Advanced": "oswPropertiesTabAdvanced",
}

# Backward-compatible name from UI-002 placeholder tests.
TAB_TITLES = PROPERTY_TAB_TITLES


class PropertiesPanel(_BaseWidget):
    """Right inspector with compact tabbed mock settings sections."""

    def __init__(self, parent: object | None = None) -> None:
        if QtWidgets is None:
            raise PySide6UnavailableError(pyside6_missing_message())

        super().__init__(parent)
        self.setObjectName("oswPropertiesPanel")
        self.setMinimumWidth(390)
        self._tokens = DARK_TOKENS
        self._selection = "HeatSink_Flow"
        self._current_project: Project | None = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setObjectName("oswPropertiesTabs")

        self.properties_tab = self._make_tab("Properties")
        self.materials_tab = self._make_tab("Materials")
        self.bcs_tab = self._make_tab("BCS")
        self.advanced_tab = self._make_tab("Advanced")
        self._build_properties_tab()
        self._build_placeholder_tab(
            self.materials_tab,
            "Material editor will be available in a later implementation pass.",
        )
        self._build_placeholder_tab(
            self.bcs_tab,
            "Boundary condition editing is shown in the Properties tab.",
        )
        self._build_placeholder_tab(
            self.advanced_tab,
            "Advanced solver options are collapsed for this visual shell.",
        )

        for title, tab in (
            ("Properties", self.properties_tab),
            ("Materials", self.materials_tab),
            ("BCS", self.bcs_tab),
            ("Advanced", self.advanced_tab),
        ):
            self.tabs.addTab(tab, title)

        self.tabs.setCurrentIndex(0)
        layout.addWidget(self.tabs, 1)
        self.set_theme_tokens(self._tokens)
        self.set_project(create_heatsink_flow_demo_project())

    @property
    def current_tokens(self) -> ThemeTokens:
        return self._tokens

    def tab_titles(self) -> list[str]:
        return [self.tabs.tabText(index) for index in range(self.tabs.count())]

    def row_value(self, name: str) -> str:
        if name == "Selection":
            return self._selection
        if name == "Workflow step":
            return _workflow_step_for_selection(self._selection)
        return ""

    def set_node_selection(self, selection: str) -> None:
        self._selection = selection or "HeatSink_Flow"

    def set_project(self, project: Project) -> None:
        self._current_project = project
        self.refresh_from_project(project)

    def current_project(self) -> Project | None:
        return self._current_project

    def refresh_from_project(self, project: Project) -> None:
        material = project.materials[0] if project.materials else None
        if material is not None:
            self.material_section.set_material_library(material.library or "project")
            self.material_section.set_material(material.name)

        physics = project.primary_physics
        if physics is not None:
            self.boundary_conditions_section.set_boundary_rows(
                [
                    {
                        "Name": boundary.name,
                        "Type": boundary.type or boundary.kind,
                        "Value": boundary.value or _values_summary(boundary.values),
                    }
                    for boundary in physics.boundary_conditions
                ]
            )

        solver = project.solver_config
        if solver is not None:
            self.solver_settings_section.set_solver(solver.solver or solver.name)
            self.solver_settings_section.set_time_scheme(solver.time_scheme)
            self.solver_settings_section.set_linear_solver(solver.linear_solver)
            self.solver_settings_section.set_preconditioner(solver.preconditioner)
            self.solver_settings_section.set_convergence_tolerance(
                _format_tolerance(solver.convergence_tolerance)
            )

        self.report_preview_panel.set_report_title(project.report.title)
        if project.report.run_label:
            self.report_preview_panel.set_run_label(project.report.run_label)
        if project.report.sections:
            self.report_preview_panel.set_sections(project.report.sections)

    def set_properties(self, _properties: dict[str, str]) -> None:
        return

    def reset_demo_data(self) -> None:
        self.material_section.set_material_library("builtin")
        self.material_section.set_material("Aluminum 6061")
        self.boundary_conditions_section.reset_demo_boundaries()
        self.solver_settings_section.set_solver("chtSolver")
        self.solver_settings_section.set_convergence_tolerance("1.0e-06")
        for row in self.plugins_section.plugin_rows():
            self.plugins_section.set_plugin_enabled(str(row["name"]), True)

    def set_theme_tokens(self, tokens: ThemeTokens) -> None:
        self._tokens = tokens
        for child in (
            self.material_section,
            self.boundary_conditions_section,
            self.solver_settings_section,
            self.plugins_section,
            self.report_preview_panel,
        ):
            child.set_theme_tokens(tokens)
        self.setStyleSheet(
            "QWidget#oswPropertiesPanel {"
            f"background-color: {tokens.bg_panel};"
            f"border-left: 1px solid {tokens.border};"
            "}"
            "QTabWidget#oswPropertiesTabs::pane {"
            f"border: 1px solid {tokens.border};"
            f"background-color: {tokens.bg_panel};"
            "}"
            "QTabWidget#oswPropertiesTabs QTabBar::tab {"
            f"background-color: {tokens.bg_header};"
            f"color: {tokens.text_secondary};"
            f"border: 1px solid {tokens.border};"
            "padding: 5px 8px;"
            "}"
            "QTabWidget#oswPropertiesTabs QTabBar::tab:selected {"
            f"background-color: {tokens.bg_panel_alt};"
            f"color: {tokens.text_primary};"
            f"border-bottom: 2px solid {tokens.primary};"
            "}"
            "QLabel[oswPlaceholder='true'] {"
            f"color: {tokens.text_muted};"
            f"background-color: {tokens.bg_panel_alt};"
            f"border: 1px solid {tokens.border};"
            "border-radius: 4px;"
            "padding: 8px;"
            "}"
        )

    def _make_tab(self, title: str) -> object:
        tab = QtWidgets.QWidget(self.tabs)
        tab.setObjectName(PROPERTY_TAB_OBJECT_NAMES[title])
        return tab

    def _build_properties_tab(self) -> None:
        tab_layout = QtWidgets.QVBoxLayout(self.properties_tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)

        scroll = QtWidgets.QScrollArea(self.properties_tab)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        content = QtWidgets.QWidget(scroll)
        content_layout = QtWidgets.QVBoxLayout(content)
        content_layout.setContentsMargins(8, 8, 8, 8)
        content_layout.setSpacing(8)

        self.material_section = MaterialSection(content)
        self.boundary_conditions_section = BoundaryConditionsSection(content)
        self.solver_settings_section = SolverSettingsSection(content)
        self.plugins_section = PluginsSection(content)
        self.report_preview_panel = ReportPreviewPanel(content)
        for section in (
            self.material_section,
            self.boundary_conditions_section,
            self.solver_settings_section,
            self.plugins_section,
            self.report_preview_panel,
        ):
            content_layout.addWidget(section)
        content_layout.addStretch(1)
        scroll.setWidget(content)
        tab_layout.addWidget(scroll)

    def _build_placeholder_tab(self, tab: object, message: str) -> None:
        layout = QtWidgets.QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        label = QtWidgets.QLabel(message, tab)
        label.setWordWrap(True)
        label.setProperty("oswPlaceholder", True)
        layout.addWidget(label)
        layout.addStretch(1)


def _workflow_step_for_selection(selection: str) -> str:
    return {
        "Geometry": "Import or preview standard geometry",
        "Mesh": "Import or generate mesh",
        "Physics": "Configure units, materials, and boundary data",
        "Solvers": "Prepare bounded solver workflows",
        "Scripts": "Preview script data safely",
        "Results": "Inspect structured result datasets",
        "Reports": "Export an HTML report",
    }.get(selection, "Run")


def _values_summary(values: dict[str, object]) -> str:
    if not values:
        return "—"
    return ", ".join(f"{key}={value}" for key, value in values.items())


def _format_tolerance(value: object) -> str:
    try:
        numeric = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.1e}"
