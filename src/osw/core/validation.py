"""Validation helpers for OSW core data contracts."""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

Severity = Literal["error", "warning", "info"]


class ProjectSchemaError(ValueError):
    """Raised when project data cannot be parsed into the OSW schema."""


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True)
class ValidationMessage:
    severity: Severity
    path: str
    message: str

    @classmethod
    def error(cls, path: str, message: str) -> ValidationMessage:
        return cls("error", path, message)

    @classmethod
    def warning(cls, path: str, message: str) -> ValidationMessage:
        return cls("warning", path, message)


@dataclass
class ValidationReport:
    messages: list[ValidationMessage] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(message.severity == "error" for message in self.messages)

    @property
    def has_warnings(self) -> bool:
        return any(message.severity == "warning" for message in self.messages)

    def add_error(self, path: str, message: str) -> None:
        self.messages.append(ValidationMessage.error(path, message))

    def add_warning(self, path: str, message: str) -> None:
        self.messages.append(ValidationMessage.warning(path, message))

    def extend(self, other: ValidationReport) -> None:
        self.messages.extend(other.messages)

    def friendly_summary(self) -> str:
        if not self.messages:
            return "No validation messages."
        return "\n".join(
            f"{message.severity.upper()} {message.path}: {message.message}"
            for message in self.messages
        )


STRUCTURAL_ANALYSIS_TYPES = frozenset(
    {
        "linear_static",
        "static",
        "structural",
        "solid",
        "fem",
        "cae",
    }
)
VISCOSITY_KEYS = frozenset(
    {
        "viscosity",
        "dynamic_viscosity",
        "kinematic_viscosity",
    }
)


def validate_project_sanity(
    project: object,
    *,
    meshes: Iterable[object] | Mapping[str, object] = (),
    path: str = "project",
) -> ValidationReport:
    """Run lightweight physical/numerical sanity checks for reportable workflows."""

    report = ValidationReport()
    _check_unit_consistency(project, report, path=path)
    _check_material_sanity(project, report, path=path)
    _check_mesh_references(project, report, path=path)
    _check_mesh_payloads(meshes, report)
    _check_boundary_condition_completeness(project, report, path=path)
    _check_solver_convergence_placeholders(project, report, path=path)
    return report


def validate_project(project: object) -> ValidationReport:
    """Validate a ProjectSchema object without requiring callers to know methods."""

    validate = getattr(project, "validate", None)
    if callable(validate):
        return validate()
    report = ValidationReport()
    report.add_error("project", "Object does not provide ProjectSchema validation.")
    return report


def validate_units(project: object) -> ValidationReport:
    units = getattr(project, "units", getattr(project, "unit_system", None))
    if units is None:
        report = ValidationReport()
        report.add_warning("units", "Unit system missing; verify physical units.")
        return report
    validate = getattr(units, "validate", None)
    if callable(validate):
        return validate()
    return ValidationReport()


def validate_materials(project: object) -> ValidationReport:
    from osw.core.materials import MaterialDB

    return MaterialDB(list(getattr(project, "materials", ()) or ())).validate()


def validate_boundaries(project: object) -> ValidationReport:
    report = ValidationReport()
    for setup_index, setup in enumerate(tuple(getattr(project, "physics", ()) or ())):
        for bc_index, boundary_condition in enumerate(
            tuple(getattr(setup, "boundary_conditions", ()) or ())
        ):
            _check_boundary_condition(
                boundary_condition,
                report,
                path=f"physics[{setup_index}].boundary_conditions[{bc_index}]",
            )
    return report


def validate_solver_config(project: object) -> ValidationReport:
    report = ValidationReport()
    for index, solver in enumerate(tuple(getattr(project, "solvers", ()) or ())):
        solver_name = str(getattr(solver, "solver", "") or getattr(solver, "name", "") or "")
        if not solver_name:
            report.add_error(f"solvers[{index}].solver", "Solver name is required.")
        tolerance = _coerce_float(getattr(solver, "convergence_tolerance", None))
        if tolerance is not None and tolerance <= 0:
            report.add_error(
                f"solvers[{index}].convergence_tolerance",
                "Convergence tolerance must be positive.",
            )
    return report


def validate_mesh_sanity(mesh: object, *, path: str = "mesh") -> ValidationReport:
    """Check mesh payloads for the minimum structural sanity needed in v0.1."""

    report = ValidationReport()
    points = getattr(mesh, "points", None)
    cells = getattr(mesh, "cells", None)
    cell_blocks = () if cells is None else tuple(cells)
    point_count = _safe_len(points)
    element_count = sum(_cell_block_count(block) for block in cell_blocks)

    if point_count <= 0:
        report.add_error(f"{path}.points", "Mesh must contain at least one node.")
    if element_count <= 0:
        report.add_error(f"{path}.cells", "Mesh must contain at least one cell.")
    return report


