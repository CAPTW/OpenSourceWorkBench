"""Deterministic, renderer-neutral summaries for in-memory meshes."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, sqrt

from .identity import MeshFingerprint, compute_mesh_fingerprint
from .mesh_model import MeshBounds, MeshData

MESH_DIAGNOSTICS_SCHEMA = "osw.mesh_diagnostics.v1"
QUALITY_SUPPORTED_CELL_TYPES = frozenset({"triangle", "quad", "tetra"})
SURFACE_CELL_TYPES = frozenset({"triangle", "quad", "polygon"})
VOLUME_CELL_TYPES = frozenset(
    {"tetra", "tetra10", "hexahedron", "hexahedron20", "wedge", "pyramid"}
)

_EXACT_NODE_COUNTS = {
    "triangle": 3,
    "quad": 4,
    "tetra": 4,
    "tetra10": 10,
    "hexahedron": 8,
    "hexahedron20": 20,
    "wedge": 6,
    "pyramid": 5,
}


@dataclass(frozen=True, slots=True)
class MeshSummary:
    """Stable structural summary used by diagnostics, GUI, and exports."""

    schema: str
    mesh_fingerprint: MeshFingerprint
    point_count: int
    cell_count: int
    block_count: int
    cell_type_distribution: tuple[tuple[str, int], ...]
    surface_cell_count: int
    volume_cell_count: int
    quality_supported_count: int
    quality_uncovered_count: int
    invalid_cell_count: int
    bounds: MeshBounds
    extents: tuple[float, float, float]
    diagonal: float
    finite_point_count: int
    nonfinite_point_count: int
    referenced_point_count: int
    orphan_point_count: int
    supported_quality_types: tuple[str, ...]
    uncovered_quality_types: tuple[str, ...]

    @property
    def mesh_fingerprint_digest(self) -> str:
        return self.mesh_fingerprint.digest


def build_mesh_summary(mesh: MeshData) -> MeshSummary:
    """Summarize one mesh without changing its geometry or data arrays."""

    fingerprint = compute_mesh_fingerprint(mesh)
    point_count = len(mesh.points)
    finite_points = tuple(
        point for point in mesh.points if all(isfinite(component) for component in point)
    )
    bounds = _finite_bounds(finite_points)
    extents = tuple(
        maximum - minimum for minimum, maximum in zip(bounds.minimum, bounds.maximum, strict=True)
    )
    distribution: dict[str, int] = {}
    referenced: set[int] = set()
    surface_count = 0
    volume_count = 0
    supported_count = 0
    uncovered_count = 0
    invalid_count = 0
    supported_types: set[str] = set()
    uncovered_types: set[str] = set()
    cell_count = 0

    for block in mesh.cells:
        cell_type = str(block.cell_type or "").strip().lower()
        rows = tuple(block.data)
        declared_count = max(int(block.count), 0)
        distribution[cell_type] = distribution.get(cell_type, 0) + declared_count
        cell_count += declared_count
        missing_rows = max(0, declared_count - len(rows))
        invalid_count += missing_rows
        for connectivity in rows[:declared_count]:
            for point_index in connectivity:
                if 0 <= point_index < point_count:
                    referenced.add(point_index)
            invalid = not _valid_connectivity(
                cell_type,
                connectivity,
                point_count=point_count,
                points=mesh.points,
            )
            invalid_count += int(invalid)
            if cell_type in QUALITY_SUPPORTED_CELL_TYPES:
                supported_count += 1
                supported_types.add(cell_type)
            else:
                uncovered_count += 1
                uncovered_types.add(cell_type or "unknown")
            if cell_type in SURFACE_CELL_TYPES:
                surface_count += 1
            elif cell_type in VOLUME_CELL_TYPES:
                volume_count += 1
        if missing_rows:
            if cell_type in QUALITY_SUPPORTED_CELL_TYPES:
                supported_count += missing_rows
                supported_types.add(cell_type)
            else:
                uncovered_count += missing_rows
                uncovered_types.add(cell_type or "unknown")
            if cell_type in SURFACE_CELL_TYPES:
                surface_count += missing_rows
            elif cell_type in VOLUME_CELL_TYPES:
                volume_count += missing_rows

    return MeshSummary(
        schema=MESH_DIAGNOSTICS_SCHEMA,
        mesh_fingerprint=fingerprint,
        point_count=point_count,
        cell_count=cell_count,
        block_count=len(mesh.cells),
        cell_type_distribution=tuple(sorted(distribution.items())),
        surface_cell_count=surface_count,
        volume_cell_count=volume_count,
        quality_supported_count=supported_count,
        quality_uncovered_count=uncovered_count,
        invalid_cell_count=invalid_count,
        bounds=bounds,
        extents=extents,
        diagonal=sqrt(sum(component * component for component in extents)),
        finite_point_count=len(finite_points),
        nonfinite_point_count=point_count - len(finite_points),
        referenced_point_count=len(referenced),
        orphan_point_count=point_count - len(referenced),
        supported_quality_types=tuple(sorted(supported_types)),
        uncovered_quality_types=tuple(sorted(uncovered_types)),
    )


def cell_connectivity_is_valid(
    mesh: MeshData,
    cell_type: str,
    connectivity: tuple[int, ...],
) -> bool:
    """Return whether one row is safe for the retained quality provider."""

    return _valid_connectivity(
        str(cell_type or "").strip().lower(),
        connectivity,
        point_count=len(mesh.points),
        points=mesh.points,
    )


def _valid_connectivity(
    cell_type: str,
    connectivity: tuple[int, ...],
    *,
    point_count: int,
    points: tuple[tuple[float, float, float], ...],
) -> bool:
    expected = _EXACT_NODE_COUNTS.get(cell_type)
    if expected is not None and len(connectivity) != expected:
        return False
    if cell_type == "polygon" and len(connectivity) < 3:
        return False
    if not connectivity:
        return False
    if any(index < 0 or index >= point_count for index in connectivity):
        return False
    return all(all(isfinite(component) for component in points[index]) for index in connectivity)


def _finite_bounds(
    points: tuple[tuple[float, float, float], ...],
) -> MeshBounds:
    if not points:
        return MeshBounds()
    minimum = tuple(min(point[axis] for point in points) for axis in range(3))
    maximum = tuple(max(point[axis] for point in points) for axis in range(3))
    return MeshBounds(minimum=minimum, maximum=maximum)


__all__ = [
    "MESH_DIAGNOSTICS_SCHEMA",
    "QUALITY_SUPPORTED_CELL_TYPES",
    "SURFACE_CELL_TYPES",
    "VOLUME_CELL_TYPES",
    "MeshSummary",
    "build_mesh_summary",
    "cell_connectivity_is_valid",
]
