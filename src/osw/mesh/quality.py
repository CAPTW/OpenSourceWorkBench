"""Deterministic cell-quality diagnostics for normalized in-memory meshes.

The product-facing metric is the retained VTK/PyVista Scaled Jacobian. The
provider is lazy and optional; identity, coverage, classification, statistics,
and export-facing records remain renderer-neutral.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from enum import StrEnum
from itertools import combinations
from math import dist, isfinite
from statistics import fmean, median, pstdev
from typing import Any, Literal, Protocol

from .diagnostics import (
    QUALITY_SUPPORTED_CELL_TYPES,
    MeshSummary,
    build_mesh_summary,
    cell_connectivity_is_valid,
)
from .identity import MeshFingerprint, MeshIdentityError
from .mesh_model import MeshBoundingBox, MeshCellBlock, MeshData, Point3D, build_mesh_info

Severity = Literal["warning", "info"]
MESH_QUALITY_METRIC_SCHEMA = "osw.mesh_quality.scaled_jacobian.v1"
MESH_QUALITY_METRIC_LABEL = "Scaled Jacobian"
MESH_QUALITY_TOPOLOGY_RULES = "osw.mesh_quality.scaled_jacobian.topology.v1"
MESH_QUALITY_RESULT_SCHEMA = "osw.mesh_diagnostics.v1"
MESH_QUALITY_METRIC_DIRECTION = "higher_is_better"
MESH_QUALITY_METRIC_SEMANTICS = (
    "Higher is better; negative values indicate inverted orientation for topology "
    "where orientation is defined; values near zero indicate degeneracy or severe "
    "distortion."
)
DEFAULT_MESH_QUALITY_THRESHOLD = 0.0
DEFAULT_DEGENERATE_EPSILON = 1.0e-12
_CELL_ORDINAL_NAMESPACE = "osw.mesh.cell_block_ordinal.v1"


class MeshQualityAnalysisError(ValueError):
    """Per-cell diagnostics could not bind safely to exact mesh identity."""


class MeshQualityProviderUnavailableError(RuntimeError):
    """The optional retained quality provider is not importable or usable."""


class MeshQualityProviderError(RuntimeError):
    """The retained quality provider failed after becoming available."""


class MeshDiagnosticsStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    READY = "ready"
    PARTIAL_COVERAGE = "partial_coverage"
    STALE = "stale"
    UNAVAILABLE_OPTIONAL_DEPENDENCY = "unavailable_optional_dependency"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MeshCellQualityStatus(StrEnum):
    """Provider/coverage state of one canonical cell record."""

    EVALUATED = "EVALUATED"
    INVALID = "INVALID"
    UNCOVERED = "UNCOVERED"
    UNAVAILABLE = "UNAVAILABLE"
    # Compatibility values for readers of the former preview schema.
    DEGENERATE = "DEGENERATE"
    UNSUPPORTED = "UNCOVERED"


class MeshQualityCategory(StrEnum):
    INVERTED = "inverted"
    DEGENERATE = "degenerate"
    THRESHOLD_BAD = "threshold_bad"
    ACCEPTABLE = "acceptable"
    INVALID = "invalid"
    UNCOVERED = "uncovered"
    UNAVAILABLE = "unavailable"


class ScaledJacobianProvider(Protocol):
    provider_schema: str
    provider_version: str

    def evaluate(self, mesh: MeshData) -> Sequence[float]: ...


@dataclass(frozen=True, slots=True)
class MeshCellQualityRecord:
    """One fingerprint-bound metric result in canonical block/local order."""

    mesh_fingerprint: str
    entity_kind: str
    id_namespace: str
    stable_cell_key: str
    backend_index: int
    cell_type: str
    block_ordinal: int
    cell_ordinal: int
    metric_schema: str
    value: float | None
    status: MeshCellQualityStatus
    category: MeshQualityCategory
    is_bad: bool
    reason: str


@dataclass(frozen=True, slots=True)
class MeshQualityStatistics:
    count: int = 0
    minimum: float | None = None
    maximum: float | None = None
    mean: float | None = None
    median: float | None = None
    population_stddev: float | None = None
    p05: float | None = None
    p25: float | None = None
    p75: float | None = None
    p95: float | None = None
    # NumPy ``percentile(method="linear")`` semantics, implemented locally so
    # renderer-neutral unit tests do not gain a mandatory NumPy dependency.
    percentile_method: str = "linear"


@dataclass(frozen=True, slots=True)
class MeshTopologyQualitySummary:
    cell_type: str
    total_count: int
    covered_count: int
    uncovered_count: int
    invalid_count: int
    bad_count: int
    statistics: MeshQualityStatistics


@dataclass(frozen=True, slots=True)
class MeshQualityAnalysis:
    """Immutable, deterministic mesh-diagnostics result."""

    schema: str
    status: MeshDiagnosticsStatus
    mesh_ref: str
    mesh_summary: MeshSummary
    metric_schema: str
    metric_label: str
    metric_direction: str
    metric_semantics: str
    topology_rules_version: str
    provider_schema: str
    provider_version: str
    threshold: float
    degenerate_epsilon: float
    range_mode: str
    display_range: tuple[float, float]
    covered_count: int
    uncovered_count: int
    invalid_count: int
    unavailable_count: int
    bad_count: int
    statistics: MeshQualityStatistics
    topology_summaries: tuple[MeshTopologyQualitySummary, ...]
    records: tuple[MeshCellQualityRecord, ...]
    digest: str
    diagnostics: tuple[str, ...] = ()

    @property
    def mesh_fingerprint(self) -> MeshFingerprint:
        return self.mesh_summary.mesh_fingerprint

    @property
    def node_count(self) -> int:
        return self.mesh_summary.point_count

    @property
    def cell_count(self) -> int:
        return self.mesh_summary.cell_count

    @property
    def cell_type_distribution(self) -> dict[str, int]:
        return dict(self.mesh_summary.cell_type_distribution)

    @property
    def bounding_box(self) -> MeshBoundingBox:
        return self.mesh_summary.bounds

    @property
    def evaluated_count(self) -> int:
        return self.covered_count

    @property
    def unsupported_count(self) -> int:
        return self.uncovered_count

    @property
    def degenerate_count(self) -> int:
        return sum(record.category is MeshQualityCategory.DEGENERATE for record in self.records)

    @property
    def minimum(self) -> float | None:
        return self.statistics.minimum

    @property
    def maximum(self) -> float | None:
        return self.statistics.maximum

    @property
    def mean(self) -> float | None:
        return self.statistics.mean

    @property
    def zero_edge_tolerance(self) -> float:
        return self.degenerate_epsilon

    @property
    def bad_cell_keys(self) -> tuple[str, ...]:
        return tuple(record.stable_cell_key for record in self.records if record.is_bad)


def analyze_mesh_cell_quality(
    mesh_data: MeshData,
    *,
    threshold: float = DEFAULT_MESH_QUALITY_THRESHOLD,
    degenerate_epsilon: float = DEFAULT_DEGENERATE_EPSILON,
    zero_edge_tolerance: float | None = None,
    range_mode: str = "auto",
    manual_range: tuple[float, float] | None = None,
    provider: ScaledJacobianProvider | None = None,
) -> MeshQualityAnalysis:
    """Evaluate supported linear cells with the retained Scaled Jacobian provider."""

    normalized_threshold = _finite_threshold(threshold)
    epsilon = float(degenerate_epsilon if zero_edge_tolerance is None else zero_edge_tolerance)
    if not isfinite(epsilon) or epsilon < 0.0:
        raise ValueError("Degenerate epsilon must be finite and non-negative.")
    try:
        summary = build_mesh_summary(mesh_data)
    except MeshIdentityError as exc:
        raise MeshQualityAnalysisError(
            "Mesh Diagnostics requires an exact mesh fingerprint; the in-memory "
            "geometry or connectivity is invalid."
        ) from exc

    base_records: list[MeshCellQualityRecord] = []
    provider_rows: list[tuple[int, int, str, tuple[int, ...], int]] = []
    backend_index = 0
    for block_ordinal, block in enumerate(mesh_data.cells):
        cell_type = str(block.cell_type or "").strip().lower()
        for cell_ordinal, connectivity in enumerate(block.data):
            common = {
                "mesh_fingerprint": summary.mesh_fingerprint.digest,
                "entity_kind": "cell",
                "id_namespace": _CELL_ORDINAL_NAMESPACE,
                "stable_cell_key": f"{block_ordinal}:{cell_ordinal}",
                "backend_index": backend_index,
                "cell_type": cell_type,
                "block_ordinal": block_ordinal,
                "cell_ordinal": cell_ordinal,
                "metric_schema": MESH_QUALITY_METRIC_SCHEMA,
            }
            if cell_type not in QUALITY_SUPPORTED_CELL_TYPES:
                base_records.append(
                    MeshCellQualityRecord(
                        **common,
                        value=None,
                        status=MeshCellQualityStatus.UNCOVERED,
                        category=MeshQualityCategory.UNCOVERED,
                        is_bad=False,
                        reason="TOPOLOGY_NOT_COVERED_BY_SCALED_JACOBIAN_V1",
                    )
                )
            elif not cell_connectivity_is_valid(mesh_data, cell_type, connectivity):
                base_records.append(
                    MeshCellQualityRecord(
                        **common,
                        value=None,
                        status=MeshCellQualityStatus.INVALID,
                        category=MeshQualityCategory.INVALID,
                        is_bad=True,
                        reason="INVALID_OR_NONFINITE_CONNECTIVITY",
                    )
                )
            else:
                provider_rows.append(
                    (block_ordinal, cell_ordinal, cell_type, connectivity, backend_index)
                )
                base_records.append(
                    MeshCellQualityRecord(
                        **common,
                        value=None,
                        status=MeshCellQualityStatus.UNAVAILABLE,
                        category=MeshQualityCategory.UNAVAILABLE,
                        is_bad=False,
                        reason="PROVIDER_NOT_EVALUATED",
                    )
                )
            backend_index += 1

    diagnostics: list[str] = []
    provider_status: MeshDiagnosticsStatus | None = None
    resolved_provider: ScaledJacobianProvider | None
    if provider is None and not provider_rows:
        resolved_provider = None
        provider_schema = "osw.mesh_quality.provider.pyvista_vtk.v1"
        provider_version = "not_evaluated_no_covered_cells"
    else:
        resolved_provider = provider or _default_scaled_jacobian_provider()
        provider_schema = str(getattr(resolved_provider, "provider_schema", "") or "unknown")
        try:
            provider_version = str(getattr(resolved_provider, "provider_version", "") or "unknown")
        except MeshQualityProviderUnavailableError as exc:
            provider_version = "unavailable"
            provider_status = MeshDiagnosticsStatus.UNAVAILABLE_OPTIONAL_DEPENDENCY
            diagnostics.append(str(exc))
    values: tuple[float, ...] = ()
    if provider_rows and provider_status is None:
        assert resolved_provider is not None
        try:
            values = tuple(
                float(value)
                for value in resolved_provider.evaluate(_provider_mesh(mesh_data, provider_rows))
            )
        except MeshQualityProviderUnavailableError as exc:
            provider_status = MeshDiagnosticsStatus.UNAVAILABLE_OPTIONAL_DEPENDENCY
            diagnostics.append(str(exc))
        except Exception as exc:
            provider_status = MeshDiagnosticsStatus.FAILED
            diagnostics.append(f"{type(exc).__name__}: {exc}")
        if provider_status is None and len(values) != len(provider_rows):
            provider_status = MeshDiagnosticsStatus.FAILED
            diagnostics.append(
                "Scaled Jacobian provider returned a value count that does not match "
                "the canonical covered-cell count."
            )

    if provider_status is None:
        index_by_backend = {
            record.backend_index: index for index, record in enumerate(base_records)
        }
        for provider_index, row in enumerate(provider_rows):
            record_index = index_by_backend[row[4]]
            value = values[provider_index]
            current = base_records[record_index]
            if not isfinite(value):
                base_records[record_index] = replace(
                    current,
                    value=None,
                    status=MeshCellQualityStatus.INVALID,
                    category=MeshQualityCategory.INVALID,
                    is_bad=True,
                    reason="PROVIDER_RETURNED_NONFINITE_VALUE",
                )
            else:
                base_records[record_index] = replace(
                    current,
                    value=value,
                    status=MeshCellQualityStatus.EVALUATED,
                    category=_classify_value(
                        value,
                        threshold=normalized_threshold,
                        epsilon=epsilon,
                    ),
                    is_bad=value <= normalized_threshold,
                    reason="EVALUATED",
                )
    elif provider_status is MeshDiagnosticsStatus.FAILED:
        base_records = [
            replace(
                record,
                status=MeshCellQualityStatus.INVALID,
                category=MeshQualityCategory.INVALID,
                is_bad=True,
                reason="SCALED_JACOBIAN_PROVIDER_FAILED",
            )
            if record.status is MeshCellQualityStatus.UNAVAILABLE
            else record
            for record in base_records
        ]
    else:
        base_records = [
            replace(record, reason="OPTIONAL_QUALITY_PROVIDER_UNAVAILABLE")
            if record.status is MeshCellQualityStatus.UNAVAILABLE
            else record
            for record in base_records
        ]

    return _build_analysis(
        summary=summary,
        mesh_ref="",
        records=tuple(base_records),
        provider_schema=provider_schema,
        provider_version=provider_version,
        threshold=normalized_threshold,
        epsilon=epsilon,
        range_mode=range_mode,
        manual_range=manual_range,
        diagnostics=tuple(diagnostics),
        forced_status=provider_status,
    )


def reclassify_mesh_quality(
    analysis: MeshQualityAnalysis,
    *,
    threshold: float,
    range_mode: str | None = None,
    manual_range: tuple[float, float] | None = None,
) -> MeshQualityAnalysis:
    """Reclassify cached finite values without geometry or provider work."""

    normalized_threshold = _finite_threshold(threshold)
    normalized_mode = (
        ("manual" if manual_range is not None else analysis.range_mode)
        if range_mode is None
        else str(range_mode).strip().lower()
    )
    resolved_manual = manual_range
    if normalized_mode == "manual" and resolved_manual is None:
        resolved_manual = analysis.display_range
    if (
        normalized_threshold == analysis.threshold
        and normalized_mode == analysis.range_mode
        and (normalized_mode != "manual" or resolved_manual == analysis.display_range)
    ):
        return analysis
    records = tuple(
        replace(
            record,
            category=_classify_value(
                record.value,
                threshold=normalized_threshold,
                epsilon=analysis.degenerate_epsilon,
            ),
            is_bad=record.value <= normalized_threshold,
        )
        if record.status is MeshCellQualityStatus.EVALUATED and record.value is not None
        else record
        for record in analysis.records
    )
    forced = (
        analysis.status
        if analysis.status
        in {
            MeshDiagnosticsStatus.UNAVAILABLE_OPTIONAL_DEPENDENCY,
            MeshDiagnosticsStatus.FAILED,
            MeshDiagnosticsStatus.STALE,
            MeshDiagnosticsStatus.CANCELLED,
        }
        else None
    )
    return _build_analysis(
        summary=analysis.mesh_summary,
        mesh_ref=analysis.mesh_ref,
        records=records,
        provider_schema=analysis.provider_schema,
        provider_version=analysis.provider_version,
        threshold=normalized_threshold,
        epsilon=analysis.degenerate_epsilon,
        range_mode=normalized_mode,
        manual_range=resolved_manual,
        diagnostics=analysis.diagnostics,
        forced_status=forced,
    )


def derive_bad_cell_records(
    analysis: MeshQualityAnalysis,
    *,
    threshold: float | None = None,
) -> tuple[MeshCellQualityRecord, ...]:
    """Return bad finite cells plus invalid cells; uncovered cells stay excluded."""

    classified = (
        analysis
        if threshold is None or float(threshold) == analysis.threshold
        else reclassify_mesh_quality(analysis, threshold=float(threshold))
    )
    return tuple(record for record in classified.records if record.is_bad)


def _build_analysis(
    *,
    summary: MeshSummary,
    mesh_ref: str,
    records: tuple[MeshCellQualityRecord, ...],
    provider_schema: str,
    provider_version: str,
    threshold: float,
    epsilon: float,
    range_mode: str,
    manual_range: tuple[float, float] | None,
    diagnostics: tuple[str, ...],
    forced_status: MeshDiagnosticsStatus | None,
) -> MeshQualityAnalysis:
    finite_values = tuple(
        record.value
        for record in records
        if record.status is MeshCellQualityStatus.EVALUATED and record.value is not None
    )
    statistics = _statistics(finite_values)
    normalized_mode, display_range = _display_range(
        finite_values,
        range_mode=range_mode,
        manual_range=manual_range,
    )
    covered_count = len(finite_values)
    uncovered_count = sum(record.status is MeshCellQualityStatus.UNCOVERED for record in records)
    invalid_count = sum(
        record.status in {MeshCellQualityStatus.INVALID, MeshCellQualityStatus.DEGENERATE}
        for record in records
    )
    unavailable_count = sum(
        record.status is MeshCellQualityStatus.UNAVAILABLE for record in records
    )
    bad_count = sum(record.is_bad for record in records)
    status = forced_status or (
        MeshDiagnosticsStatus.PARTIAL_COVERAGE if uncovered_count else MeshDiagnosticsStatus.READY
    )
    all_diagnostics = list(diagnostics)
    if uncovered_count:
        all_diagnostics.append(
            f"{uncovered_count} cell(s) are outside Scaled Jacobian v1 topology coverage."
        )
    if invalid_count:
        all_diagnostics.append(
            f"{invalid_count} cell(s) are invalid or have an undefined provider value."
        )
    display = (float(display_range[0]), float(display_range[1]))
    return MeshQualityAnalysis(
        schema=MESH_QUALITY_RESULT_SCHEMA,
        status=status,
        mesh_ref=str(mesh_ref or ""),
        mesh_summary=summary,
        metric_schema=MESH_QUALITY_METRIC_SCHEMA,
        metric_label=MESH_QUALITY_METRIC_LABEL,
        metric_direction=MESH_QUALITY_METRIC_DIRECTION,
        metric_semantics=MESH_QUALITY_METRIC_SEMANTICS,
        topology_rules_version=MESH_QUALITY_TOPOLOGY_RULES,
        provider_schema=provider_schema,
        provider_version=provider_version,
        threshold=threshold,
        degenerate_epsilon=epsilon,
        range_mode=normalized_mode,
        display_range=display,
        covered_count=covered_count,
        uncovered_count=uncovered_count,
        invalid_count=invalid_count,
        unavailable_count=unavailable_count,
        bad_count=bad_count,
        statistics=statistics,
        topology_summaries=_topology_summaries(records),
        records=records,
        digest=_analysis_digest(
            mesh_fingerprint=summary.mesh_fingerprint.digest,
            provider_schema=provider_schema,
            provider_version=provider_version,
            threshold=threshold,
            records=records,
        ),
        diagnostics=tuple(all_diagnostics),
    )


def _provider_mesh(
    mesh: MeshData,
    rows: Sequence[tuple[int, int, str, tuple[int, ...], int]],
) -> MeshData:
    grouped: list[MeshCellBlock] = []
    current_block: int | None = None
    current_type = ""
    current_rows: list[tuple[int, ...]] = []
    for block_ordinal, _cell_ordinal, cell_type, connectivity, _backend in rows:
        if current_block is not None and block_ordinal != current_block:
            grouped.append(MeshCellBlock(current_type, tuple(current_rows)))
            current_rows = []
        current_block = block_ordinal
        current_type = cell_type
        current_rows.append(connectivity)
    if current_block is not None:
        grouped.append(MeshCellBlock(current_type, tuple(current_rows)))
    return MeshData(points=mesh.points, cells=tuple(grouped))


def _default_scaled_jacobian_provider() -> ScaledJacobianProvider:
    try:
        from .quality_pyvista import PyVistaScaledJacobianProvider
    except ModuleNotFoundError as exc:  # pragma: no cover - install boundary
        raise MeshQualityProviderUnavailableError(
            "Scaled Jacobian requires the optional PyVista/VTK post-processing extra."
        ) from exc
    return PyVistaScaledJacobianProvider()


def _classify_value(
    value: float,
    *,
    threshold: float,
    epsilon: float,
) -> MeshQualityCategory:
    if value < -epsilon:
        return MeshQualityCategory.INVERTED
    if abs(value) <= epsilon:
        return MeshQualityCategory.DEGENERATE
    if value <= threshold:
        return MeshQualityCategory.THRESHOLD_BAD
    return MeshQualityCategory.ACCEPTABLE


def _finite_threshold(value: float) -> float:
    normalized = float(value)
    if not isfinite(normalized) or not -1.0 <= normalized <= 1.0:
        raise ValueError("Mesh quality threshold must be finite and within [-1, 1].")
    return normalized


def _statistics(values: Sequence[float]) -> MeshQualityStatistics:
    ordered = tuple(sorted(float(value) for value in values))
    if not ordered:
        return MeshQualityStatistics()
    return MeshQualityStatistics(
        count=len(ordered),
        minimum=ordered[0],
        maximum=ordered[-1],
        mean=fmean(ordered),
        median=median(ordered),
        population_stddev=pstdev(ordered),
        p05=_percentile(ordered, 0.05),
        p25=_percentile(ordered, 0.25),
        p75=_percentile(ordered, 0.75),
        p95=_percentile(ordered, 0.95),
    )


def _percentile(values: Sequence[float], fraction: float) -> float:
    if len(values) == 1:
        return float(values[0])
    position = (len(values) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower
    return float(values[lower] * (1.0 - weight) + values[upper] * weight)


def _display_range(
    values: Sequence[float],
    *,
    range_mode: str,
    manual_range: tuple[float, float] | None,
) -> tuple[str, tuple[float, float]]:
    mode = str(range_mode or "auto").strip().lower()
    if manual_range is not None and mode == "auto":
        mode = "manual"
    if mode not in {"auto", "manual"}:
        raise ValueError("Mesh quality range mode must be auto or manual.")
    if mode == "manual":
        if manual_range is None or len(manual_range) != 2:
            raise ValueError("Manual mesh quality range requires minimum and maximum.")
        minimum, maximum = (float(value) for value in manual_range)
        if not isfinite(minimum) or not isfinite(maximum):
            raise ValueError("Manual mesh quality range values must be finite.")
        if minimum >= maximum:
            raise ValueError("Manual mesh quality range minimum must be less than maximum.")
        return mode, (minimum, maximum)
    if not values:
        return mode, (-1.0, 1.0)
    minimum = min(values)
    maximum = max(values)
    if minimum == maximum:
        delta = max(1.0e-12, abs(minimum) * 1.0e-12)
        return mode, (minimum - delta, maximum + delta)
    return mode, (minimum, maximum)


def _topology_summaries(
    records: Sequence[MeshCellQualityRecord],
) -> tuple[MeshTopologyQualitySummary, ...]:
    summaries: list[MeshTopologyQualitySummary] = []
    for cell_type in sorted({record.cell_type for record in records}):
        selected = tuple(record for record in records if record.cell_type == cell_type)
        values = tuple(
            record.value
            for record in selected
            if record.status is MeshCellQualityStatus.EVALUATED and record.value is not None
        )
        summaries.append(
            MeshTopologyQualitySummary(
                cell_type=cell_type,
                total_count=len(selected),
                covered_count=len(values),
                uncovered_count=sum(
                    record.status is MeshCellQualityStatus.UNCOVERED for record in selected
                ),
                invalid_count=sum(
                    record.status is MeshCellQualityStatus.INVALID for record in selected
                ),
                bad_count=sum(record.is_bad for record in selected),
                statistics=_statistics(values),
            )
        )
    return tuple(summaries)


def _analysis_digest(
    *,
    mesh_fingerprint: str,
    provider_schema: str,
    provider_version: str,
    threshold: float,
    records: Sequence[MeshCellQualityRecord],
) -> str:
    digest = hashlib.sha256()

    def frame(data: bytes) -> None:
        digest.update(struct.pack("<Q", len(data)))
        digest.update(data)

    for text in (
        MESH_QUALITY_RESULT_SCHEMA,
        MESH_QUALITY_METRIC_SCHEMA,
        mesh_fingerprint,
        provider_schema,
        provider_version,
    ):
        frame(text.encode("utf-8"))
    frame(struct.pack("<d", float(threshold)))
    for record in records:
        for text in (record.stable_cell_key, record.status.value):
            frame(text.encode("utf-8"))
        if record.status is MeshCellQualityStatus.UNCOVERED:
            marker = b"U"
        elif record.status is MeshCellQualityStatus.INVALID:
            marker = b"I"
        elif record.value is None:
            marker = b"A"
        else:
            marker = b"F" + struct.pack("<d", record.value)
        frame(marker)
    return digest.hexdigest()


# Legacy report-level edge summaries. They are no longer user-facing Mesh
# Diagnostics, but remain compatible with existing report callers.


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
            f"bounding_box={self.bounding_box.minimum} -> {self.bounding_box.maximum}",
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
    """Compute legacy lightweight edge summaries for existing reports."""

    if bad_aspect_ratio_threshold <= 0:
        raise ValueError("Bad aspect ratio threshold must be positive.")
    if zero_edge_tolerance < 0:
        raise ValueError("Zero edge tolerance must be non-negative.")
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
                        "invalid_connectivity",
                        str(exc),
                        cell_type=block.cell_type,
                        element_index=local_index,
                    )
                )
                continue
            if not element_edges:
                warnings.append(
                    MeshQualityWarning(
                        "insufficient_connectivity",
                        "Element has fewer than two valid nodes.",
                        cell_type=block.cell_type,
                        element_index=local_index,
                    )
                )
                continue
            edge_lengths.extend(element_edges)
            minimum = min(element_edges)
            maximum = max(element_edges)
            if minimum <= zero_edge_tolerance:
                warnings.append(
                    MeshQualityWarning(
                        "degenerate_edge",
                        "Element contains a near-zero edge length.",
                        cell_type=block.cell_type,
                        element_index=local_index,
                    )
                )
                continue
            ratio = maximum / minimum
            aspect_ratios.append(ratio)
            if ratio > bad_aspect_ratio_threshold:
                warnings.append(
                    MeshQualityWarning(
                        "high_aspect_ratio",
                        (
                            f"Element aspect ratio {ratio:g} exceeds threshold "
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
        mean_aspect_ratio=fmean(aspect_ratios) if aspect_ratios else None,
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
        raise ValueError(f"Element references node index outside mesh point range: {invalid[0]}")
    return tuple(dist(points[start], points[end]) for start, end in combinations(connectivity, 2))


def _format_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "none"
    return ", ".join(f"{cell_type}:{count}" for cell_type, count in sorted(distribution.items()))


__all__ = [
    "DEFAULT_DEGENERATE_EPSILON",
    "DEFAULT_MESH_QUALITY_THRESHOLD",
    "MESH_QUALITY_METRIC_DIRECTION",
    "MESH_QUALITY_METRIC_LABEL",
    "MESH_QUALITY_METRIC_SCHEMA",
    "MESH_QUALITY_METRIC_SEMANTICS",
    "MESH_QUALITY_RESULT_SCHEMA",
    "MESH_QUALITY_TOPOLOGY_RULES",
    "MeshCellQualityRecord",
    "MeshCellQualityStatus",
    "MeshDiagnosticsStatus",
    "MeshQualityAnalysis",
    "MeshQualityAnalysisError",
    "MeshQualityCategory",
    "MeshQualityMetrics",
    "MeshQualityProviderError",
    "MeshQualityProviderUnavailableError",
    "MeshQualityStatistics",
    "MeshQualityWarning",
    "MeshTopologyQualitySummary",
    "ScaledJacobianProvider",
    "analyze_mesh_cell_quality",
    "analyze_mesh_quality",
    "derive_bad_cell_records",
    "reclassify_mesh_quality",
]
