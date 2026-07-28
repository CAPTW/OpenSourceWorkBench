"""Report-friendly mesh quality metrics for normalized mesh previews."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from itertools import combinations
from math import dist, isfinite
from typing import Any, Literal

from .identity import MeshFingerprint, MeshIdentityError, compute_mesh_fingerprint
from .mesh_model import MeshBoundingBox, MeshData, Point3D, build_mesh_info

Severity = Literal["warning", "info"]
MESH_QUALITY_METRIC_SCHEMA = "osw.mesh_quality.edge_aspect_ratio.v1"
MESH_QUALITY_METRIC_LABEL = "Edge aspect ratio preview"
MESH_QUALITY_TOPOLOGY_RULES = "osw.mesh_quality.linear_topology_edges.v1"
_CELL_ORDINAL_NAMESPACE = "osw.mesh.cell_block_ordinal.v1"

_LINEAR_TOPOLOGY_EDGES: dict[str, tuple[tuple[int, int], ...]] = {
    "line": ((0, 1),),
    "triangle": ((0, 1), (1, 2), (2, 0)),
    "quad": ((0, 1), (1, 2), (2, 3), (3, 0)),
    "tetra": ((0, 1), (1, 2), (2, 0), (0, 3), (1, 3), (2, 3)),
    "hexahedron": (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (4, 5),
        (5, 6),
        (6, 7),
        (7, 4),
        (0, 4),
        (1, 5),
        (2, 6),
        (3, 7),
    ),
    "wedge": (
        (0, 1),
        (1, 2),
        (2, 0),
        (3, 4),
        (4, 5),
        (5, 3),
        (0, 3),
        (1, 4),
        (2, 5),
    ),
    "pyramid": (
        (0, 1),
        (1, 2),
        (2, 3),
        (3, 0),
        (0, 4),
        (1, 4),
        (2, 4),
        (3, 4),
    ),
}
_HIGH_ORDER_CELL_TYPES = frozenset(
    {
        "line3",
        "triangle6",
        "quad8",
        "quad9",
        "tetra10",
        "hexahedron20",
    }
)


class MeshQualityAnalysisError(ValueError):
    """Per-cell diagnostics could not bind safely to exact mesh identity."""


class MeshCellQualityStatus(StrEnum):
    """Fail-closed state of one per-cell preview metric record."""

    EVALUATED = "EVALUATED"
    DEGENERATE = "DEGENERATE"
    INVALID = "INVALID"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True)
class MeshCellQualityRecord:
    """One stable, fingerprint-bound cell metric result."""

    mesh_fingerprint: str
    entity_kind: str
    id_namespace: str
    stable_cell_key: str
    cell_type: str
    block_ordinal: int
    cell_ordinal: int
    metric_schema: str
    value: float | None
    status: MeshCellQualityStatus
    reason: str


@dataclass(frozen=True)
class MeshQualityAnalysis:
    """Immutable deterministic per-cell preview analysis."""

    mesh_fingerprint: MeshFingerprint
    metric_schema: str
    metric_label: str
    topology_rules_version: str
    zero_edge_tolerance: float
    node_count: int
    cell_count: int
    cell_type_distribution: dict[str, int]
    bounding_box: MeshBoundingBox
    evaluated_count: int
    unsupported_count: int
    invalid_count: int
    degenerate_count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    records: tuple[MeshCellQualityRecord, ...]
    diagnostics: tuple[str, ...] = ()


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


def analyze_mesh_cell_quality(
    mesh_data: MeshData,
    *,
    zero_edge_tolerance: float = 1e-12,
) -> MeshQualityAnalysis:
    """Evaluate explicit linear-topology edges for each fingerprint-bound cell."""

    tolerance = float(zero_edge_tolerance)
    if not isfinite(tolerance) or tolerance < 0.0:
        msg = "Zero edge tolerance must be finite and non-negative."
        raise ValueError(msg)
    try:
        fingerprint = compute_mesh_fingerprint(mesh_data)
    except MeshIdentityError as exc:
        raise MeshQualityAnalysisError(
            "Mesh Diagnostics requires an exact mesh fingerprint; "
            "the in-memory geometry or connectivity is invalid."
        ) from exc

    info = build_mesh_info(
        source="in-memory",
        mesh_format="normalized",
        points=mesh_data.points,
        cells=mesh_data.cells,
    )
    records: list[MeshCellQualityRecord] = []
    values: list[float] = []
    diagnostics: list[str] = []
    for block_ordinal, block in enumerate(mesh_data.cells):
        cell_type = str(block.cell_type or "").strip().lower()
        for cell_ordinal, connectivity in enumerate(block.data):
            stable_key = f"{block_ordinal}:{cell_ordinal}"
            record = _analyze_cell(
                mesh_data.points,
                connectivity,
                mesh_fingerprint=fingerprint.digest,
                stable_cell_key=stable_key,
                cell_type=cell_type,
                block_ordinal=block_ordinal,
                cell_ordinal=cell_ordinal,
                zero_edge_tolerance=tolerance,
            )
            records.append(record)
            if record.value is not None:
                values.append(record.value)

    unsupported_count = sum(
        record.status is MeshCellQualityStatus.UNSUPPORTED for record in records
    )
    invalid_count = sum(
        record.status is MeshCellQualityStatus.INVALID for record in records
    )
    degenerate_count = sum(
        record.status is MeshCellQualityStatus.DEGENERATE for record in records
    )
    if unsupported_count:
        diagnostics.append(
            f"{unsupported_count} cell(s) use unsupported topology and were not evaluated."
        )
    if invalid_count:
        diagnostics.append(
            f"{invalid_count} cell(s) have invalid topology and were not evaluated."
        )
    if degenerate_count:
        diagnostics.append(
            f"{degenerate_count} cell(s) contain a zero or near-zero topological edge."
        )

    return MeshQualityAnalysis(
        mesh_fingerprint=fingerprint,
        metric_schema=MESH_QUALITY_METRIC_SCHEMA,
        metric_label=MESH_QUALITY_METRIC_LABEL,
        topology_rules_version=MESH_QUALITY_TOPOLOGY_RULES,
        zero_edge_tolerance=tolerance,
        node_count=info.nodes,
        cell_count=info.elements,
        cell_type_distribution=_cell_type_distribution(mesh_data),
        bounding_box=info.bounding_box,
        evaluated_count=len(values),
        unsupported_count=unsupported_count,
        invalid_count=invalid_count,
        degenerate_count=degenerate_count,
        minimum=min(values) if values else None,
        maximum=max(values) if values else None,
        mean=sum(values) / len(values) if values else None,
        records=tuple(records),
        diagnostics=tuple(diagnostics),
    )


def derive_bad_cell_records(
    analysis: MeshQualityAnalysis,
    *,
    threshold: float,
) -> tuple[MeshCellQualityRecord, ...]:
    """Derive one deterministic bad/degenerate subset without geometry work."""

    normalized = float(threshold)
    if not isfinite(normalized) or normalized <= 0.0:
        msg = "Bad-cell threshold must be finite and positive."
        raise ValueError(msg)
    return tuple(
        record
        for record in analysis.records
        if record.status is MeshCellQualityStatus.DEGENERATE
        or (
            record.status is MeshCellQualityStatus.EVALUATED
            and record.value is not None
            and record.value > normalized
        )
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
    if info.nodes == 0:
        warnings.append(MeshQualityWarning("zero_nodes", "Mesh contains zero nodes."))
    if info.elements == 0:
        warnings.append(MeshQualityWarning("zero_elements", "Mesh contains zero elements."))

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


def _analyze_cell(
    points: tuple[Point3D, ...],
    connectivity: tuple[int, ...],
    *,
    mesh_fingerprint: str,
    stable_cell_key: str,
    cell_type: str,
    block_ordinal: int,
    cell_ordinal: int,
    zero_edge_tolerance: float,
) -> MeshCellQualityRecord:
    if cell_type in _HIGH_ORDER_CELL_TYPES:
        return _cell_record(
            mesh_fingerprint,
            stable_cell_key,
            cell_type,
            block_ordinal,
            cell_ordinal,
            MeshCellQualityStatus.UNSUPPORTED,
            "UNSUPPORTED_HIGH_ORDER_TOPOLOGY",
        )
    edge_pairs = _LINEAR_TOPOLOGY_EDGES.get(cell_type)
    if edge_pairs is None:
        return _cell_record(
            mesh_fingerprint,
            stable_cell_key,
            cell_type,
            block_ordinal,
            cell_ordinal,
            MeshCellQualityStatus.UNSUPPORTED,
            "UNSUPPORTED_CELL_TYPE",
        )

    required_nodes = max(max(pair) for pair in edge_pairs) + 1
    if len(connectivity) < required_nodes:
        return _cell_record(
            mesh_fingerprint,
            stable_cell_key,
            cell_type,
            block_ordinal,
            cell_ordinal,
            MeshCellQualityStatus.INVALID,
            "INSUFFICIENT_CONNECTIVITY",
        )
    if len(connectivity) != required_nodes:
        return _cell_record(
            mesh_fingerprint,
            stable_cell_key,
            cell_type,
            block_ordinal,
            cell_ordinal,
            MeshCellQualityStatus.INVALID,
            "INVALID_CONNECTIVITY",
        )

    edge_lengths = tuple(
        dist(points[connectivity[start]], points[connectivity[end]])
        for start, end in edge_pairs
    )
    if not all(isfinite(length) for length in edge_lengths):
        return _cell_record(
            mesh_fingerprint,
            stable_cell_key,
            cell_type,
            block_ordinal,
            cell_ordinal,
            MeshCellQualityStatus.INVALID,
            "NONFINITE_EDGE_LENGTH",
        )
    minimum = min(edge_lengths)
    if minimum <= zero_edge_tolerance:
        return _cell_record(
            mesh_fingerprint,
            stable_cell_key,
            cell_type,
            block_ordinal,
            cell_ordinal,
            MeshCellQualityStatus.DEGENERATE,
            "ZERO_OR_NEAR_ZERO_EDGE",
        )
    ratio = max(edge_lengths) / minimum
    if not isfinite(ratio) or ratio < 1.0:
        return _cell_record(
            mesh_fingerprint,
            stable_cell_key,
            cell_type,
            block_ordinal,
            cell_ordinal,
            MeshCellQualityStatus.INVALID,
            "NONFINITE_EDGE_ASPECT_RATIO",
        )
    return _cell_record(
        mesh_fingerprint,
        stable_cell_key,
        cell_type,
        block_ordinal,
        cell_ordinal,
        MeshCellQualityStatus.EVALUATED,
        "EVALUATED",
        value=ratio,
    )


def _cell_record(
    mesh_fingerprint: str,
    stable_cell_key: str,
    cell_type: str,
    block_ordinal: int,
    cell_ordinal: int,
    status: MeshCellQualityStatus,
    reason: str,
    *,
    value: float | None = None,
) -> MeshCellQualityRecord:
    return MeshCellQualityRecord(
        mesh_fingerprint=mesh_fingerprint,
        entity_kind="cell",
        id_namespace=_CELL_ORDINAL_NAMESPACE,
        stable_cell_key=stable_cell_key,
        cell_type=cell_type,
        block_ordinal=block_ordinal,
        cell_ordinal=cell_ordinal,
        metric_schema=MESH_QUALITY_METRIC_SCHEMA,
        value=value,
        status=status,
        reason=reason,
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


__all__ = [
    "MESH_QUALITY_METRIC_LABEL",
    "MESH_QUALITY_METRIC_SCHEMA",
    "MESH_QUALITY_TOPOLOGY_RULES",
    "MeshCellQualityRecord",
    "MeshCellQualityStatus",
    "MeshQualityAnalysis",
    "MeshQualityAnalysisError",
    "MeshQualityMetrics",
    "MeshQualityWarning",
    "analyze_mesh_cell_quality",
    "analyze_mesh_quality",
    "derive_bad_cell_records",
]
