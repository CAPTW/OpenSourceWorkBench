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
        self._mesh_by_label: dict[str, object] = {}
        self._script_by_label: dict[str, object] = {}
        self._curve_by_label: dict[str, object] = {}
        self._setup_properties: dict[str, str] = {}
        self._mesh_diagnostics_properties: dict[str, str] = {}

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
        if name in self._setup_properties:
            return self._setup_properties[name]
        if name in self._mesh_diagnostics_properties:
            return self._mesh_diagnostics_properties[name]
        mesh = self._selected_mesh_ref()
        if mesh is not None:
            return _mesh_row_value(mesh, name)
        script = self._selected_script_ref()
        if script is not None:
            return _script_row_value(script, name)
        curve = self._selected_boundary_curve()
        if curve is not None:
            return _curve_row_value(curve, name)
        return ""

    def set_node_selection(self, selection: str) -> None:
        self._selection = selection or "HeatSink_Flow"

    def _selected_mesh_ref(self) -> object | None:
        return self._mesh_by_label.get(self._selection)

    def _selected_script_ref(self) -> object | None:
        return self._script_by_label.get(self._selection)

    def _selected_boundary_curve(self) -> object | None:
        return self._curve_by_label.get(self._selection)

    def set_project(self, project: Project) -> None:
        self._current_project = project
        self.refresh_from_project(project)

    def current_project(self) -> Project | None:
        return self._current_project

    def refresh_from_project(self, project: Project) -> None:
        self._mesh_by_label = {_mesh_label(mesh): mesh for mesh in project.mesh_refs}
        self._script_by_label = {_script_label(script): script for script in project.script_refs}
        self._curve_by_label = {_curve_label(curve): curve for curve in project.boundary_curves}
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
                        "Value": _boundary_value_summary(boundary),
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
        self._setup_properties = {str(key): str(value) for key, value in _properties.items()}
        self._refresh_setup_properties_table()

    def set_setup_record(
        self,
        record: object,
        *,
        status: object | None,
        target_name: str = "",
        material_name: str = "",
        adapter_readiness: str = "NOT_EVALUATED",
    ) -> None:
        """Inspect persisted typed setup data without making it editable here."""

        self._setup_properties = _setup_property_rows(
            record,
            status=status,
            target_name=target_name,
            material_name=material_name,
            adapter_readiness=adapter_readiness,
        )
        self._refresh_setup_properties_table()

    def clear_setup_record(self) -> None:
        self._setup_properties = {}
        self._refresh_setup_properties_table()

    def setup_property_rows(self) -> dict[str, str]:
        return dict(self._setup_properties)

    def set_mesh_diagnostics_view_model(self, view_model: object) -> None:
        cell_types = (
            ", ".join(
                f"{name}:{count}"
                for name, count in getattr(view_model, "cell_type_distribution", ())
            )
            or "none"
        )
        diagnostics = tuple(getattr(view_model, "diagnostics", ()) or ())
        display_range = tuple(getattr(view_model, "display_range", (-1.0, 1.0)))
        self._mesh_diagnostics_properties = {
            "Status": str(getattr(view_model, "status", "idle")),
            "Metric": str(getattr(view_model, "metric_label", "Scaled Jacobian")),
            "Metric ID": str(getattr(view_model, "metric_schema", "")),
            "Provider": str(getattr(view_model, "provider_schema", "")),
            "Provider version": str(getattr(view_model, "provider_version", "")),
            "Mesh fingerprint": str(getattr(view_model, "mesh_fingerprint", ""))[:16],
            "Quality digest": str(getattr(view_model, "digest", "")),
            "Nodes": str(getattr(view_model, "node_count", 0)),
            "Cells": str(getattr(view_model, "cell_count", 0)),
            "Blocks": str(getattr(view_model, "block_count", 0)),
            "Cell types": cell_types,
            "Surface cells": str(getattr(view_model, "surface_cell_count", 0)),
            "Volume cells": str(getattr(view_model, "volume_cell_count", 0)),
            "Bounds": str(getattr(view_model, "bounding_box_text", "unavailable")),
            "Extents": str(getattr(view_model, "extents_text", "unavailable")),
            "Diagonal": _diagnostic_number(getattr(view_model, "diagonal", None)),
            "Referenced points": str(getattr(view_model, "referenced_point_count", 0)),
            "Orphan points": str(getattr(view_model, "orphan_point_count", 0)),
            "Covered": str(getattr(view_model, "covered_count", 0)),
            "Coverage ratio": (f"{100.0 * float(getattr(view_model, 'coverage_ratio', 0.0)):.1f}%"),
            "Bad": str(getattr(view_model, "bad_count", 0)),
            "Inverted": str(getattr(view_model, "inverted_count", 0)),
            "Degenerate": str(getattr(view_model, "degenerate_count", 0)),
            "Threshold bad": str(getattr(view_model, "threshold_bad_count", 0)),
            "Acceptable": str(getattr(view_model, "acceptable_count", 0)),
            "Invalid": str(getattr(view_model, "invalid_count", 0)),
            "Uncovered": str(getattr(view_model, "unsupported_count", 0)),
            "Threshold": f"{float(getattr(view_model, 'threshold', 0.0)):g}",
            "Range mode": str(getattr(view_model, "range_mode", "auto")),
            "Display range": f"{display_range[0]:g} .. {display_range[1]:g}",
            "Minimum": _diagnostic_number(getattr(view_model, "minimum", None)),
            "Maximum": _diagnostic_number(getattr(view_model, "maximum", None)),
            "Mean": _diagnostic_number(getattr(view_model, "mean", None)),
            "Median": _diagnostic_number(getattr(view_model, "median", None)),
            "Population stddev": _diagnostic_number(getattr(view_model, "population_stddev", None)),
            "p05 / p25 / p75 / p95": " / ".join(
                _diagnostic_number(getattr(view_model, name, None))
                for name in ("p05", "p25", "p75", "p95")
            ),
            "Diagnostic": diagnostics[-1] if diagnostics else "none",
        }
        self._refresh_mesh_diagnostics_properties_table()

    def clear_mesh_diagnostics_view_model(self) -> None:
        self._mesh_diagnostics_properties = {}
        self._refresh_mesh_diagnostics_properties_table()

    def mesh_diagnostics_property_rows(self) -> dict[str, str]:
        return dict(self._mesh_diagnostics_properties)

    def _refresh_setup_properties_table(self) -> None:
        table = self.setup_properties_table
        table.clear()
        for key, value in self._setup_properties.items():
            item = QtWidgets.QTreeWidgetItem((key, value))
            item.setToolTip(1, value)
            table.addTopLevelItem(item)
        self.setup_properties_group.setVisible(bool(self._setup_properties))

    def _refresh_mesh_diagnostics_properties_table(self) -> None:
        table = self.mesh_diagnostics_properties_table
        table.clear()
        for key, value in self._mesh_diagnostics_properties.items():
            item = QtWidgets.QTreeWidgetItem((key, value))
            item.setToolTip(1, value)
            table.addTopLevelItem(item)
        self.mesh_diagnostics_properties_group.setVisible(bool(self._mesh_diagnostics_properties))

    def reset_demo_data(self) -> None:
        self.material_section.set_material_library("builtin")
        self.material_section.set_material("Aluminum 6061")
        self.boundary_conditions_section.reset_demo_boundaries()
        self.solver_settings_section.set_solver("chtSolver")
        self.solver_settings_section.set_convergence_tolerance("1.0e-06")
        for row in self.plugins_section.plugin_rows():
            self.plugins_section.set_plugin_enabled(str(row["name"]), True)

    def set_plugin_registry(self, registry: object | None) -> None:
        self.plugins_section.set_plugin_registry(registry)

    def set_plugin_health_map(self, health_by_id: object | None) -> None:
        if isinstance(health_by_id, dict):
            self.plugins_section.set_plugin_health_map(health_by_id)
        else:
            self.plugins_section.set_plugin_health_map({})

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
        self.mesh_diagnostics_properties_group = QtWidgets.QGroupBox(
            "MESH DIAGNOSTICS",
            content,
        )
        self.mesh_diagnostics_properties_group.setObjectName("oswMeshDiagnosticsPropertiesSection")
        diagnostics_layout = QtWidgets.QVBoxLayout(self.mesh_diagnostics_properties_group)
        self.mesh_diagnostics_properties_table = QtWidgets.QTreeWidget(
            self.mesh_diagnostics_properties_group
        )
        self.mesh_diagnostics_properties_table.setObjectName("oswMeshDiagnosticsPropertiesTable")
        self.mesh_diagnostics_properties_table.setColumnCount(2)
        self.mesh_diagnostics_properties_table.setHeaderLabels(("Property", "Value"))
        self.mesh_diagnostics_properties_table.header().setStretchLastSection(True)
        self.mesh_diagnostics_properties_table.setRootIsDecorated(False)
        diagnostics_layout.addWidget(self.mesh_diagnostics_properties_table)
        self.mesh_diagnostics_properties_group.setVisible(False)
        self.setup_properties_group = QtWidgets.QGroupBox(
            "SOLVER SETUP",
            content,
        )
        self.setup_properties_group.setObjectName("oswSetupPropertiesSection")
        self.setup_properties_group.setAccessibleName("Solver setup properties")
        setup_layout = QtWidgets.QVBoxLayout(self.setup_properties_group)
        self.setup_properties_table = QtWidgets.QTreeWidget(self.setup_properties_group)
        self.setup_properties_table.setObjectName("oswSetupPropertiesTable")
        self.setup_properties_table.setAccessibleName(
            "Typed solver setup parameters and validation status"
        )
        self.setup_properties_table.setColumnCount(2)
        self.setup_properties_table.setHeaderLabels(("Property", "Value"))
        self.setup_properties_table.header().setStretchLastSection(True)
        self.setup_properties_table.setRootIsDecorated(False)
        setup_layout.addWidget(self.setup_properties_table)
        self.setup_properties_group.setVisible(False)
        for section in (
            self.mesh_diagnostics_properties_group,
            self.setup_properties_group,
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


def _boundary_value_summary(boundary: object) -> str:
    curve_id = str(getattr(boundary, "curve_id", "") or "")
    if curve_id:
        return f"Curve: {curve_id}"
    return str(getattr(boundary, "value", "") or _values_summary(getattr(boundary, "values", {})))


def _format_tolerance(value: object) -> str:
    try:
        numeric = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric:.1e}"


