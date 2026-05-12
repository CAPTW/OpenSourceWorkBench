"""Preview-safe geometry metadata model for standard CAD imports."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

Point3D = tuple[float, float, float]


@dataclass(frozen=True)
class GeometryBoundingBox:
    """Axis-aligned bounds for geometry preview vertices."""

    minimum: Point3D
    maximum: Point3D


@dataclass(frozen=True)
class GeometryBody:
    """A lightweight body placeholder for preview and report surfaces."""

    name: str
    kind: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GeometryModel:
    """Minimal geometry import preview model."""

    source: str
    format: str
    bodies: tuple[GeometryBody, ...]
    bounding_box: GeometryBoundingBox
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()

    @property
    def body_count(self) -> int:
        return len(self.bodies)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "format": self.format,
            "body_count": self.body_count,
            "bodies": [
                {"name": body.name, "kind": body.kind, "metadata": body.metadata}
                for body in self.bodies
            ],
            "bounding_box": {
                "minimum": list(self.bounding_box.minimum),
                "maximum": list(self.bounding_box.maximum),
            },
            "metadata": self.metadata,
            "warnings": list(self.warnings),
        }


def build_geometry_model(
    *,
    source: str,
    geometry_format: str,
    vertices: Iterable[Sequence[float]],
    bodies: Iterable[GeometryBody],
    metadata: dict[str, Any] | None = None,
    warnings: Iterable[str] = (),
) -> GeometryModel:
    normalized_vertices = tuple(normalize_point(vertex) for vertex in vertices)
    return GeometryModel(
        source=source,
        format=geometry_format,
        bodies=tuple(bodies),
        bounding_box=_bounding_box(normalized_vertices),
        metadata=dict(metadata or {}),
        warnings=tuple(warnings),
    )


def normalize_point(point: Sequence[float]) -> Point3D:
    values = tuple(float(value) for value in point)
    if len(values) == 2:
        return (values[0], values[1], 0.0)
    if len(values) >= 3:
        return (values[0], values[1], values[2])
    msg = "Geometry point must contain at least two coordinates."
    raise ValueError(msg)


def empty_bounding_box() -> GeometryBoundingBox:
    zero = (0.0, 0.0, 0.0)
    return GeometryBoundingBox(minimum=zero, maximum=zero)


def _bounding_box(vertices: tuple[Point3D, ...]) -> GeometryBoundingBox:
    if not vertices:
        return empty_bounding_box()

    xs = [vertex[0] for vertex in vertices]
    ys = [vertex[1] for vertex in vertices]
    zs = [vertex[2] for vertex in vertices]
    return GeometryBoundingBox(
        minimum=(min(xs), min(ys), min(zs)),
        maximum=(max(xs), max(ys), max(zs)),
    )
