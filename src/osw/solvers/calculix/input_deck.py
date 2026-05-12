"""CalculiX linear static input deck generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from osw.core.materials import Material
from osw.core.validation import ValidationReport
from osw.mesh.mesh_model import MeshCellBlock, MeshData

from .validation import SUPPORTED_CELL_TYPES, validate_calculix_case

LoadKind = Literal["force", "pressure"]


class CalculixInputDeckError(ValueError):
    """Raised when a CalculiX input deck cannot be generated safely."""


@dataclass(frozen=True)
class CalculixNodeSet:
    """Named one-based CalculiX node set."""

    name: str
    node_ids: tuple[int, ...]

    def __init__(self, name: str, node_ids: tuple[int, ...]) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "node_ids", tuple(int(node_id) for node_id in node_ids))


@dataclass(frozen=True)
class CalculixSurface:
    """Named CalculiX element surface using element id and face label pairs."""

    name: str
    element_faces: tuple[tuple[int, str], ...]

    def __init__(self, name: str, element_faces: tuple[tuple[int, str], ...]) -> None:
        normalized = tuple((int(element_id), str(face)) for element_id, face in element_faces)
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "element_faces", normalized)


@dataclass(frozen=True)
class CalculixBoundaryCondition:
    """Boundary condition supported by the v0.1 linear static deck generator."""

    name: str
    node_set: str
    dof_start: int = 1
    dof_end: int = 3
    value: float = 0.0
    kind: str = "fixed"

    @classmethod
    def fixed(
        cls,
        *,
        name: str,
        node_set: str,
        dofs: tuple[int, int] = (1, 3),
        value: float = 0.0,
    ) -> CalculixBoundaryCondition:
        return cls(
            name=name,
            node_set=node_set,
            dof_start=dofs[0],
            dof_end=dofs[1],
            value=value,
            kind="fixed",
        )


@dataclass(frozen=True)
class CalculixLoad:
    """Linear static force or pressure load."""

    name: str
    kind: LoadKind
    value: float
    node_set: str | None = None
    dof: int | None = None
    surface: str | None = None

    @classmethod
    def force(
        cls,
        *,
        name: str,
        node_set: str,
        dof: int,
        value: float,
    ) -> CalculixLoad:
        return cls(name=name, kind="force", node_set=node_set, dof=dof, value=value)

    @classmethod
    def pressure(cls, *, name: str, surface: str, value: float) -> CalculixLoad:
        return cls(name=name, kind="pressure", surface=surface, value=value)


@dataclass(frozen=True)
class CalculixLinearStaticCase:
    """Prepare-only CalculiX case for v0.1 linear static educational demos."""

    case_id: str
    mesh: MeshData
    material: Material | None
    node_sets: tuple[CalculixNodeSet, ...] = field(default_factory=tuple)
    surfaces: tuple[CalculixSurface, ...] = field(default_factory=tuple)
    boundary_conditions: tuple[CalculixBoundaryCondition, ...] = field(default_factory=tuple)
    loads: tuple[CalculixLoad, ...] = field(default_factory=tuple)
    step_name: str = "linear_static"


class CalculixInputDeckGenerator:
    """Render a deterministic CalculiX `.inp` deck without executing CalculiX."""

    def validate(self, case: CalculixLinearStaticCase) -> ValidationReport:
        return validate_calculix_case(case)

    def generate(self, case: CalculixLinearStaticCase) -> str:
        report = self.validate(case)
        if report.has_errors:
            raise CalculixInputDeckError(report.friendly_summary())

        if case.material is None or case.material.elastic is None:
            raise CalculixInputDeckError("CalculiX material validation did not run.")

        lines: list[str] = [
            "*HEADING",
            f"OSW CalculiX linear static deck: {case.case_id}",
            "Scope: v0.1 linear static only",
            "*NODE",
        ]
        lines.extend(_node_lines(case.mesh))
        lines.extend(_element_lines(case.mesh))
        lines.extend(_set_lines("ELSET", "EALL", tuple(range(1, _element_count(case.mesh) + 1))))
        lines.extend(_set_lines("NSET", "NALL", tuple(range(1, len(case.mesh.points) + 1))))
        for node_set in case.node_sets:
            lines.extend(_set_lines("NSET", node_set.name, node_set.node_ids))
        lines.extend(_surface_lines(case.surfaces))
        lines.extend(_material_lines(case.material))
        lines.append(f"*SOLID SECTION, ELSET=EALL, MATERIAL={case.material.material_id}")
        lines.extend(
            [
                f"*STEP, NAME={case.step_name}",
                "*STATIC",
            ]
        )
        lines.extend(_boundary_lines(case.boundary_conditions))
        lines.extend(_load_lines(case.loads))
        lines.extend(
            [
                "*NODE PRINT, NSET=NALL",
                "U",
                "*EL PRINT, ELSET=EALL",
                "S",
                "*END STEP",
            ]
        )
        return "\n".join(lines) + "\n"


def generate_calculix_input_deck(case: CalculixLinearStaticCase) -> str:
    return CalculixInputDeckGenerator().generate(case)


def _node_lines(mesh: MeshData) -> list[str]:
    return [
        f"{index}, {_format_float(x)}, {_format_float(y)}, {_format_float(z)}"
        for index, (x, y, z) in enumerate(mesh.points, start=1)
    ]


def _element_lines(mesh: MeshData) -> list[str]:
    lines: list[str] = []
    element_id = 1
    for block in mesh.cells:
        element_type = _calculix_element_type(block)
        lines.append(f"*ELEMENT, TYPE={element_type}, ELSET=EALL")
        for connectivity in block.data:
            node_ids = [str(index + 1) for index in connectivity]
            lines.append(f"{element_id}, {', '.join(node_ids)}")
            element_id += 1
    return lines


def _calculix_element_type(block: MeshCellBlock) -> str:
    try:
        return SUPPORTED_CELL_TYPES[block.cell_type]
    except KeyError as exc:
        msg = f"Unsupported CalculiX element cell type: {block.cell_type}"
        raise CalculixInputDeckError(msg) from exc


def _element_count(mesh: MeshData) -> int:
    return sum(block.count for block in mesh.cells)


def _set_lines(kind: str, name: str, ids: tuple[int, ...]) -> list[str]:
    lines = [f"*{kind}, {kind}={name}"]
    lines.extend(_chunked_ids(ids))
    return lines


def _chunked_ids(ids: tuple[int, ...], *, width: int = 16) -> list[str]:
    if not ids:
        return [""]
    return [
        ", ".join(str(item) for item in ids[index : index + width])
        for index in range(0, len(ids), width)
    ]


def _surface_lines(surfaces: tuple[CalculixSurface, ...]) -> list[str]:
    lines: list[str] = []
    for surface in surfaces:
        lines.append(f"*SURFACE, NAME={surface.name}, TYPE=ELEMENT")
        lines.extend(f"{element_id}, {face}" for element_id, face in surface.element_faces)
    return lines


def _material_lines(material: Material) -> list[str]:
    if material.elastic is None:
        raise CalculixInputDeckError("Material must include isotropic elastic fields.")

    lines = [
        f"*MATERIAL, NAME={material.material_id}",
        "*ELASTIC",
        (
            f"{_format_float(material.elastic.young_modulus.value)}, "
            f"{_format_float(material.elastic.poisson_ratio)}"
        ),
    ]
    if material.density is not None:
        lines.extend(["*DENSITY", _format_float(material.density.value)])
    return lines


def _boundary_lines(boundary_conditions: tuple[CalculixBoundaryCondition, ...]) -> list[str]:
    if not boundary_conditions:
        return []
    lines = ["*BOUNDARY"]
    lines.extend(
        (
            f"{item.node_set}, {item.dof_start}, {item.dof_end}, "
            f"{_format_float(item.value)}"
        )
        for item in boundary_conditions
    )
    return lines


def _load_lines(loads: tuple[CalculixLoad, ...]) -> list[str]:
    lines: list[str] = []
    force_loads = [load for load in loads if load.kind == "force"]
    pressure_loads = [load for load in loads if load.kind == "pressure"]
    if force_loads:
        lines.append("*CLOAD")
        for load in force_loads:
            lines.append(f"{load.node_set}, {load.dof}, {_format_float(load.value)}")
    if pressure_loads:
        lines.append("*DLOAD")
        for load in pressure_loads:
            lines.append(f"{load.surface}, P, {_format_float(load.value)}")
    return lines


def _format_float(value: float) -> str:
    return f"{float(value):.12g}"