def _setup_property_rows(
    record: object,
    *,
    status: object | None,
    target_name: str,
    material_name: str,
    adapter_readiness: str,
) -> dict[str, str]:
    kind = str(
        getattr(getattr(record, "setup_kind", ""), "value", "")
        or getattr(record, "setup_kind", "")
        or ""
    )
    target_id = str(getattr(record, "target_selection_id", "") or "")
    reason_code = str(getattr(status, "reason_code", "NOT_EVALUATED"))
    rows = {
        "Setup ID": str(getattr(record, "id", "") or ""),
        "Name": str(getattr(record, "name", "") or ""),
        "Kind": kind,
        "Target NamedSelection": target_name or target_id,
        "Target ID": target_id,
        "Enabled": str(bool(getattr(record, "enabled", True))),
        "Validity": reason_code,
        "Status reason": str(getattr(status, "message", "Setup record not evaluated.")),
        "Adapter readiness": str(adapter_readiness),
    }
    material_id = str(getattr(record, "material_id", "") or "")
    if material_id:
        rows["Material"] = material_name or material_id
        rows["Material ID"] = material_id
    dofs = tuple(getattr(record, "translational_dofs", ()) or ())
    if dofs:
        rows["Constrained DOFs"] = ", ".join(f"U{'XYZ'[item - 1]}" for item in dofs)
    components = tuple(getattr(record, "components", ()) or ())
    if components:
        for axis, component in zip(("UX", "UY", "UZ"), components, strict=True):
            rows[axis] = "free" if component is None else _quantity_text(component)
    magnitude = getattr(record, "magnitude", None)
    if magnitude is not None:
        rows["Magnitude"] = _quantity_text(magnitude)
        direction = tuple(getattr(record, "direction", ()) or ())
        rows["Direction"] = ", ".join(f"{float(value):g}" for value in direction)
        rows["Coordinate system"] = str(getattr(record, "coordinate_system", "GLOBAL"))
        rows["Application mode"] = str(getattr(record, "application_mode", "PER_NODE"))
    value = getattr(record, "value", None)
    if value is not None:
        label = {
            "pressure": "Pressure",
            "temperature": "Temperature",
            "heat_flux": "Heat flux",
        }.get(kind, "Value")
        rows[label] = _quantity_text(value)
    return rows


