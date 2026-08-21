"""Qt/PyVista-free Mesh Diagnostics tables and semantic actor payloads."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isfinite

from osw.mesh.quality import (
    DEFAULT_MESH_QUALITY_THRESHOLD,
    MESH_QUALITY_METRIC_LABEL,
    MESH_QUALITY_METRIC_SCHEMA,
    MESH_QUALITY_METRIC_SEMANTICS,
    MeshCellQualityRecord,
    MeshCellQualityStatus,
    MeshDiagnosticsStatus,
    MeshQualityAnalysis,
    derive_bad_cell_records,
    reclassify_mesh_quality,
)

MESH_QUALITY_ACTOR_KEY = "mesh_quality"
MESH_BAD_ELEMENTS_ACTOR_KEY = "mesh_bad_elements"
MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY = "mesh_diagnostic_good_elements"
MESH_QUALITY_SCALARBAR_ACTOR_KEY = "mesh_quality_scalar_bar"
MESH_QUALITY_SCALAR_NAME = "osw_scaled_jacobian"


@dataclass(frozen=True, slots=True)
class MeshQualityTableRow:
    stable_cell_id: str
    backend_index: int
    cell_type: str
    block_ordinal: int
    cell_ordinal: int
    status: str
    category: str
    metric_value: float | None
    reason: str
    is_bad: bool


@dataclass(frozen=True, slots=True)
class MeshQualityOverlaySpec:
    actor_key: str
    mesh_fingerprint: str
    stable_cell_keys: tuple[str, ...]
    entity_indices: tuple[int, ...]
    values: tuple[float, ...] = ()
    scalar_name: str = MESH_QUALITY_SCALAR_NAME
    display_range: tuple[float, float] = (-1.0, 1.0)
    colormap: str = "coolwarm"
    visible: bool = True
    role: str = "quality"


@dataclass(frozen=True, slots=True)
class MeshQualityScalarBarSpec:
    actor_key: str
    title: str
    scalar_actor_key: str
    display_range: tuple[float, float]
    colormap: str = "coolwarm"
    visible: bool = True


@dataclass(frozen=True, slots=True)
class MeshDiagnosticsOverlaySpecs:
    quality: MeshQualityOverlaySpec | None
    bad: MeshQualityOverlaySpec | None
    good: MeshQualityOverlaySpec | None
    scalar_bar: MeshQualityScalarBarSpec | None


@dataclass(frozen=True, slots=True)
class MeshDiagnosticsViewModel:
    analysis_available: bool
    status: str
    mesh_label: str
    mesh_fingerprint: str
    metric_schema: str
    metric_label: str
    metric_semantics: str
    provider_schema: str
    provider_version: str
    threshold: float
    range_mode: str
    display_range: tuple[float, float]
    node_count: int
    cell_count: int
    block_count: int
    cell_type_distribution: tuple[tuple[str, int], ...]
    surface_cell_count: int
    volume_cell_count: int
    covered_topology_types: tuple[str, ...]
    uncovered_topology_types: tuple[str, ...]
    bounding_box_text: str
    extents_text: str
    diagonal: float
    referenced_point_count: int
    orphan_point_count: int
    finite_point_count: int
    nonfinite_point_count: int
    evaluated_count: int
    covered_count: int
    coverage_ratio: float
    bad_count: int
    bad_percentage: float
    degenerate_count: int
    inverted_count: int
    threshold_bad_count: int
    acceptable_count: int
    invalid_count: int
    unsupported_count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None
    population_stddev: float | None
    p05: float | None
    p25: float | None
    p75: float | None
    p95: float | None
    rows: tuple[MeshQualityTableRow, ...]
    bad_cell_keys: tuple[str, ...]
    table_bad_cell_keys: tuple[str, ...]
    renderer_available: bool
    overlay_actions_enabled: bool
    quality_coloring_visible: bool
    highlight_visible: bool
    filter_mode: str
    isolated: bool
    backend_diagnostic: str
    diagnostics: tuple[str, ...]
    digest: str


def build_mesh_diagnostics_view_model(
    analysis: MeshQualityAnalysis | None,
    *,
    threshold: float = DEFAULT_MESH_QUALITY_THRESHOLD,
    mesh_label: str = "",
    renderer_available: bool = False,
    backend_reason: str = "",
    quality_coloring_visible: bool = False,
    highlight_visible: bool = False,
    filter_mode: str = "clear",
    isolated: bool | None = None,
) -> MeshDiagnosticsViewModel:
    """Build deterministic GUI state from one immutable analysis."""

    normalized_threshold = _finite_threshold(threshold)
    safe_label = _safe_display_label(mesh_label)
    normalized_filter = str(filter_mode or "clear").strip().lower()
    if isolated is True:
        normalized_filter = "isolate_bad"
    if analysis is None:
        return _empty_view_model(
            threshold=normalized_threshold,
            mesh_label=safe_label,
            renderer_available=renderer_available,
            backend_reason=backend_reason,
        )
    classified = (
        analysis
        if analysis.threshold == normalized_threshold
        else reclassify_mesh_quality(analysis, threshold=normalized_threshold)
    )
    bad_records = derive_bad_cell_records(classified)
    bad_keys = tuple(record.stable_cell_key for record in bad_records)
    bad_key_set = frozenset(bad_keys)
    rows = tuple(_table_row(record, bad_key_set) for record in classified.records)
    backend_diagnostic = ""
    if not renderer_available:
        backend_diagnostic = (
            str(backend_reason or "").strip()
            or "Interactive renderer unavailable; summary and table remain available."
        )
    overlay_ready = classified.status in {
        MeshDiagnosticsStatus.READY,
        MeshDiagnosticsStatus.PARTIAL_COVERAGE,
    }
    summary = classified.mesh_summary
    return MeshDiagnosticsViewModel(
        analysis_available=True,
        status=classified.status.value,
        mesh_label=safe_label,
        mesh_fingerprint=classified.mesh_fingerprint.digest,
        metric_schema=classified.metric_schema,
        metric_label=classified.metric_label,
        metric_semantics=classified.metric_semantics,
        provider_schema=classified.provider_schema,
        provider_version=classified.provider_version,
        threshold=classified.threshold,
        range_mode=classified.range_mode,
        display_range=classified.display_range,
        node_count=summary.point_count,
        cell_count=summary.cell_count,
        block_count=summary.block_count,
        cell_type_distribution=summary.cell_type_distribution,
        surface_cell_count=summary.surface_cell_count,
        volume_cell_count=summary.volume_cell_count,
        covered_topology_types=summary.supported_quality_types,
        uncovered_topology_types=summary.uncovered_quality_types,
        bounding_box_text=f"{summary.bounds.minimum} -> {summary.bounds.maximum}",
        extents_text=str(summary.extents),
        diagonal=summary.diagonal,
        referenced_point_count=summary.referenced_point_count,
        orphan_point_count=summary.orphan_point_count,
        finite_point_count=summary.finite_point_count,
        nonfinite_point_count=summary.nonfinite_point_count,
        evaluated_count=classified.covered_count,
        covered_count=classified.covered_count,
        coverage_ratio=(
            classified.covered_count / summary.cell_count if summary.cell_count else 0.0
        ),
        bad_count=len(bad_keys),
        bad_percentage=(100.0 * len(bad_keys) / summary.cell_count if summary.cell_count else 0.0),
        degenerate_count=sum(row.category == "degenerate" for row in rows),
        inverted_count=sum(row.category == "inverted" for row in rows),
        threshold_bad_count=sum(row.category == "threshold_bad" for row in rows),
        acceptable_count=sum(row.category == "acceptable" for row in rows),
        invalid_count=classified.invalid_count,
        unsupported_count=classified.uncovered_count,
        minimum=classified.statistics.minimum,
        maximum=classified.statistics.maximum,
        mean=classified.statistics.mean,
        median=classified.statistics.median,
        population_stddev=classified.statistics.population_stddev,
        p05=classified.statistics.p05,
        p25=classified.statistics.p25,
        p75=classified.statistics.p75,
        p95=classified.statistics.p95,
        rows=rows,
        bad_cell_keys=bad_keys,
        table_bad_cell_keys=tuple(row.stable_cell_id for row in rows if row.is_bad),
        renderer_available=renderer_available,
        overlay_actions_enabled=renderer_available and overlay_ready,
        quality_coloring_visible=bool(
            quality_coloring_visible and renderer_available and overlay_ready
        ),
        highlight_visible=bool(
            highlight_visible and bad_keys and renderer_available and overlay_ready
        ),
        filter_mode=normalized_filter,
        isolated=normalized_filter == "isolate_bad",
        backend_diagnostic=backend_diagnostic,
        diagnostics=classified.diagnostics,
        digest=classified.digest,
    )


def build_mesh_diagnostics_overlay_specs(
    analysis: MeshQualityAnalysis,
) -> MeshDiagnosticsOverlaySpecs:
    """Build distinct color, bad, complement, and legend payloads."""

    finite_records = tuple(
        record
        for record in analysis.records
        if record.status is MeshCellQualityStatus.EVALUATED and record.value is not None
    )
    bad_records = derive_bad_cell_records(analysis)
    bad_indices = frozenset(record.backend_index for record in bad_records)
    good_records = tuple(
        record for record in analysis.records if record.backend_index not in bad_indices
    )
    quality = _overlay(
        MESH_QUALITY_ACTOR_KEY,
        analysis,
        finite_records,
        values=tuple(float(record.value) for record in finite_records if record.value is not None),
        role="quality",
    )
    bad = _overlay(
        MESH_BAD_ELEMENTS_ACTOR_KEY,
        analysis,
        bad_records,
        role="bad",
    )
    good = _overlay(
        MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY,
        analysis,
        good_records,
        role="good",
    )
    scalar_bar = (
        MeshQualityScalarBarSpec(
            actor_key=MESH_QUALITY_SCALARBAR_ACTOR_KEY,
            title=f"{MESH_QUALITY_METRIC_LABEL} (higher is better)",
            scalar_actor_key=MESH_QUALITY_ACTOR_KEY,
            display_range=analysis.display_range,
        )
        if quality is not None
        else None
    )
    return MeshDiagnosticsOverlaySpecs(quality, bad, good, scalar_bar)


def build_mesh_quality_overlay_spec(
    analysis: MeshQualityAnalysis,
    *,
    threshold: float | None = None,
    visible: bool = True,
) -> MeshQualityOverlaySpec | None:
    """Compatibility entry point returning the bad-element actor payload."""

    classified = (
        analysis
        if threshold is None or float(threshold) == analysis.threshold
        else reclassify_mesh_quality(analysis, threshold=float(threshold))
    )
    spec = build_mesh_diagnostics_overlay_specs(classified).bad
    return None if spec is None else replace(spec, visible=bool(visible))


def _overlay(
    actor_key: str,
    analysis: MeshQualityAnalysis,
    records: tuple[MeshCellQualityRecord, ...],
    *,
    values: tuple[float, ...] = (),
    role: str,
) -> MeshQualityOverlaySpec | None:
    if not records:
        return None
    return MeshQualityOverlaySpec(
        actor_key=actor_key,
        mesh_fingerprint=analysis.mesh_fingerprint.digest,
        stable_cell_keys=tuple(record.stable_cell_key for record in records),
        entity_indices=tuple(record.backend_index for record in records),
        values=values,
        display_range=analysis.display_range,
        role=role,
    )


def _table_row(
    record: MeshCellQualityRecord,
    bad_keys: frozenset[str],
) -> MeshQualityTableRow:
    return MeshQualityTableRow(
        stable_cell_id=record.stable_cell_key,
        backend_index=record.backend_index,
        cell_type=record.cell_type,
        block_ordinal=record.block_ordinal,
        cell_ordinal=record.cell_ordinal,
        status=record.status.value,
        category=record.category.value,
        metric_value=record.value,
        reason=record.reason,
        is_bad=record.stable_cell_key in bad_keys,
    )


def _empty_view_model(
    *,
    threshold: float,
    mesh_label: str,
    renderer_available: bool,
    backend_reason: str,
) -> MeshDiagnosticsViewModel:
    return MeshDiagnosticsViewModel(
        analysis_available=False,
        status=MeshDiagnosticsStatus.IDLE.value,
        mesh_label=mesh_label,
        mesh_fingerprint="",
        metric_schema=MESH_QUALITY_METRIC_SCHEMA,
        metric_label=MESH_QUALITY_METRIC_LABEL,
        metric_semantics=MESH_QUALITY_METRIC_SEMANTICS,
        provider_schema="",
        provider_version="",
        threshold=threshold,
        range_mode="auto",
        display_range=(-1.0, 1.0),
        node_count=0,
        cell_count=0,
        block_count=0,
        cell_type_distribution=(),
        surface_cell_count=0,
        volume_cell_count=0,
        covered_topology_types=(),
        uncovered_topology_types=(),
        bounding_box_text="unavailable",
        extents_text="unavailable",
        diagonal=0.0,
        referenced_point_count=0,
        orphan_point_count=0,
        finite_point_count=0,
        nonfinite_point_count=0,
        evaluated_count=0,
        covered_count=0,
        coverage_ratio=0.0,
        bad_count=0,
        bad_percentage=0.0,
        degenerate_count=0,
        inverted_count=0,
        threshold_bad_count=0,
        acceptable_count=0,
        invalid_count=0,
        unsupported_count=0,
        minimum=None,
        maximum=None,
        mean=None,
        median=None,
        population_stddev=None,
        p05=None,
        p25=None,
        p75=None,
        p95=None,
        rows=(),
        bad_cell_keys=(),
        table_bad_cell_keys=(),
        renderer_available=renderer_available,
        overlay_actions_enabled=False,
        quality_coloring_visible=False,
        highlight_visible=False,
        filter_mode="clear",
        isolated=False,
        backend_diagnostic=str(backend_reason or ""),
        diagnostics=(),
        digest="",
    )


def _finite_threshold(value: float) -> float:
    normalized = float(value)
    if not isfinite(normalized) or not -1.0 <= normalized <= 1.0:
        raise ValueError("Mesh quality threshold must be finite and within [-1, 1].")
    return normalized


def _safe_display_label(value: str) -> str:
    normalized = str(value or "").replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", 1)[-1] if normalized else "active mesh"


__all__ = [
    "MESH_BAD_ELEMENTS_ACTOR_KEY",
    "MESH_DIAGNOSTIC_GOOD_ELEMENTS_ACTOR_KEY",
    "MESH_QUALITY_ACTOR_KEY",
    "MESH_QUALITY_SCALARBAR_ACTOR_KEY",
    "MESH_QUALITY_SCALAR_NAME",
    "MeshDiagnosticsOverlaySpecs",
    "MeshDiagnosticsViewModel",
    "MeshQualityOverlaySpec",
    "MeshQualityScalarBarSpec",
    "MeshQualityTableRow",
    "build_mesh_diagnostics_overlay_specs",
    "build_mesh_diagnostics_view_model",
    "build_mesh_quality_overlay_spec",
]
