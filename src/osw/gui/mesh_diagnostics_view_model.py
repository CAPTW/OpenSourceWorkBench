"""Qt/PyVista-free Mesh Diagnostics table and semantic-overlay projection."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from osw.mesh.quality import (
    MeshCellQualityRecord,
    MeshQualityAnalysis,
    derive_bad_cell_records,
)

MESH_QUALITY_ACTOR_KEY = "mesh_quality:bad_cells"


@dataclass(frozen=True)
class MeshQualityTableRow:
    stable_cell_id: str
    cell_type: str
    block_ordinal: int
    cell_ordinal: int
    status: str
    metric_value: float | None
    reason: str
    is_bad: bool


@dataclass(frozen=True)
class MeshQualityOverlaySpec:
    actor_key: str
    mesh_fingerprint: str
    stable_cell_keys: tuple[str, ...]
    entity_indices: tuple[int, ...]
    visible: bool = True


@dataclass(frozen=True)
class MeshDiagnosticsViewModel:
    analysis_available: bool
    mesh_label: str
    mesh_fingerprint: str
    metric_schema: str
    metric_label: str
    threshold: float
    node_count: int
    cell_count: int
    cell_type_distribution: tuple[tuple[str, int], ...]
    bounding_box_text: str
    evaluated_count: int
    bad_count: int
    bad_percentage: float
    degenerate_count: int
    invalid_count: int
    unsupported_count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    rows: tuple[MeshQualityTableRow, ...]
    bad_cell_keys: tuple[str, ...]
    table_bad_cell_keys: tuple[str, ...]
    renderer_available: bool
    overlay_actions_enabled: bool
    highlight_visible: bool
    isolated: bool
    backend_diagnostic: str
    diagnostics: tuple[str, ...]


def build_mesh_diagnostics_view_model(
    analysis: MeshQualityAnalysis | None,
    *,
    threshold: float = 10.0,
    mesh_label: str = "",
    renderer_available: bool = False,
    backend_reason: str = "",
    highlight_visible: bool = False,
    isolated: bool = False,
) -> MeshDiagnosticsViewModel:
    """Build one deterministic table and bad-key set from immutable analysis."""

    normalized_threshold = _positive_threshold(threshold)
    safe_label = _safe_display_label(mesh_label)
    if analysis is None:
        diagnostic = str(backend_reason or "")
        return MeshDiagnosticsViewModel(
            analysis_available=False,
            mesh_label=safe_label,
            mesh_fingerprint="",
            metric_schema="",
            metric_label="Edge aspect ratio preview",
            threshold=normalized_threshold,
            node_count=0,
            cell_count=0,
            cell_type_distribution=(),
            bounding_box_text="unavailable",
            evaluated_count=0,
            bad_count=0,
            bad_percentage=0.0,
            degenerate_count=0,
            invalid_count=0,
            unsupported_count=0,
            minimum=None,
            maximum=None,
            mean=None,
            rows=(),
            bad_cell_keys=(),
            table_bad_cell_keys=(),
            renderer_available=renderer_available,
            overlay_actions_enabled=False,
            highlight_visible=False,
            isolated=False,
            backend_diagnostic=diagnostic,
            diagnostics=(),
        )

    bad_records = derive_bad_cell_records(
        analysis,
        threshold=normalized_threshold,
    )
    bad_keys = tuple(record.stable_cell_key for record in bad_records)
    bad_key_set = frozenset(bad_keys)
    rows = tuple(_table_row(record, bad_key_set) for record in analysis.records)
    table_bad_keys = tuple(row.stable_cell_id for row in rows if row.is_bad)
    backend_diagnostic = ""
    if not renderer_available:
        backend_diagnostic = (
            str(backend_reason or "").strip()
            or "Interactive renderer unavailable; metadata and table remain available."
        )
    return MeshDiagnosticsViewModel(
        analysis_available=True,
        mesh_label=safe_label,
        mesh_fingerprint=analysis.mesh_fingerprint.digest,
        metric_schema=analysis.metric_schema,
        metric_label=analysis.metric_label,
        threshold=normalized_threshold,
        node_count=analysis.node_count,
        cell_count=analysis.cell_count,
        cell_type_distribution=tuple(sorted(analysis.cell_type_distribution.items())),
        bounding_box_text=(
            f"{analysis.bounding_box.minimum} -> {analysis.bounding_box.maximum}"
        ),
        evaluated_count=analysis.evaluated_count,
        bad_count=len(bad_keys),
        bad_percentage=(
            100.0 * len(bad_keys) / analysis.cell_count
            if analysis.cell_count
            else 0.0
        ),
        degenerate_count=analysis.degenerate_count,
        invalid_count=analysis.invalid_count,
        unsupported_count=analysis.unsupported_count,
        minimum=analysis.minimum,
        maximum=analysis.maximum,
        mean=analysis.mean,
        rows=rows,
        bad_cell_keys=bad_keys,
        table_bad_cell_keys=table_bad_keys,
        renderer_available=renderer_available,
        overlay_actions_enabled=renderer_available and bool(bad_keys),
        highlight_visible=bool(highlight_visible and bad_keys),
        isolated=bool(isolated and bad_keys),
        backend_diagnostic=backend_diagnostic,
        diagnostics=analysis.diagnostics,
    )


def build_mesh_quality_overlay_spec(
    analysis: MeshQualityAnalysis,
    *,
    threshold: float,
    visible: bool = True,
) -> MeshQualityOverlaySpec | None:
    """Project the same ordered bad-key set to transient global cell indices."""

    bad_records = derive_bad_cell_records(analysis, threshold=threshold)
    if not bad_records:
        return None
    bad_keys = tuple(record.stable_cell_key for record in bad_records)
    bad_key_set = frozenset(bad_keys)
    entity_indices = tuple(
        index
        for index, record in enumerate(analysis.records)
        if record.stable_cell_key in bad_key_set
    )
    return MeshQualityOverlaySpec(
        actor_key=MESH_QUALITY_ACTOR_KEY,
        mesh_fingerprint=analysis.mesh_fingerprint.digest,
        stable_cell_keys=bad_keys,
        entity_indices=entity_indices,
        visible=bool(visible),
    )


def _table_row(
    record: MeshCellQualityRecord,
    bad_keys: frozenset[str],
) -> MeshQualityTableRow:
    return MeshQualityTableRow(
        stable_cell_id=record.stable_cell_key,
        cell_type=record.cell_type,
        block_ordinal=record.block_ordinal,
        cell_ordinal=record.cell_ordinal,
        status=record.status.value,
        metric_value=record.value,
        reason=record.reason,
        is_bad=record.stable_cell_key in bad_keys,
    )


def _positive_threshold(value: float) -> float:
    normalized = float(value)
    if not isfinite(normalized) or normalized <= 0.0:
        msg = "Bad-cell threshold must be finite and positive."
        raise ValueError(msg)
    return normalized


def _safe_display_label(value: str) -> str:
    normalized = str(value or "").replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", 1)[-1] if normalized else "active mesh"


__all__ = [
    "MESH_QUALITY_ACTOR_KEY",
    "MeshDiagnosticsViewModel",
    "MeshQualityOverlaySpec",
    "MeshQualityTableRow",
    "build_mesh_diagnostics_view_model",
    "build_mesh_quality_overlay_spec",
]
