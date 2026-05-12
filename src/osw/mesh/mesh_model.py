"""Small mesh metadata model used by mesh import previews."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

Point3D = tuple[float, float, float]
Connectivity = tuple[int, ...]


@dataclass(frozen=True)
class MeshBoundingBox:
    """Axis-aligned bounds for imported mesh points."""

    minimum: Point3D
    maximum: Point3D


@dataclass(frozen=True)
class MeshCellBlock:
    """One homogeneous element block."""

    cell_type: str
    data: tuple[Connectivity, ...]

    @property
    def count(self) -> int:
        return len(self.data)


@dataclass(frozen=True)
class MeshInfo:
    """Preview-safe mesh metadata for UI, reports, and validation logs."""

    source: str
    format: str
    nodes: int
    elements: int
    cell_types: tuple[str, ...]
    bounding_box: MeshBoundingBox

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "format": self.format,
            "nodes": self.nodes,
            "elements": self.elements,
            "cell_types": list(self.cell_types),
            "bounding_box": {
                "minimum": list(self.bounding_box.minimum),
                "maximum": list(self.bounding_box.maximum),
            },
        }


@dataclass(frozen=True)
class MeshData:
    """In-memory mesh payload normalized from meshio-like objects."""

    points: tuple[Point3D, ...]
    cells: tuple[MeshCellBlock, ...]
    point_data: dict[str, Any] = field(default_factory=dict)
    cell_data: dict[str, Any] = field(default_factory=dict)

    def info(self, source: str, mesh_format: str) -> MeshInfo:
        return build_mesh_info(
            source=source,
            mesh_format=mesh_format,
            points=self.points,
            cells=self.cells,
        )


def build_mesh_info(
    *,
    source: str,
    mesh_format: str,
    points: Iterable[Sequence[float]],
    cells: Iterable[MeshCellBlock],
) -> MeshInfo:
    """Build stable mesh metadata from normalized points and cell blocks."""

    normalized_points = tuple(normalize_point(point) for point in points)
    normalized_cells = tuple(cells)
    return MeshInfo(
        source=source,
        format=mesh_format,
        nodes=len(normalized_points),
        elements=sum(block.count for block in normalized_cells),
        cell_types=_cell_types(normalized_cells),
        bounding_box=_bounding_box(normalized_points),
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
    return MeshCellBlock(
        cell_type=cell_type,
        data=tuple(tuple(int(index) for index in row) for row in data),
    )


def _bounding_box(points: tuple[Point3D, ...]) -> MeshBoundingBox:
    if not points:
        zero = (0.0, 0.0, 0.0)
        return MeshBoundingBox(minimum=zero, maximum=zero)

    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    return MeshBoundingBox(
        minimum=(min(xs), min(ys), min(zs)),
        maximum=(max(xs), max(ys), max(zs)),
    )


def _cell_types(cells: Iterable[MeshCellBlock]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for block in cells:
        if block.cell_type not in seen:
            ordered.append(block.cell_type)
            seen.add(block.cell_type)
    return tuple(ordered)
