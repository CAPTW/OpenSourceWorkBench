"""Serializable models for bounded Gmsh mesh generation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Self

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.mesh.mesh_model import MeshInfo, MeshModel
from osw.solvers.runner import RunResult


class GmshGeometryKind(StrEnum):
    BOX = "box"
    RECTANGLE = "rectangle"
    CYLINDER = "cylinder"
    SPHERE = "sphere"
    PLATE_WITH_HOLE = "plate_with_hole"
    IMPORTED_GEOMETRY_PLACEHOLDER = "imported_geometry_placeholder"
    UNKNOWN = "unknown"


class GmshMeshDimension(StrEnum):
    DIM1 = "dim1"
    DIM2 = "dim2"
    DIM3 = "dim3"

    @property
    def numeric(self) -> int:
        return {self.DIM1: 1, self.DIM2: 2, self.DIM3: 3}[self]


class GmshMeshStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    DEPENDENCY_MISSING = "dependency_missing"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, init=False)
class GmshMeshSizeField:
    """Small mesh size control model for primitive Gmsh templates."""

    global_size: float
    min_size: float | None
    max_size: float | None
    curvature_based: bool
    boundary_layer_placeholder: bool
    metadata: dict[str, Any]

    def __init__(
        self,
        global_size: float = 1.0,
        min_size: float | None = None,
        max_size: float | None = None,
        curvature_based: bool = False,
        boundary_layer_placeholder: bool = False,
        metadata: Mapping[str, Any] | None = None,
        *,
        target_size: float | None = None,
    ) -> None:
        resolved_global = float(global_size if target_size is None else target_size)
        _validate_positive("global mesh size", resolved_global)
        if min_size is not None:
            _validate_positive("minimum mesh size", float(min_size))
        if max_size is not None:
            _validate_positive("maximum mesh size", float(max_size))
        if min_size is not None and max_size is not None and min_size > max_size:
            msg = "minimum mesh size must be less than or equal to maximum mesh size."
            raise ValueError(msg)
        object.__setattr__(self, "global_size", resolved_global)
        object.__setattr__(self, "min_size", float(min_size) if min_size is not None else None)
        object.__setattr__(self, "max_size", float(max_size) if max_size is not None else None)
        object.__setattr__(self, "curvature_based", bool(curvature_based))
        object.__setattr__(self, "boundary_layer_placeholder", bool(boundary_layer_placeholder))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def target_size(self) -> float:
        return self.global_size

    @property
    def effective_min(self) -> float:
        return self.min_size if self.min_size is not None else self.global_size

    @property
    def effective_max(self) -> float:
        return self.max_size if self.max_size is not None else self.global_size

    def to_dict(self) -> dict[str, Any]:
        return {
            "global_size": self.global_size,
            "target_size": self.global_size,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "curvature_based": self.curvature_based,
            "boundary_layer_placeholder": self.boundary_layer_placeholder,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            global_size=float(data.get("global_size", data.get("target_size", 1.0))),
            min_size=_optional_float(data.get("min_size")),
            max_size=_optional_float(data.get("max_size")),
            curvature_based=bool(data.get("curvature_based", False)),
            boundary_layer_placeholder=bool(data.get("boundary_layer_placeholder", False)),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class GmshPhysicalGroup:
    name: str
    dimension: int
    entity_ids: tuple[int, ...] = field(default_factory=tuple)
    tag: int | None = None
    role: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __init__(
        self,
        name: str,
        dimension: int | str | GmshMeshDimension,
        entity_ids: Iterable[int] = (),
        *,
        tag: int | None = None,
        role: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "name", str(name))
        object.__setattr__(self, "dimension", _dimension_number(dimension))
        object.__setattr__(self, "entity_ids", tuple(int(item) for item in entity_ids))
        object.__setattr__(self, "tag", int(tag) if tag is not None else None)
        object.__setattr__(self, "role", str(role or name))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def entities(self) -> tuple[int, ...]:
        return self.entity_ids

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "dimension": self.dimension,
            "tag": self.tag,
            "entity_ids": list(self.entity_ids),
            "entities": list(self.entity_ids),
            "role": self.role,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            name=str(data.get("name", "")),
            dimension=data.get("dimension", 0),
            entity_ids=data.get("entity_ids", data.get("entities", ())) or (),
            tag=_optional_int(data.get("tag")),
            role=str(data.get("role", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True, init=False)
class GmshGeometrySpec:
    geometry_id: str
    kind: GmshGeometryKind
    parameters: dict[str, Any]
    units: str
    physical_groups: tuple[GmshPhysicalGroup, ...]
    metadata: dict[str, Any]

    def __init__(
        self,
        kind: str | GmshGeometryKind = GmshGeometryKind.UNKNOWN,
        parameters: Mapping[str, Any] | None = None,
        *,
        geometry_id: str = "",
        units: str = "",
        physical_groups: Iterable[GmshPhysicalGroup | Mapping[str, Any]] = (),
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        resolved_kind = _geometry_kind(kind)
        object.__setattr__(self, "geometry_id", geometry_id or resolved_kind.value)
        object.__setattr__(self, "kind", resolved_kind)
        object.__setattr__(self, "parameters", dict(parameters or {}))
        object.__setattr__(self, "units", str(units))
        object.__setattr__(
            self,
            "physical_groups",
            tuple(_physical_group(item) for item in physical_groups),
        )
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self) -> dict[str, Any]:
        return {
            "geometry_id": self.geometry_id,
            "kind": self.kind.value,
            "parameters": dict(self.parameters),
            "units": self.units,
            "physical_groups": [group.to_dict() for group in self.physical_groups],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            kind=data.get("kind", GmshGeometryKind.UNKNOWN.value),
            parameters=dict(data.get("parameters", {}) or {}),
            geometry_id=str(data.get("geometry_id", "")),
            units=str(data.get("units", "")),
            physical_groups=data.get("physical_groups", ()) or (),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True, init=False)
class GmshMeshRequest:
    geometry: GmshGeometrySpec
    mesh_dimension: GmshMeshDimension
    mesh_size: GmshMeshSizeField
    output_dir: Path
    output_name: str
    run_id: str
    write_geo: bool
    convert_to_vtu: bool
    timeout_seconds: float
    metadata: dict[str, Any]

    def __init__(
        self,
        geometry: GmshGeometrySpec | Mapping[str, Any] | None = None,
        mesh_dimension: str | int | GmshMeshDimension = GmshMeshDimension.DIM3,
        mesh_size: GmshMeshSizeField | Mapping[str, Any] | None = None,
        output_dir: str | Path = ".",
        output_name: str = "gmsh_mesh",
        *,
        run_id: str = "",
        write_geo: bool = True,
        convert_to_vtu: bool = False,
        timeout_seconds: float = 30.0,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        object.__setattr__(self, "geometry", _geometry_spec(geometry))
        object.__setattr__(self, "mesh_dimension", _mesh_dimension(mesh_dimension))
        object.__setattr__(self, "mesh_size", _mesh_size(mesh_size))
        object.__setattr__(self, "output_dir", Path(output_dir))
        object.__setattr__(self, "output_name", _safe_output_name(output_name))
        object.__setattr__(self, "run_id", str(run_id))
        object.__setattr__(self, "write_geo", bool(write_geo))
        object.__setattr__(self, "convert_to_vtu", bool(convert_to_vtu))
        object.__setattr__(self, "timeout_seconds", float(timeout_seconds))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def geo_filename(self) -> str:
        return f"{self.output_name}.geo"

    @property
    def msh_filename(self) -> str:
        return f"{self.output_name}.msh"

    @property
    def vtu_filename(self) -> str:
        return f"{self.output_name}.vtu"

    def to_dict(self) -> dict[str, Any]:
        return {
            "geometry": self.geometry.to_dict(),
            "mesh_dimension": self.mesh_dimension.value,
            "mesh_size": self.mesh_size.to_dict(),
            "output_dir": str(self.output_dir),
            "output_name": self.output_name,
            "run_id": self.run_id,
            "write_geo": self.write_geo,
            "convert_to_vtu": self.convert_to_vtu,
            "timeout_seconds": self.timeout_seconds,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        return cls(
            geometry=data.get("geometry", {}),
            mesh_dimension=data.get("mesh_dimension", GmshMeshDimension.DIM3.value),
            mesh_size=data.get("mesh_size", {}),
            output_dir=Path(str(data.get("output_dir", "."))),
            output_name=str(data.get("output_name", "gmsh_mesh")),
            run_id=str(data.get("run_id", "")),
            write_geo=bool(data.get("write_geo", True)),
            convert_to_vtu=bool(data.get("convert_to_vtu", False)),
            timeout_seconds=float(data.get("timeout_seconds", 30.0)),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class GmshMeshResult:
    status: GmshMeshStatus
    request: GmshMeshRequest
    geo_path: Path | None = None
    msh_path: Path | None = None
    converted_mesh_path: Path | None = None
    mesh_model: MeshModel | None = None
    mesh_info: MeshInfo | None = None
    physical_groups: tuple[GmshPhysicalGroup, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    run_result: RunResult | None = None
    artifacts: tuple[RunArtifact, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "request": self.request.to_dict(),
            "geo_path": str(self.geo_path) if self.geo_path else "",
            "msh_path": str(self.msh_path) if self.msh_path else "",
            "converted_mesh_path": (
                str(self.converted_mesh_path) if self.converted_mesh_path else ""
            ),
            "mesh_model": (
                self.mesh_model.to_dict(include_arrays=False) if self.mesh_model else None
            ),
            "mesh_info": self.mesh_info.to_dict() if self.mesh_info else None,
            "physical_groups": [group.to_dict() for group in self.physical_groups],
            "diagnostics": self.diagnostics.to_dict(),
            "run_result": self.run_result.to_dict() if self.run_result else None,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
        }


def _validate_positive(label: str, value: float) -> None:
    if value <= 0:
        msg = f"{label} must be positive."
        raise ValueError(msg)


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)  # type: ignore[arg-type]


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)  # type: ignore[arg-type]


def _geometry_kind(value: object) -> GmshGeometryKind:
    if isinstance(value, GmshGeometryKind):
        return value
    try:
        return GmshGeometryKind(str(value))
    except ValueError:
        return GmshGeometryKind.UNKNOWN


def _mesh_dimension(value: object) -> GmshMeshDimension:
    if isinstance(value, GmshMeshDimension):
        return value
    if isinstance(value, int):
        return {1: GmshMeshDimension.DIM1, 2: GmshMeshDimension.DIM2}.get(
            value,
            GmshMeshDimension.DIM3,
        )
    text = str(value).strip().lower()
    aliases = {
        "1": GmshMeshDimension.DIM1,
        "dim1": GmshMeshDimension.DIM1,
        "1d": GmshMeshDimension.DIM1,
        "2": GmshMeshDimension.DIM2,
        "dim2": GmshMeshDimension.DIM2,
        "2d": GmshMeshDimension.DIM2,
        "3": GmshMeshDimension.DIM3,
        "dim3": GmshMeshDimension.DIM3,
        "3d": GmshMeshDimension.DIM3,
    }
    return aliases.get(text, GmshMeshDimension.DIM3)


def _dimension_number(value: object) -> int:
    if isinstance(value, GmshMeshDimension):
        return value.numeric
    if isinstance(value, int):
        return value
    text = str(value).strip().lower()
    if text.startswith("dim"):
        text = text[-1]
    try:
        return int(text)
    except ValueError:
        return 0


def _geometry_spec(value: GmshGeometrySpec | Mapping[str, Any] | None) -> GmshGeometrySpec:
    if isinstance(value, GmshGeometrySpec):
        return value
    if isinstance(value, Mapping):
        return GmshGeometrySpec.from_dict(value)
    return GmshGeometrySpec(GmshGeometryKind.BOX, {"length": 1.0, "width": 1.0, "height": 1.0})


def _mesh_size(value: GmshMeshSizeField | Mapping[str, Any] | None) -> GmshMeshSizeField:
    if isinstance(value, GmshMeshSizeField):
        return value
    if isinstance(value, Mapping):
        return GmshMeshSizeField.from_dict(value)
    return GmshMeshSizeField()


def _physical_group(value: GmshPhysicalGroup | Mapping[str, Any]) -> GmshPhysicalGroup:
    if isinstance(value, GmshPhysicalGroup):
        return value
    return GmshPhysicalGroup.from_dict(value)


def _safe_output_name(value: str) -> str:
    text = Path(str(value)).stem
    safe = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in text)
    return safe or "gmsh_mesh"