def _check_unit_consistency(project: object, report: ValidationReport, *, path: str) -> None:
    units = getattr(project, "units", None)
    if units is None:
        report.add_warning(f"{path}.units", "Unit system missing; verify physical units.")
        return

    if bool(getattr(units, "defaulted", False)):
        report.add_warning(
            f"{path}.units",
            "Unit system defaulted to SI; verify imported physical quantities.",
        )

    pressure = str(getattr(units, "pressure", "") or "")
    stress = str(getattr(units, "stress", "") or "")
    if pressure and stress and pressure != stress:
        report.add_warning(
            f"{path}.units",
            f"Pressure unit {pressure!r} differs from stress unit {stress!r}; verify conversions.",
        )


def _check_material_sanity(project: object, report: ValidationReport, *, path: str) -> None:
    units = getattr(project, "units", None)
    density_unit = _expected_density_unit(units)
    stress_unit = str(getattr(units, "stress", "") or "")
    for index, material in enumerate(tuple(getattr(project, "materials", ()) or ())):
        material_path = f"{path}.materials[{index}]"
        density = getattr(material, "density", None)
        if density is None:
            report.add_warning(
                f"{material_path}.density",
                "Material density missing; mass-related sanity checks are limited.",
            )
        else:
            value, unit = _quantity_value_unit(density)
            if value is not None and not math.isfinite(value):
                report.add_error(
                    f"{material_path}.density",
                    "Material density must be finite.",
                )
            elif value is not None and value < 0:
                report.add_error(
                    f"{material_path}.density",
                    "Material density must be nonnegative.",
                )
            elif value == 0:
                report.add_warning(
                    f"{material_path}.density",
                    "Material density is zero; verify this is intentional.",
                )
            if unit and density_unit and unit != density_unit:
                report.add_warning(
                    f"{material_path}.density",
                    f"Density unit {unit!r} does not match project unit basis {density_unit!r}.",
                )

        elastic = getattr(material, "elastic", None)
        young_modulus = getattr(elastic, "young_modulus", None)
        _, young_unit = _quantity_value_unit(young_modulus)
        if young_unit and stress_unit and young_unit != stress_unit:
            report.add_warning(
                f"{material_path}.elastic.young_modulus",
                (
                    f"Young modulus unit {young_unit!r} differs from project "
                    f"stress unit {stress_unit!r}."
                ),
            )

        _check_viscosity_metadata(material, report, path=material_path)


def _check_viscosity_metadata(
    material: object,
    report: ValidationReport,
    *,
    path: str,
) -> None:
    metadata = getattr(material, "metadata", {}) or {}
    if not isinstance(metadata, Mapping):
        return

    for key in VISCOSITY_KEYS:
        if key not in metadata:
            continue
        value, unit = _quantity_value_unit(metadata[key])
        if value is None:
            continue
        if not math.isfinite(value):
            report.add_error(f"{path}.metadata.{key}", "Viscosity must be finite.")
        elif value <= 0:
            report.add_error(f"{path}.metadata.{key}", "Viscosity must be positive.")
        if not unit:
            report.add_warning(
                f"{path}.metadata.{key}",
                "Viscosity value has no explicit unit metadata.",
            )


def _check_mesh_references(project: object, report: ValidationReport, *, path: str) -> None:
    for index, mesh_ref in enumerate(tuple(getattr(project, "meshes", ()) or ())):
        metadata = getattr(mesh_ref, "metadata", {}) or {}
        if not isinstance(metadata, Mapping):
            continue
        count = _first_numeric(metadata, ("element_count", "elements", "cell_count", "cells"))
        if count is not None and not math.isfinite(count):
            report.add_error(
                f"{path}.meshes[{index}].metadata.elements",
                "Mesh metadata cell count must be finite.",
            )
        elif count is not None and count <= 0:
            report.add_error(
                f"{path}.meshes[{index}].metadata.elements",
                "Mesh metadata reports zero cells.",
            )


def _check_mesh_payloads(
    meshes: Iterable[object] | Mapping[str, object],
    report: ValidationReport,
) -> None:
    if isinstance(meshes, Mapping):
        items = tuple(meshes.items())
    else:
        items = tuple((f"meshes[{index}]", mesh) for index, mesh in enumerate(meshes))

    for key, mesh in items:
        report.extend(validate_mesh_sanity(mesh, path=str(key)))