def _quantity_text(quantity: object) -> str:
    value = float(getattr(quantity, "value", 0.0))
    unit = str(getattr(quantity, "unit", "") or "")
    return f"{value:g} {unit}".strip()


def _mesh_label(mesh: object) -> str:
    name = str(getattr(mesh, "name", "") or "")
    path = str(getattr(mesh, "path", "") or "")
    if name:
        return name
    if path:
        from pathlib import Path

        return Path(path).name
    return str(getattr(mesh, "id", ""))


def _mesh_info(mesh: object) -> dict[str, object]:
    info = getattr(mesh, "mesh_info", None)
    if isinstance(info, dict):
        return info
    metadata = getattr(mesh, "metadata", {})
    if isinstance(metadata, dict) and isinstance(metadata.get("mesh_info"), dict):
        return dict(metadata["mesh_info"])
    return {}


def _mesh_row_value(mesh: object, name: str) -> str:
    info = _mesh_info(mesh)
    if name in {"Mesh format", "Format"}:
        return str(getattr(mesh, "format", "") or info.get("format", ""))
    if name in {"Nodes", "Node count"}:
        return _mesh_count(getattr(mesh, "node_count", None), info, "node_count", "nodes")
    if name in {"Elements", "Element count", "Cells"}:
        return _mesh_count(getattr(mesh, "cell_count", None), info, "element_count", "elements")
    if name == "Cell types":
        cell_types = info.get("cell_types", ())
        if not cell_types and isinstance(info.get("cell_blocks"), list):
            cell_types = [
                str(block.get("cell_type", ""))
                for block in info["cell_blocks"]
                if isinstance(block, dict) and block.get("cell_type")
            ]
        if isinstance(cell_types, list | tuple):
            return ", ".join(str(item) for item in cell_types) or "none"
        return str(cell_types or "none")
    if name == "Bounds":
        bounds = info.get("bounds") or info.get("bounding_box")
        if isinstance(bounds, dict):
            minimum = bounds.get("minimum") or [
                bounds.get("min_x", 0.0),
                bounds.get("min_y", 0.0),
                bounds.get("min_z", 0.0),
            ]
            maximum = bounds.get("maximum") or [
                bounds.get("max_x", 0.0),
                bounds.get("max_y", 0.0),
                bounds.get("max_z", 0.0),
            ]
            return f"{minimum} -> {maximum}"
        return ""
    if name in {"Quality", "Quality summary"}:
        return str(getattr(mesh, "quality_summary", "") or "")
    if name == "Mesh status":
        return str(getattr(mesh, "status", "") or "")
    return ""


