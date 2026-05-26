"""Preview-safe mesh metadata and lightweight in-memory mesh models."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

Point3D = tuple[float, float, float]
Connectivity = tuple[int, ...]


class MeshFormat(StrEnum):
    """Standard/exported mesh formats recognized by the v0.1 bridge."""

    GMSH_MSH = "gmsh"
    ABAQUS_INP = "abaqus"
    ANSYS_MSH = "ansys"
    NASTRAN_BDF = "nastran"
    SU2 = "su2"
    VTK = "vtk"
    VTU = "vtu"
    XDMF = "xdmf"
    CGNS = "cgns"
    MED = "med"
    STL = "stl"
    OBJ = "obj"
    UNKNOWN = "unknown"


@dataclass(frozen=True, init=False)
class MeshBounds:
    """Axis-aligned 3D mesh bounds."""

    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float

    def __init__(
        self,
        min_x: float = 0.0,
        min_y: float = 0.0,
        min_z: float = 0.0,
        max_x: float = 0.0,
        max_y: float = 0.0,
        max_z: float = 0.0,
        *,
        minimum: Sequence[float] | None = None,
        maximum: Sequence[float] | None = None,
    ) -> None:
        if minimum is not None:
            min_x, min_y, min_z = normalize_point(minimum)
        if maximum is not None:
            max_x, max_y, max_z = normalize_point(maximum)
        object.__setattr__(self, "min_x", float(min_x))
        object.__setattr__(self, "min_y", float(min_y))
        object.__setattr__(self, "min_z", float(min_z))
        object.__setattr__(self, "max_x", float(max_x))
        object.__setattr__(self, "max_y", float(max_y))
        object.__setattr__(self, "max_z", float(max_z))

    @property
    def minimum(self) -> Point3D:
        return (self.min_x, self.min_y, self.min_z)

    @property
    def maximum(self) -> Point3D:
        return (self.max_x, self.max_y, self.max_z)

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_x": self.min_x,
            "min_y": self.min_y,
            "min_z": self.min_z,
            "max_x": self.max_x,
            "max_y": self.max_y,
            "max_z": self.max_z,
            "minimum": list(self.minimum),
            "maximum": list(self.maximum),
        }

    @classmethod
    def from_dict(cls, data: object) -> MeshBounds:
        if not isinstance(data, Mapping):
            return cls()
        if "minimum" in data or "maximum" in data:
            return cls(
                minimum=_sequence(data.get("minimum", (0.0, 0.0, 0.0))),
                maximum=_sequence(data.get("maximum", (0.0, 0.0, 0.0))),
            )
        return cls(
            min_x=float(data.get("min_x", 0.0)),
            min_y=float(data.get("min_y", 0.0)),
            min_z=float(data.get("min_z", 0.0)),
            max_x=float(data.get("max_x", 0.0)),
            max_y=float(data.get("max_y", 0.0)),
            max_z=float(data.get("max_z", 0.0)),
        )


MeshBoundingBox = MeshBounds


@dataclass(frozen=True, init=False)
class MeshCellBlock:
    """One homogeneous cell block, optionally with summarized connectivity."""

    cell_type: str
    data: tuple[Connectivity, ...]
    count: int
    order: int | None
    metadata: dict[str, Any]

    def __init__(
        self,
        cell_type: str,
        data: Iterable[Sequence[int]] | int | None = None,
        *,
        count: int | None = None,
        order: int | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if isinstance(data, int) and count is None:
            count = data
            data = ()
        normalized_data = tuple(
            tuple(int(index) for index in row)
            for row in (data or ())
        )
        object.__setattr__(self, "cell_type", str(cell_type))
        object.__setattr__(self, "data", normalized_data)
        object.__setattr__(
            self,
            "count",
            int(count) if count is not None else len(normalized_data),
        )
        object.__setattr__(self, "order", int(order) if order is not None else None)
        object.__setattr__(self, "metadata", dict(metadata or {}))

    def to_dict(self, *, include_connectivity: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "cell_type": self.cell_type,
            "count": self.count,
            "order": self.order,
            "metadata": dict(self.metadata),
        }
        if include_connectivity:
            payload["data"] = [list(row) for row in self.data]
        return payload

    @classmethod
    def from_dict(cls, data: object) -> MeshCellBlock:
        if not isinstance(data, Mapping):
            msg = "Mesh cell block must be a mapping."
            raise ValueError(msg)
        return cls(
            str(data.get("cell_type", data.get("type", ""))),
            data.get("data", ()),
            count=_optional_int(data.get("count")),
            order=_optional_int(data.get("order")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True, init=False)
class MeshInfo:
    """Serializable mesh metadata for UI, reports, and ProjectSchema refs."""

    source_path: str
    format: str
    node_count: int
    element_count: int
    cell_blocks: tuple[MeshCellBlock, ...]
    bounds: MeshBounds
    point_data_names: tuple[str, ...]
    cell_data_names: tuple[str, ...]
    field_data_names: tuple[str, ...]
    physical_groups: dict[str, Any]
    warnings: tuple[str, ...]
    metadata: dict[str, Any]

    def __init__(
        self,
        source_path: str = "",
        format: str | MeshFormat = MeshFormat.UNKNOWN,
        node_count: int = 0,
        element_count: int | None = None,
        cell_blocks: Iterable[MeshCellBlock] = (),
        bounds: MeshBounds | None = None,
        point_data_names: Iterable[str] = (),
        cell_data_names: Iterable[str] = (),
        field_data_names: Iterable[str] = (),
        physical_groups: Mapping[str, Any] | None = None,
        warnings: Iterable[str] = (),
        metadata: Mapping[str, Any] | None = None,
        *,
        source: str | None = None,
        nodes: int | None = None,
        elements: int | None = None,
        cell_types: Iterable[str] = (),
        bounding_box: MeshBounds | None = None,
    ) -> None:
        blocks = tuple(cell_blocks)
        if not blocks and cell_types:
            blocks = tuple(MeshCellBlock(cell_type, count=0) for cell_type in cell_types)
        resolved_node_count = int(nodes if nodes is not None else node_count)
        resolved_element_count = (
            int(elements)
            if elements is not None
            else (
                int(element_count)
                if element_count is not None
                else sum(block.count for block in blocks)
            )
        )
        object.__setattr__(self, "source_path", str(source if source is not None else source_path))
        object.__setattr__(self, "format", _format_value(format))
        object.__setattr__(self, "node_count", resolved_node_count)
        object.__setattr__(self, "element_count", resolved_element_count)
        object.__setattr__(self, "cell_blocks", blocks)
        object.__setattr__(self, "bounds", bounds or bounding_box or MeshBounds())
        object.__setattr__(self, "point_data_names", tuple(str(item) for item in point_data_names))
        object.__setattr__(self, "cell_data_names", tuple(str(item) for item in cell_data_names))
        object.__setattr__(self, "field_data_names", tuple(str(item) for item in field_data_names))
        object.__setattr__(self, "physical_groups", dict(physical_groups or {}))
        object.__setattr__(self, "warnings", tuple(str(item) for item in warnings))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def source(self) -> str:
        return self.source_path

    @property
    def nodes(self) -> int:
        return self.node_count

    @property
    def elements(self) -> int:
        return self.element_count

    @property
    def cell_types(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(block.cell_type for block in self.cell_blocks))

    @property
    def bounding_box(self) -> MeshBounds:
        return self.bounds

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "source": self.source_path,
            "format": self.format,
            "node_count": self.node_count,
            "nodes": self.node_count,
            "element_count": self.element_count,
            "elements": self.element_count,
            "cell_blocks": [
                block.to_dict(include_connectivity=False) for block in self.cell_blocks
            ],
            "cell_types": list(self.cell_types),
            "bounds": self.bounds.to_dict(),
            "bounding_box": self.bounds.to_dict(),
            "point_data_names": list(self.point_data_names),
            "cell_data_names": list(self.cell_data_names),
            "field_data_names": list(self.field_data_names),
            "physical_groups": dict(self.physical_groups),
            "warnings": list(self.warnings),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: object) -> MeshInfo:
        if not isinstance(data, Mapping):
            msg = "MeshInfo must be a mapping."
            raise ValueError(msg)
        bounds_payload = data.get("bounds", data.get("bounding_box", {}))
        element_payload = data.get("element_count", data.get("elements"))
        return cls(
            source_path=str(data.get("source_path", data.get("source", ""))),
            format=str(data.get("format", MeshFormat.UNKNOWN.value)),
            node_count=int(data.get("node_count", data.get("nodes", 0)) or 0),
            element_count=(int(element_payload) if element_payload not in (None, "") else None),
            cell_blocks=[
                MeshCellBlock.from_dict(item)
                for item in data.get("cell_blocks", ())
                if isinstance(item, Mapping)
            ],
            bounds=MeshBounds.from_dict(bounds_payload),
            point_data_names=[str(item) for item in data.get("point_data_names", ())],
            cell_data_names=[str(item) for item in data.get("cell_data_names", ())],
            field_data_names=[str(item) for item in data.get("field_data_names", ())],
            physical_groups=dict(data.get("physical_groups", {}) or {}),
            warnings=[str(item) for item in data.get("warnings", ())],
            metadata=dict(data.get("metadata", {}) or {}),
            cell_types=[str(item) for item in data.get("cell_types", ())],
        )


@dataclass(frozen=True)
class MeshData:
    """In-memory mesh payload normalized from meshio-like objects."""

    points: tuple[Point3D, ...]
    cells: tuple[MeshCellBlock, ...]
    point_data: dict[str, Any] = field(default_factory=dict)
    cell_data: dict[str, Any] = field(default_factory=dict)
    field_data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(normalize_point(point) for point in self.points))
        object.__setattr__(self, "cells", tuple(self.cells))
        object.__setattr__(self, "point_data", dict(self.point_data))
        object.__setattr__(self, "cell_data", dict(self.cell_data))
        object.__setattr__(self, "field_data", dict(self.field_data))

    def info(self, source: str, mesh_format: str | MeshFormat) -> MeshInfo:
        return build_mesh_info(
            source=source,
            mesh_format=mesh_format,
            points=self.points,
            cells=self.cells,
            point_data_names=self.point_data.keys(),
            cell_data_names=self.cell_data.keys(),
            field_data_names=self.field_data.keys(),
        )


@dataclass(frozen=True, init=False)
class MeshModel:
    """Lightweight mesh model with optional arrays and required metadata."""

    id: str
    name: str
    info: MeshInfo
    points: tuple[Point3D, ...]
    cells: tuple[MeshCellBlock, ...]
    point_data: dict[str, Any]
    cell_data: dict[str, Any]
    source_path: str

    def __init__(
        self,
        id: str = "",
        name: str = "",
        info: MeshInfo | None = None,
        points: Iterable[Sequence[float]] = (),
        cells: Iterable[MeshCellBlock] = (),
        point_data: Mapping[str, Any] | None = None,
        cell_data: Mapping[str, Any] | None = None,
        source_path: str = "",
    ) -> None:
        normalized_points = tuple(normalize_point(point) for point in points)
        normalized_cells = tuple(cells)
        resolved_info = info or build_mesh_info(
            source=source_path,
            mesh_format=MeshFormat.UNKNOWN,
            points=normalized_points,
            cells=normalized_cells,
            point_data_names=(point_data or {}).keys(),
            cell_data_names=(cell_data or {}).keys(),
        )
        resolved_source = source_path or resolved_info.source_path
        object.__setattr__(self, "id", str(id or _mesh_id_from_source(resolved_source)))
        object.__setattr__(self, "name", str(name or Path(resolved_source).name or self.id))
        object.__setattr__(self, "info", resolved_info)
        object.__setattr__(self, "points", normalized_points)
        object.__setattr__(self, "cells", normalized_cells)
        object.__setattr__(self, "point_data", dict(point_data or {}))
        object.__setattr__(self, "cell_data", dict(cell_data or {}))
        object.__setattr__(self, "source_path", str(resolved_source))

    def to_mesh_data(self) -> MeshData:
        return MeshData(
            points=self.points,
            cells=self.cells,
            point_data=self.point_data,
            cell_data=self.cell_data,
        )

    def to_dict(self, *, include_arrays: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "info": self.info.to_dict(),
            "source_path": self.source_path,
            "point_data_names": list(self.point_data),
            "cell_data_names": list(self.cell_data),
        }
        if include_arrays:
            payload["points"] = [list(point) for point in self.points]
            payload["cells"] = [block.to_dict() for block in self.cells]
        return payload

    @classmethod
    def from_dict(cls, data: object) -> MeshModel:
        if not isinstance(data, Mapping):
            msg = "MeshModel must be a mapping."
            raise ValueError(msg)
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            info=MeshInfo.from_dict(data.get("info", {})),
            points=data.get("points", ()),
            cells=[
                MeshCellBlock.from_dict(item)
                for item in data.get("cells", ())
                if isinstance(item, Mapping)
            ],
            source_path=str(data.get("source_path", "")),
        )


def build_mesh_info(
    *,
    source: str,
    mesh_format: str | MeshFormat,
    points: Iterable[Sequence[float]],
    cells: Iterable[MeshCellBlock],
    point_data_names: Iterable[str] = (),
    cell_data_names: Iterable[str] = (),
    field_data_names: Iterable[str] = (),
    physical_groups: Mapping[str, Any] | None = None,
    warnings: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
) -> MeshInfo:
    """Build stable mesh metadata from normalized points and cell blocks."""

    normalized_points = tuple(normalize_point(point) for point in points)
    normalized_cells = tuple(cells)
    generated_warnings = list(warnings)
    if not normalized_points:
        generated_warnings.append("Mesh contains zero nodes.")
    if not normalized_cells or sum(block.count for block in normalized_cells) == 0:
        generated_warnings.append("Mesh contains zero elements.")
    return MeshInfo(
        source_path=source,
        format=mesh_format,
        node_count=len(normalized_points),
        element_count=sum(block.count for block in normalized_cells),
        cell_blocks=normalized_cells,
        bounds=_bounding_box(normalized_points),
        point_data_names=point_data_names,
        cell_data_names=cell_data_names,
        field_data_names=field_data_names,
        physical_groups=physical_groups,
        warnings=generated_warnings,
        metadata=metadata,
    )


def normalize_point(point: Sequence[float]) -> Point3D:
    """Normalize 2D or 3D meshio points into 3D tuples."""

    values = tuple(float(value) for value in point)
    if len(values) == 2:
        return (values[0], values[1], 0.0)
    if len(values) >= 3:
        return (values[0], values[1], values[2])
    msg = "Mesh point must contain at least two coordinates."
    raise ValueError(msg)


def normalize_cell_block(cell_type: str, data: Iterable[Sequence[int]]) -> MeshCellBlock:
    return MeshCellBlock(cell_type=cell_type, data=data)


def mesh_data_to_model(
    mesh_data: MeshData,
    *,
    source: str = "",
    mesh_format: str | MeshFormat = MeshFormat.UNKNOWN,
    mesh_id: str = "",
    name: str = "",
) -> MeshModel:
    info = mesh_data.info(source, mesh_format)
    return MeshModel(
        id=mesh_id,
        name=name,
        info=info,
        points=mesh_data.points,
        cells=mesh_data.cells,
        point_data=mesh_data.point_data,
        cell_data=mesh_data.cell_data,
        source_path=source,
    )


def _bounding_box(points: tuple[Point3D, ...]) -> MeshBounds:
    if not points:
        return MeshBounds()

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    return MeshBounds(
        min_x=min(xs),
        min_y=min(ys),
        min_z=min(zs),
        max_x=max(xs),
        max_y=max(ys),
        max_z=max(zs),
    )


def _format_value(value: str | MeshFormat) -> str:
    return value.value if isinstance(value, MeshFormat) else str(value)


def _mesh_id_from_source(source: str) -> str:
    stem = Path(source).stem if source else "mesh"
    slug = "".join(char.lower() if char.isalnum() else "-" for char in stem).strip("-")
    return slug or "mesh"


def _sequence(value: object) -> Sequence[float]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        return value  # type: ignore[return-value]
    return (0.0, 0.0, 0.0)


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
