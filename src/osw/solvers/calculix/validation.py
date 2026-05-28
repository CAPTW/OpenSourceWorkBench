"""Validation for v0.1 CalculiX linear static case preparation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from osw.core.validation import ValidationReport

SUPPORTED_CELL_TYPES = {
    "triangle": "CPS3",
    "quad": "CPS4",
    "tetra": "C3D4",
    "tetra10": "C3D10",
    "hexahedron": "C3D8",
    "hexahedron20": "C3D20",
}


@dataclass(frozen=True, init=False)
class CantileverValidationInput:
    force: float
    length: float
    young_modulus: float
    second_moment_area: float
    tolerance_ratio: float = 0.05
    expected_unit: str = "m"

    def __init__(
        self,
        *,
        force: float,
        length: float,
        second_moment_area: float,
        young_modulus: float | None = None,
        elastic_modulus: float | None = None,
        tolerance_ratio: float | None = None,
        tolerance_fraction: float | None = None,
        expected_unit: str = "m",
    ) -> None:
        modulus = young_modulus if young_modulus is not None else elastic_modulus
        if modulus is None:
            msg = "Cantilever validation requires young_modulus or elastic_modulus."
            raise ValueError(msg)
        tolerance = (
            tolerance_ratio
            if tolerance_ratio is not None
            else 0.05
            if tolerance_fraction is None
            else tolerance_fraction
        )
        object.__setattr__(self, "force", float(force))
        object.__setattr__(self, "length", float(length))
        object.__setattr__(self, "young_modulus", float(modulus))
        object.__setattr__(self, "second_moment_area", float(second_moment_area))
        object.__setattr__(self, "tolerance_ratio", float(tolerance))
        object.__setattr__(self, "expected_unit", str(expected_unit))

    @property
    def elastic_modulus(self) -> float:
        return self.young_modulus

    @property
    def tolerance_fraction(self) -> float:
        return self.tolerance_ratio


@dataclass(frozen=True)
class CantileverValidationResult:
    observed_displacement: float | None
    expected_displacement: float
    relative_error: float
    tolerance_ratio: float
    passed: bool
    message: str
    formula: str = "F L^3 / (3 E I)"
    expected_unit: str = "m"
    absolute_error: float | None = None
    diagnostics: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "observed_displacement": self.observed_displacement,
            "expected_displacement": self.expected_displacement,
            "observed_max_displacement": self.observed_displacement,
            "expected_max_displacement": self.expected_displacement,
            "absolute_error": self.absolute_error,
            "relative_error": self.relative_error,
            "tolerance_ratio": self.tolerance_ratio,
            "tolerance_fraction": self.tolerance_ratio,
            "passed": self.passed,
            "message": self.message,
            "formula": self.formula,
            "expected_unit": self.expected_unit,
            "diagnostics": list(self.diagnostics),
        }

    @property
    def observed_max_displacement(self) -> float | None:
        return self.observed_displacement

    @property
    def expected_max_displacement(self) -> float:
        return self.expected_displacement

    @property
    def tolerance_fraction(self) -> float:
        return self.tolerance_ratio


def expected_cantilever_tip_displacement(
    force: float,
    length: float,
    elastic_modulus: float,
    second_moment_area: float,
) -> float:
    """Return the Euler-Bernoulli tip displacement estimate ``F L^3 / (3 E I)``."""

    return abs(force) * length**3 / (3.0 * elastic_modulus * second_moment_area)


def validate_cantilever_tip_displacement(
    *,
    observed_displacement: float,
    inputs: CantileverValidationInput,
) -> CantileverValidationResult:
    """Validate a cantilever tip displacement against the beam-theory estimate."""

    expected = expected_cantilever_tip_displacement(
        inputs.force,
        inputs.length,
        inputs.young_modulus,
        inputs.second_moment_area,
    )
    if expected == 0:
        relative_error = 0.0 if observed_displacement == 0 else float("inf")
    else:
        relative_error = abs(abs(observed_displacement) - expected) / expected
    passed = relative_error <= inputs.tolerance_ratio
    message = (
        "Cantilever tip displacement is within tolerance."
        if passed
        else "Cantilever tip displacement is outside tolerance."
    )
    return CantileverValidationResult(
        observed_displacement=observed_displacement,
        expected_displacement=expected,
        relative_error=relative_error,
        tolerance_ratio=inputs.tolerance_ratio,
        passed=passed,
        message=message,
        expected_unit=inputs.expected_unit,
        absolute_error=abs(abs(observed_displacement) - expected),
    )


def validate_cantilever_displacement(
    parsed_results: object,
    validation_input: CantileverValidationInput,
) -> CantileverValidationResult:
    """Validate parsed CalculiX max displacement against cantilever beam theory."""

    displacement = getattr(parsed_results, "displacement_summary", None)
    observed = getattr(displacement, "max_magnitude", None)
    expected = expected_cantilever_tip_displacement(
        validation_input.force,
        validation_input.length,
        validation_input.young_modulus,
        validation_input.second_moment_area,
    )
    if observed is None:
        return CantileverValidationResult(
            observed_displacement=None,
            expected_displacement=expected,
            relative_error=float("inf"),
            tolerance_ratio=validation_input.tolerance_ratio,
            passed=False,
            message="Observed max displacement is missing from parsed CalculiX results.",
            expected_unit=validation_input.expected_unit,
            diagnostics=("Parsed CalculiX results do not include max displacement.",),
        )
    return validate_cantilever_tip_displacement(
        observed_displacement=float(observed),
        inputs=validation_input,
    )


def validate_calculix_case(case: object) -> ValidationReport:
    """Return friendly validation messages without writing files or running CalculiX."""

    report = ValidationReport()
    case_id = getattr(case, "case_id", "")
    mesh = getattr(case, "mesh", None)
    material = getattr(case, "material", None)
    node_sets = tuple(getattr(case, "node_sets", ()))
    surfaces = tuple(getattr(case, "surfaces", ()))
    boundary_conditions = tuple(getattr(case, "boundary_conditions", ()))
    loads = tuple(getattr(case, "loads", ()))

    if not case_id:
        report.add_error("case.case_id", "CalculiX case id is required.")

    if mesh is None:
        report.add_error("case.mesh", "Mesh is required for CalculiX input deck generation.")
    else:
        _validate_mesh(mesh, report)

    if material is None:
        report.add_error(
            "case.material",
            "Material is required and must include isotropic elastic material fields.",
        )
    else:
        report.extend(material.validate(path="case.material"))
        if material.elastic is None:
            report.add_error(
                "case.material.elastic",
                "Material is required to include isotropic elastic material fields.",
            )
        elif material.elastic.young_modulus.unit != "Pa":
            report.add_warning(
                "case.material.elastic.young_modulus.unit",
                "CalculiX deck writes elastic modulus as provided; SI Pa is expected.",
            )
        if material.density is not None and material.density.unit != "kg/m^3":
            report.add_warning(
                "case.material.density.unit",
                "CalculiX deck writes density as provided; SI kg/m^3 is expected.",
            )

    node_set_names = _validate_node_sets(node_sets, len(getattr(mesh, "points", ())), report)
    surface_names = _validate_surfaces(surfaces, _element_count(mesh), report)
    _validate_boundary_conditions(boundary_conditions, node_set_names, report)
    _validate_loads(loads, node_set_names, surface_names, report)

    if not any(getattr(item, "kind", "") == "fixed" for item in boundary_conditions):
        report.add_warning(
            "case.boundary_conditions",
            "No fixed support was defined; linear static demo may be underconstrained.",
        )

    return report


def validate_calculix_readiness(
    project: object,
    *,
    mesh_model: object | None = None,
    base_path: object | None = None,
) -> ValidationReport:
    """Validate ProjectSchema readiness for deck generation without running ccx."""

    from .adapter import project_to_calculix_case

    _, report = project_to_calculix_case(
        project,  # type: ignore[arg-type]
        mesh_model=mesh_model,  # type: ignore[arg-type]
        base_path=base_path,  # type: ignore[arg-type]
    )
    return report


def _validate_mesh(mesh: object, report: ValidationReport) -> None:
    points = tuple(getattr(mesh, "points", ()))
    cells = tuple(getattr(mesh, "cells", ()))
    if not points or not cells or _element_count(mesh) == 0:
        report.add_error("case.mesh", "Mesh must include nodes and elements.")
        return

    for block_index, block in enumerate(cells):
        cell_type = getattr(block, "cell_type", "")
        if cell_type not in SUPPORTED_CELL_TYPES:
            report.add_error(
                f"case.mesh.cells[{block_index}].cell_type",
                f"Unsupported CalculiX element cell type: {cell_type}",
            )
        for element_index, connectivity in enumerate(getattr(block, "data", ())):
            for node_index in connectivity:
                if node_index < 0 or node_index >= len(points):
                    report.add_error(
                        f"case.mesh.cells[{block_index}].data[{element_index}]",
                        f"Element connectivity references zero-based node index {node_index} "
                        "outside the mesh point range.",
                    )


def _validate_node_sets(
    node_sets: tuple[object, ...],
    node_count: int,
    report: ValidationReport,
) -> set[str]:
    names: set[str] = set()
    for index, node_set in enumerate(node_sets):
        name = str(getattr(node_set, "name", ""))
        node_ids = tuple(getattr(node_set, "node_ids", ()))
        path = f"case.node_sets[{index}]"
        if not name:
            report.add_error(f"{path}.name", "Node set name is required.")
            continue
        if name in names:
            report.add_error(f"{path}.name", f"Duplicate node set name: {name}")
        names.add(name)
        if not node_ids:
            report.add_warning(path, f"Node set {name} is empty.")
        for node_id in node_ids:
            if node_id < 1 or node_id > node_count:
                report.add_error(
                    f"{path}.node_ids",
                    f"Node set {name} references node id {node_id} outside mesh node range.",
                )
    return names


def _validate_surfaces(
    surfaces: tuple[object, ...],
    element_count: int,
    report: ValidationReport,
) -> set[str]:
    names: set[str] = set()
    for index, surface in enumerate(surfaces):
        name = str(getattr(surface, "name", ""))
        element_faces = tuple(getattr(surface, "element_faces", ()))
        path = f"case.surfaces[{index}]"
        if not name:
            report.add_error(f"{path}.name", "Surface name is required.")
            continue
        if name in names:
            report.add_error(f"{path}.name", f"Duplicate surface name: {name}")
        names.add(name)
        if not element_faces:
            report.add_warning(path, f"Surface {name} is empty.")
        for element_id, face in element_faces:
            if element_id < 1 or element_id > element_count:
                report.add_error(
                    f"{path}.element_faces",
                    f"Surface {name} references element id {element_id} outside mesh range.",
                )
            if not face:
                report.add_error(
                    f"{path}.element_faces",
                    f"Surface {name} has an empty face label.",
                )
    return names


def _validate_boundary_conditions(
    boundary_conditions: tuple[object, ...],
    node_set_names: set[str],
    report: ValidationReport,
) -> None:
    for index, boundary_condition in enumerate(boundary_conditions):
        path = f"case.boundary_conditions[{index}]"
        node_set = str(getattr(boundary_condition, "node_set", ""))
        if node_set not in node_set_names:
            report.add_error(f"{path}.node_set", f"Unknown node set '{node_set}'.")
        dof_start = int(getattr(boundary_condition, "dof_start", 0))
        dof_end = int(getattr(boundary_condition, "dof_end", 0))
        if dof_start < 1 or dof_end > 3 or dof_start > dof_end:
            report.add_error(path, "Boundary condition DOF range must be between 1 and 3.")


def _validate_loads(
    loads: tuple[object, ...],
    node_set_names: set[str],
    surface_names: set[str],
    report: ValidationReport,
) -> None:
    for index, load in enumerate(loads):
        kind = getattr(load, "kind", "")
        path = f"case.loads[{index}]"
        if kind == "force":
            node_set = str(getattr(load, "node_set", ""))
            if node_set not in node_set_names:
                report.add_error(f"{path}.node_set", f"Unknown node set '{node_set}'.")
            dof = getattr(load, "dof", None)
            if dof not in (1, 2, 3):
                report.add_error(f"{path}.dof", "Force load DOF must be 1, 2, or 3.")
        elif kind == "pressure":
            surface = str(getattr(load, "surface", ""))
            if surface not in surface_names:
                report.add_error(f"{path}.surface", f"Unknown surface '{surface}'.")
        else:
            report.add_error(f"{path}.kind", f"Unsupported CalculiX load kind: {kind}")


def _element_count(mesh: object | None) -> int:
    if mesh is None:
        return 0
    return sum(getattr(block, "count", 0) for block in getattr(mesh, "cells", ()))