def _mesh_count(value: object, info: dict[str, object], *keys: str) -> str:
    if value not in (None, ""):
        return str(value)
    for key in keys:
        if info.get(key) not in (None, ""):
            return str(info[key])
    return ""


def _script_label(script: object) -> str:
    name = str(getattr(script, "name", "") or "")
    path = str(getattr(script, "path", "") or "")
    if name:
        return name
    if path:
        from pathlib import Path

        return Path(path).name
    return str(getattr(script, "id", ""))


def _diagnostic_number(value: object) -> str:
    if value is None:
        return "unavailable"
    try:
        return f"{float(value):.8g}"
    except (TypeError, ValueError):
        return "unavailable"


def _script_info(script: object) -> dict[str, object]:
    metadata = getattr(script, "metadata", {})
    return dict(metadata) if isinstance(metadata, dict) else {}


def _script_row_value(script: object, name: str) -> str:
    info = _script_info(script)
    mat_summary = info.get("mat_summary")
    mat_info = mat_summary if isinstance(mat_summary, dict) else {}
    preview = info.get("preview")
    preview_info = preview if isinstance(preview, dict) else {}
    if name in {"MAT version", "Format"} and mat_info:
        return str(mat_info.get("version", ""))
    if name in {"Variables", "Variable count"}:
        variable_count = info.get("variable_count")
        if variable_count not in (None, ""):
            return str(variable_count)
        variables = mat_info.get("variables", ())
        if isinstance(variables, list | tuple):
            return str(len(variables))
    if name in {"Variable names", "MAT variables"}:
        variables = mat_info.get("variables", info.get("variables", ()))
        if isinstance(variables, list | tuple):
            names = [
                str(variable.get("name", ""))
                for variable in variables
                if isinstance(variable, dict) and variable.get("name")
            ]
            return ", ".join(names)
    if name in {"Script kind", "Kind"}:
        return str(info.get("kind", info.get("data_type", preview_info.get("kind", ""))))
    if name in {"Lines", "Line count"}:
        return str(info.get("line_count", preview_info.get("line_count", "")))
    if name in {"Safety", "Safety summary"}:
        preview_metadata = preview_info.get("metadata", {})
        fallback = (
            preview_metadata.get("safety_summary", "") if isinstance(preview_metadata, dict) else ""
        )
        return str(info.get("safety_summary", fallback))
    if name in {"Plot hints", "Plot hint count"}:
        return str(info.get("plot_hint_count", len(preview_info.get("plot_hints", ()))))
    if name in {"Function", "Function signature"}:
        return str(info.get("raw_signature", info.get("function_name", "")))
    if name in {"Script status", "Status"}:
        return str(getattr(script, "status", "") or "")
    if name == "Safe preview required":
        return str(getattr(script, "safe_preview_required", True))
    return ""


def _curve_label(curve: object) -> str:
    return str(getattr(curve, "name", "") or getattr(curve, "curve_id", ""))


def _curve_row_value(curve: object, name: str) -> str:
    if name in {"Curve", "Name"}:
        return _curve_label(curve)
    if name in {"Curve kind", "Kind"}:
        return str(getattr(curve, "kind", ""))
    if name in {"Points", "Point count"}:
        return str(getattr(curve, "point_count", ""))
    if name in {"X unit", "Independent unit"}:
        return str(getattr(curve, "x_unit", ""))
    if name in {"Y unit", "Dependent unit"}:
        return str(getattr(curve, "y_unit", ""))
    if name == "Interpolation":
        return str(getattr(curve, "interpolation", ""))
    if name == "Source":
        source = getattr(curve, "source", None)
        if source is None:
            return ""
        return str(
            getattr(source, "source_file", "")
            or getattr(source, "source_dataset_id", "")
            or getattr(source, "source_run_id", "")
        )
    return ""
