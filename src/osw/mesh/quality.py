"""Report-friendly mesh quality metrics for normalized mesh previews."""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from math import dist
from typing import Any, Literal

from .mesh_model import MeshBoundingBox, MeshData, Point3D, build_mesh_info

Severity = Literal["warning", "info"]


@dataclass(frozen=True)
class MeshQualityWarning:
    code: str
    message: str
    severity: Severity = "warning"
    cell_type: str = ""
    element_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
            "cell_type": self.cell_type,
            "element_index": self.element_index,
        }


@dataclass(frozen=True)
class MeshQualityMetrics:
    node_count: int
    element_count: int
    cell_type_distribution: dict[str, int]
    bounding_box: MeshBoundingBox
    min_edge_length: float | None = None
    max_edge_length: float | None = None
    min_aspect_ratio: float | None = None
    max_aspect_ratio: float | None = None
    mean_aspect_ratio: float | None = None
    warnings: tuple[MeshQualityWarning, ...] = field(default_factory=tuple)

    @property
    def has_warnings(self) -> bool:
        return bool(self.warnings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_count": self.node_count,
            "element_count": self.element_count,
            "cell_type_distribution": dict(self.cell_type_distribution),
            "bounding_box": {
                "minimum": list(self.bounding_box.minimum),
                "maximum": list(self.bounding_box.maximum),
            },
            "min_edge_length": self.min_edge_length,
            "max_edge_length": self.max_edge_length,
            "min_aspect_ratio": self.min_aspect_ratio,
            "max_aspect_ratio": self.max_aspect_ratio,
            "mean_aspect_ratio": self.mean_aspect_ratio,
            "warnings": [warning.to_dict() for warning in self.warnings],
        }

    def report_lines(self) -> tuple[str, ...]:
        edge_summary = (
            f"edge_length={self.min_edge_length:g}..{self.max_edge_length:g}"
            if self.min_edge_length is not None and self.max_edge_length is not None
            else "edge_length=unavailable"
        )
        aspect_summary = (
            f"aspect_ratio={self.min_aspect_ratio:g}..{self.max_aspect_ratio:g}"
            if self.min_aspect_ratio is not None and self.max_aspect_ratio is not None
            else "aspect_ratio=unavailable"
        )
        return (
            f"nodes={self.node_count}",
            f"elements={self.element_count}",
            f"cell_types={_format_distribution(self.cell_type_distribution)}",
            (
                "bounding_box="
                f"{self.bounding_box.minimum} -> {self.bounding_box.maximum}"
            ),
            edge_summary,
            aspect_summary,
            f"warnings={len(self.warnings)}",
        )


def analyze_mesh_quality(
    mesh_data: MeshData,
    *,
    bad_aspect_ratio_threshold: float = 10.0,
    zero_edge_tolerance: float = 1e-12,
) -> MeshQualityMetrics:
    """Compute lightweight mesh quality metrics for preview and reports."""

    if bad_aspect_ratio_threshold <= 0:
        msg = "Bad aspect ratio threshold must be positive."
        raise ValueError(msg)
    if zero_edge_tolerance < 0:
        msg = "Zero edge tolerance must be non-negative."
        raise ValueError(msg)

    info = build_mesh_info(
        source="in-memory",
        mesh_format="normalized",
        points=mesh_data.points,
        cells=mesh_data.cells,
    )
    edge_lengths: list[float] = []
    aspect_ratios: list[float] = []
    warnings: list[MeshQualityWarning] = []

    for block in mesh_data.cells:
        for local_index, connectivity in enumerate(block.data):
            try:
                element_edges = _element_edge_lengths(mesh_data.points, connectivity)
            except ValueError as exc:
                warnings.append(
                    MeshQualityWarning(
                        code="invalid_connectivity",
                        message=str(exc),
                        cell_type=block.cell_type,
                        element_index=local_index,
                    )
                )
                continue

            if not element_edges:
                warnings.append(
                    MeshQualityWarning(
                        code="insufficient_connectivity",
                        message="Element has fewer than two valid nodes.",
                        cell_type=block.cell_type,
                        element_index=local_index,
                    )
                )
                continue

            edge_lengths.extend(element_edges)
            min_edge = min(element_edges)
            max_edge = max(element_edges)
            if min_edge <= zero_edge_tolerance:
                warnings.append(
                    MeshQualityWarning(
                        code="degenerate_edge",
                        message="Element contains a near-zero edge length.",
                        cell_type=block.cell_type,
                        element_index=local_index,
                    )
                )
                continue

            aspect_ratio = max_edge / min_edge
            aspect_ratios.append(aspect_ratio)
            if aspect_ratio > bad_aspect_ratio_threshold:
                warnings.append(
                    MeshQualityWarning(
                        code="high_aspect_ratio",
                        message=(
                            f"Element aspect ratio {aspect_ratio:g} exceeds threshold "
                            f"{bad_aspect_ratio_threshold:g}."
                        ),
                        cell_type=block.cell_type,
                        element_index=local_index,
                    )
                )

    return MeshQualityMetrics(
        node_count=info.nodes,
        element_count=info.elements,
        cell_type_distribution=_cell_type_distribution(mesh_data),
        bounding_box=info.bounding_box,
        min_edge_length=min(edge_lengths) if edge_lengths else None,
        max_edge_length=max(edge_lengths) if edge_lengths else None,
        min_aspect_ratio=min(aspect_ratios) if aspect_ratios else None,
        max_aspect_ratio=max(aspect_ratios) if aspect_ratios else None,
        mean_aspect_ratio=(
            sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else None
        ),
        warnings=tuple(warnings),
    )


def _cell_type_distribution(mesh_data: MeshData) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for block in mesh_data.cells:
        distribution[block.cell_type] = distribution.get(block.cell_type, 0) + block.count
    return distribution


def _element_edge_lengths(
    points: tuple[Point3D, ...],
    connectivity: tuple[int, ...],
) -> tuple[float, ...]:
    if len(connectivity) < 2:
        return ()

    invalid = [index for index in connectivity if index < 0 or index >= len(points)]
    if invalid:
        msg = f"Element references node index outside mesh point range: {invalid[0]}"
        raise ValueError(msg)

    return tuple(
        dist(points[start], points[end])
        for start, end in combinations(connectivity, 2)
    )


def _format_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "none"
    return ", ".join(f"{cell_type}:{count}" for cell_type, count in sorted(distribution.items()))