def _check_boundary_condition_completeness(
    project: object,
    report: ValidationReport,
    *,
    path: str,
) -> None:
    material_ids = {
        str(getattr(material, "material_id", ""))
        for material in tuple(getattr(project, "materials", ()) or ())
        if getattr(material, "material_id", "")
    }
    for setup_index, setup in enumerate(tuple(getattr(project, "physics", ()) or ())):
        setup_path = f"{path}.physics[{setup_index}]"
        analysis_type = str(getattr(setup, "analysis_type", "") or "").lower()
        boundary_conditions = tuple(getattr(setup, "boundary_conditions", ()) or ())
        assignments = dict(getattr(setup, "material_assignments", {}) or {})

        if not boundary_conditions:
            report.add_warning(
                f"{setup_path}.boundary_conditions",
                "No boundary conditions defined; case may be under-constrained.",
            )
        for bc_index, boundary_condition in enumerate(boundary_conditions):
            _check_boundary_condition(
                boundary_condition,
                report,
                path=f"{setup_path}.boundary_conditions[{bc_index}]",
            )

        if not assignments:
            severity = "error" if analysis_type in STRUCTURAL_ANALYSIS_TYPES else "warning"
            _add_message(
                report,
                severity,
                f"{setup_path}.material_assignments",
                "No material assignments defined for physics setup.",
            )
        elif not material_ids:
            severity = "error" if analysis_type in STRUCTURAL_ANALYSIS_TYPES else "warning"
            _add_message(
                report,
                severity,
                f"{setup_path}.material_assignments",
                "Material assignments are present but no material definitions are registered.",
            )
        for region, material_id in assignments.items():
            if not material_id:
                report.add_error(
                    f"{setup_path}.material_assignments.{region}",
                    "Material assignment must reference a material id.",
                )
            elif material_ids and str(material_id) not in material_ids:
                report.add_error(
                    f"{setup_path}.material_assignments.{region}",
                    f"Material assignment references unknown material id: {material_id}",
                )


def _check_boundary_condition(
    boundary_condition: object,
    report: ValidationReport,
    *,
    path: str,
) -> None:
    if not str(getattr(boundary_condition, "name", "") or ""):
        report.add_warning(f"{path}.name", "Boundary condition name is missing.")
    if not str(getattr(boundary_condition, "kind", "") or ""):
        report.add_error(f"{path}.kind", "Boundary condition kind is required.")
    if not str(getattr(boundary_condition, "target", "") or ""):
        report.add_error(f"{path}.target", "Boundary condition target is required.")
    values = getattr(boundary_condition, "values", {}) or {}
    curve_id = str(getattr(boundary_condition, "curve_id", "") or "")
    if not values and not curve_id:
        report.add_warning(
            f"{path}.values",
            "Boundary condition has no values; verify the constraint or load definition.",
        )


def _check_solver_convergence_placeholders(
    project: object,
    report: ValidationReport,
    *,
    path: str,
) -> None:
    for index, solver in enumerate(tuple(getattr(project, "solvers", ()) or ())):
        parameters = dict(getattr(solver, "parameters", {}) or {})
        solver_path = f"{path}.solvers[{index}]"
        convergence_value = parameters.get("convergence_status", parameters.get("converged"))
        if convergence_value is None:
            report.add_warning(
                f"{solver_path}.convergence",
                "Solver convergence status not recorded; treat result checks as provisional.",
            )
            continue
        if convergence_value is False or str(convergence_value).lower() in {
            "failed",
            "false",
            "not_converged",
            "not-converged",
            "unknown",
        }:
            report.add_warning(
                f"{solver_path}.convergence",
                f"Solver convergence status is {convergence_value!r}.",
            )


def _add_message(
    report: ValidationReport,
    severity: Severity,
    path: str,
    message: str,
) -> None:
    if severity == "error":
        report.add_error(path, message)
    elif severity == "warning":
        report.add_warning(path, message)


def _expected_density_unit(units: object | None) -> str:
    if units is None:
        return ""
    mass = str(getattr(units, "mass", "") or "")
    length = str(getattr(units, "length", "") or "")
    if not mass or not length:
        return ""
    return f"{mass}/{length}^3"


def _quantity_value_unit(value: object) -> tuple[float | None, str]:
    if value is None:
        return None, ""
    if isinstance(value, Mapping):
        raw_value = value.get("value", value.get("magnitude"))
        raw_unit = value.get("unit", value.get("units", ""))
    else:
        raw_value = getattr(value, "value", value)
        raw_unit = getattr(value, "unit", "")

    numeric = _coerce_float(raw_value)
    return numeric, str(raw_unit or "")


def _first_numeric(metadata: Mapping[str, Any], keys: Iterable[str]) -> float | None:
    for key in keys:
        if key in metadata:
            return _coerce_float(metadata[key])
    return None


def _cell_block_count(block: object) -> int:
    explicit_count = getattr(block, "count", None)
    if explicit_count is not None:
        try:
            return int(explicit_count)
        except (OverflowError, TypeError, ValueError):
            return 0
    return _safe_len(getattr(block, "data", block))


def _safe_len(value: object) -> int:
    if value is None:
        return 0
    try:
        return len(value)  # type: ignore[arg-type]
    except TypeError:
        return 0


def _coerce_float(value: object) -> float | None:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
