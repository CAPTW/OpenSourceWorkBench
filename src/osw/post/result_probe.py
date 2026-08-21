"""Pure exact-identity result probes and bounded selected-entity tables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import fsum, isfinite, sqrt

from osw.core.result_mesh_binding import (
    ResultMeshBindingResolution,
    ResultMeshBindingResolutionState,
)
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData


class ResultProbeStatus(StrEnum):
    """Fail-closed exact probe outcomes."""

    RESOLVED = "RESOLVED"
    STALE = "STALE"
    INVALID = "INVALID"
    ASSOCIATION_MISMATCH = "ASSOCIATION_MISMATCH"
    NOT_FOUND = "NOT_FOUND"


class ResultValueStatus(StrEnum):
    """Value-level status kept separate from canonical lookup status."""

    FINITE = "FINITE"
    NONFINITE = "NONFINITE"
    ASSOCIATION_MISMATCH = "ASSOCIATION_MISMATCH"
    STALE = "STALE"
    INVALID = "INVALID"
    NOT_FOUND = "NOT_FOUND"


@dataclass(frozen=True)
class ResultProbeRequest:
    """One exact point/cell lookup against an already-loaded dataset."""

    dataset_id: str
    field_name: str
    component: str
    association: str
    stable_entity_key: int | str
    mesh_fingerprint: str


@dataclass(frozen=True)
class ResultComponentValue:
    """One stored component with an explicit finite/nonfinite projection."""

    component: str
    value: float | None
    raw_value: float
    display_value: str
    status: ResultValueStatus


@dataclass(frozen=True)
class ResultProbeResult:
    """Resolved stored tuple plus canonical geometry metadata."""

    status: ResultProbeStatus
    stable_entity_key: int | str
    entity_display_id: str
    field_name: str
    component: str
    association: str
    value: float | None = None
    unit: str = ""
    reason_code: str = ""
    diagnostics: tuple[str, ...] = ()
    value_status: ResultValueStatus = ResultValueStatus.INVALID
    display_value: str = "N/A"
    component_values: tuple[ResultComponentValue, ...] = ()
    magnitude: float | None = None
    magnitude_display: str = "N/A"
    coordinate: tuple[float, float, float] | None = None
    cell_type: str = ""
    connectivity: tuple[int, ...] = ()
    centroid: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class SelectedResultRow:
    """One canonical row produced through the exact probe lookup."""

    stable_entity_key: int | str
    entity_display_id: str
    value: float | None
    unit: str
    entity_kind: str = ""
    association_status: str = "MATCH"
    field_id: str = ""
    field_name: str = ""
    component: str = ""
    component_values: tuple[ResultComponentValue, ...] = ()
    magnitude: float | None = None
    display_value: str = "N/A"
    value_status: str = ResultValueStatus.INVALID.value
    coordinate: tuple[float, float, float] | None = None
    cell_type: str = ""
    connectivity: tuple[int, ...] = ()
    centroid: tuple[float, float, float] | None = None


@dataclass(frozen=True)
class SelectedResultTable:
    """Bounded renderer-neutral table of exact stored values."""

    rows: tuple[SelectedResultRow, ...]
    total_count: int
    truncated_count: int
    limit: int
    field_name: str
    component: str
    association: str
    status: str = "RESOLVED"
    diagnostics: tuple[str, ...] = ()


def probe_result_entity(
    mesh: MeshData,
    result_dataset: object,
    request: ResultProbeRequest,
    *,
    binding_resolution: ResultMeshBindingResolution,
) -> ResultProbeResult:
    """Return one exact stored tuple; never interpolate or geometrically remap."""

    association = _normalize_association(request.association)
    display = _entity_display(association, request.stable_entity_key)
    if binding_resolution.state is not ResultMeshBindingResolutionState.RESOLVED:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.STALE,
            ResultValueStatus.STALE,
            binding_resolution.reason_code,
            binding_resolution.message,
        )
    current_fingerprint = compute_mesh_fingerprint(mesh).digest
    if (
        request.mesh_fingerprint != current_fingerprint
        or binding_resolution.active_mesh_fingerprint != current_fingerprint
    ):
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.STALE,
            ResultValueStatus.STALE,
            "MESH_FINGERPRINT_MISMATCH",
            "Probe request does not match the exact active mesh fingerprint.",
        )
    if str(getattr(result_dataset, "dataset_id", "")) != request.dataset_id:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.INVALID,
            ResultValueStatus.INVALID,
            "RESULT_DATASET_ID_MISMATCH",
            "Probe request does not match the active ResultDataset.",
        )
    field = _find_field(result_dataset, request.field_name)
    if field is None:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.NOT_FOUND,
            ResultValueStatus.NOT_FOUND,
            "RESULT_FIELD_NOT_FOUND",
            "Requested result field is not available.",
        )
    metadata = _entity_metadata(mesh, association, request.stable_entity_key)
    if metadata is None:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.NOT_FOUND,
            ResultValueStatus.NOT_FOUND,
            "STABLE_ENTITY_NOT_FOUND",
            "Stable entity key is outside the active mesh domain.",
        )
    field_association = _normalize_association(getattr(field, "location", ""))
    if not association or association != field_association:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.ASSOCIATION_MISMATCH,
            ResultValueStatus.ASSOCIATION_MISMATCH,
            "ASSOCIATION_MISMATCH",
            "Probe association does not match the field association.",
            metadata=metadata,
        )
    components = tuple(str(item) for item in getattr(field, "components", ()) or ())
    selected_component, selected_index, magnitude_selected = _resolve_component(
        components,
        request.component,
    )
    if selected_component is None:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.NOT_FOUND,
            ResultValueStatus.NOT_FOUND,
            "RESULT_COMPONENT_NOT_FOUND",
            "Requested result component is not available.",
            metadata=metadata,
        )
    rows = tuple(getattr(field, "rows", ()) or ())
    target = len(mesh.points) if association == "point" else _cell_count(mesh)
    row, reason = _row_for_ordinal(rows, target=target, ordinal=metadata.ordinal)
    if reason:
        status = (
            ResultProbeStatus.NOT_FOUND
            if reason == "RESULT_ROW_NOT_FOUND"
            else ResultProbeStatus.INVALID
        )
        value_status = (
            ResultValueStatus.NOT_FOUND
            if status is ResultProbeStatus.NOT_FOUND
            else ResultValueStatus.INVALID
        )
        return _probe_failure(
            request,
            display,
            status,
            value_status,
            reason,
            reason,
            metadata=metadata,
        )
    assert row is not None
    values = getattr(row, "values", None)
    if not isinstance(values, Mapping):
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.INVALID,
            ResultValueStatus.INVALID,
            "INVALID_RESULT_VALUES",
            "Result row values are not a mapping.",
            metadata=metadata,
        )
    component_values: list[ResultComponentValue] = []
    for field_component in components:
        if field_component not in values:
            return _probe_failure(
                request,
                display,
                ResultProbeStatus.INVALID,
                ResultValueStatus.INVALID,
                "RESULT_COMPONENT_NOT_FOUND",
                f"Stored result component {field_component!r} is missing.",
                metadata=metadata,
            )
        try:
            raw_value = float(values[field_component])
        except (TypeError, ValueError, OverflowError):
            return _probe_failure(
                request,
                display,
                ResultProbeStatus.INVALID,
                ResultValueStatus.INVALID,
                "INVALID_RESULT_VALUE",
                f"Stored result component {field_component!r} is not numeric.",
                metadata=metadata,
            )
        finite = isfinite(raw_value)
        component_values.append(
            ResultComponentValue(
                component=field_component,
                value=raw_value if finite else None,
                raw_value=raw_value,
                display_value=_display_number(raw_value) if finite else "N/A",
                status=(ResultValueStatus.FINITE if finite else ResultValueStatus.NONFINITE),
            )
        )
    magnitude = _magnitude(component_values) if len(component_values) == 3 else None
    if magnitude_selected:
        selected_value = magnitude
    else:
        assert selected_index is not None
        selected_value = component_values[selected_index].value
    value_status = (
        ResultValueStatus.FINITE if selected_value is not None else ResultValueStatus.NONFINITE
    )
    unit = str(getattr(field, "unit", "") or "")
    return ResultProbeResult(
        status=ResultProbeStatus.RESOLVED,
        stable_entity_key=request.stable_entity_key,
        entity_display_id=display,
        field_name=request.field_name,
        component=selected_component,
        association=association,
        value=selected_value,
        unit=unit,
        reason_code=(
            "EXACT_STORED_VALUE"
            if value_status is ResultValueStatus.FINITE
            else "EXACT_STORED_NONFINITE"
        ),
        diagnostics=(
            ()
            if value_status is ResultValueStatus.FINITE
            else ("Stored result value is nonfinite and is displayed as N/A.",)
        ),
        value_status=value_status,
        display_value=(_display_number(selected_value) if selected_value is not None else "N/A"),
        component_values=tuple(component_values),
        magnitude=magnitude,
        magnitude_display=(_display_number(magnitude) if magnitude is not None else "N/A"),
        coordinate=metadata.coordinate,
        cell_type=metadata.cell_type,
        connectivity=metadata.connectivity,
        centroid=metadata.centroid,
    )


def build_selected_result_table(
    mesh: MeshData,
    result_dataset: object,
    *,
    field_name: str,
    component: str,
    association: str,
    stable_entity_keys: Sequence[int | str],
    binding_resolution: ResultMeshBindingResolution,
    limit: int = 500,
) -> SelectedResultTable:
    """Build deterministic copy-ready rows through the exact probe path."""

    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 500:
        raise ValueError("Selected-result table limit must be between 1 and 500.")
    normalized = _normalize_association(association)
    ordered = tuple(
        sorted(
            set(stable_entity_keys),
            key=lambda item: _stable_sort_key(normalized, item),
        )
    )
    if binding_resolution.state is not ResultMeshBindingResolutionState.RESOLVED:
        return SelectedResultTable(
            rows=(),
            total_count=len(ordered),
            truncated_count=max(0, len(ordered) - limit),
            limit=limit,
            field_name=field_name,
            component=component,
            association=normalized,
            status="STALE",
            diagnostics=(f"{binding_resolution.reason_code}: {binding_resolution.message}",),
        )
    dataset_id = str(getattr(result_dataset, "dataset_id", "") or "")
    fingerprint = compute_mesh_fingerprint(mesh).digest
    rows: list[SelectedResultRow] = []
    for key in ordered[:limit]:
        result = probe_result_entity(
            mesh,
            result_dataset,
            ResultProbeRequest(
                dataset_id=dataset_id,
                field_name=field_name,
                component=component,
                association=normalized,
                stable_entity_key=key,
                mesh_fingerprint=fingerprint,
            ),
            binding_resolution=binding_resolution,
        )
        rows.append(
            SelectedResultRow(
                stable_entity_key=key,
                entity_display_id=result.entity_display_id,
                value=result.value,
                unit=result.unit,
                entity_kind=normalized or "entity",
                association_status=(
                    "ASSOCIATION_MISMATCH"
                    if result.status is ResultProbeStatus.ASSOCIATION_MISMATCH
                    else "MATCH"
                ),
                field_id=field_name,
                field_name=field_name,
                component=result.component or component,
                component_values=result.component_values,
                magnitude=result.magnitude,
                display_value=result.display_value,
                value_status=result.value_status.value,
                coordinate=result.coordinate,
                cell_type=result.cell_type,
                connectivity=result.connectivity,
                centroid=result.centroid,
            )
        )
    return SelectedResultTable(
        rows=tuple(rows),
        total_count=len(ordered),
        truncated_count=max(0, len(ordered) - limit),
        limit=limit,
        field_name=field_name,
        component=component,
        association=normalized,
    )


@dataclass(frozen=True)
class _EntityMetadata:
    ordinal: int
    coordinate: tuple[float, float, float] | None = None
    cell_type: str = ""
    connectivity: tuple[int, ...] = ()
    centroid: tuple[float, float, float] | None = None


def _entity_metadata(
    mesh: MeshData,
    association: str,
    key: int | str,
) -> _EntityMetadata | None:
    if association == "point":
        ordinal = _point_ordinal(key, len(mesh.points))
        if ordinal is None:
            return None
        return _EntityMetadata(ordinal=ordinal, coordinate=mesh.points[ordinal])
    if association != "cell":
        return None
    parts = str(key).split(":")
    if len(parts) != 2:
        return None
    try:
        block_ordinal, local_ordinal = (int(item) for item in parts)
    except (TypeError, ValueError, OverflowError):
        return None
    if not 0 <= block_ordinal < len(mesh.cells):
        return None
    block = mesh.cells[block_ordinal]
    if not 0 <= local_ordinal < block.count or local_ordinal >= len(block.data):
        return None
    connectivity = block.data[local_ordinal]
    if not connectivity or any(not 0 <= index < len(mesh.points) for index in connectivity):
        return None
    points = tuple(mesh.points[index] for index in connectivity)
    factor = 1.0 / len(points)
    centroid = (
        fsum(point[0] for point in points) * factor,
        fsum(point[1] for point in points) * factor,
        fsum(point[2] for point in points) * factor,
    )
    ordinal = sum(item.count for item in mesh.cells[:block_ordinal]) + local_ordinal
    return _EntityMetadata(
        ordinal=ordinal,
        cell_type=block.cell_type,
        connectivity=connectivity,
        centroid=centroid,
    )


def _find_field(result_dataset: object, field_name: str) -> object | None:
    return next(
        (
            field
            for field in getattr(result_dataset, "fields", ()) or ()
            if str(getattr(field, "name", "")) == field_name
        ),
        None,
    )


def _normalize_association(value: object) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"point", "node", "vertex"}:
        return "point"
    if normalized in {"cell", "element"}:
        return "cell"
    return ""


def _cell_count(mesh: MeshData) -> int:
    return sum(block.count for block in mesh.cells)


def _point_ordinal(key: int | str, count: int) -> int | None:
    if isinstance(key, bool):
        return None
    try:
        ordinal = int(key)
    except (TypeError, ValueError, OverflowError):
        return None
    return ordinal if 0 <= ordinal < count else None


def _row_for_ordinal(
    rows: tuple[object, ...],
    *,
    target: int,
    ordinal: int,
) -> tuple[object | None, str]:
    if len(rows) != target:
        return None, "RESULT_ROW_COUNT_MISMATCH"
    by_id: dict[int, object] = {}
    for row in rows:
        entity_id = _finite_integer(getattr(row, "entity_id", None))
        if entity_id is None:
            return None, "INVALID_RESULT_ENTITY_ID"
        if entity_id in by_id:
            return None, "DUPLICATE_RESULT_ENTITY_ID"
        by_id[entity_id] = row
    keys = sorted(by_id)
    if keys == list(range(target)):
        offset = 0
    elif keys == list(range(1, target + 1)):
        offset = 1
    else:
        return None, "RESULT_ROW_NOT_FOUND"
    row = by_id.get(ordinal + offset)
    return (row, "" if row is not None else "RESULT_ROW_NOT_FOUND")


def _resolve_component(
    components: tuple[str, ...],
    requested: str,
) -> tuple[str | None, int | None, bool]:
    if not components:
        return (None, None, False)
    normalized = str(requested or "").strip()
    folded = normalized.casefold()
    if len(components) == 1:
        if not folded or folded in {"scalar", components[0].casefold()}:
            return ("scalar" if folded == "scalar" else components[0], 0, False)
        return (None, None, False)
    if len(components) != 3:
        return (None, None, False)
    if not folded or folded == "magnitude":
        return ("magnitude", None, True)
    if folded in {"x", "y", "z"}:
        index = ("x", "y", "z").index(folded)
        return (folded, index, False)
    matches = [
        index for index, component in enumerate(components) if component.casefold() == folded
    ]
    if len(matches) == 1:
        return (components[matches[0]], matches[0], False)
    return (None, None, False)


def _magnitude(values: Sequence[ResultComponentValue]) -> float | None:
    raw = tuple(item.raw_value for item in values)
    if not all(isfinite(item) for item in raw):
        return None
    return sqrt(fsum(item * item for item in raw))


def _finite_integer(value: object) -> int | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not isfinite(number) or not number.is_integer():
        return None
    return int(number)


def _entity_display(association: str, key: int | str) -> str:
    return f"{association or 'entity'} {key}"


def _stable_sort_key(association: str, key: int | str) -> tuple[int, int, int, str]:
    if association == "point":
        try:
            return (0, int(key), 0, str(key))
        except (TypeError, ValueError, OverflowError):
            return (1, 0, 0, str(key))
    parts = str(key).split(":")
    if len(parts) == 2:
        try:
            return (0, int(parts[0]), int(parts[1]), str(key))
        except (TypeError, ValueError, OverflowError):
            pass
    return (1, 0, 0, str(key))


def _display_number(value: float) -> str:
    return f"{value:.12g}"


def _probe_failure(
    request: ResultProbeRequest,
    display: str,
    status: ResultProbeStatus,
    value_status: ResultValueStatus,
    reason: str,
    message: str,
    *,
    metadata: _EntityMetadata | None = None,
) -> ResultProbeResult:
    return ResultProbeResult(
        status=status,
        stable_entity_key=request.stable_entity_key,
        entity_display_id=display,
        field_name=request.field_name,
        component=request.component,
        association=_normalize_association(request.association),
        reason_code=reason,
        diagnostics=(str(message),),
        value_status=value_status,
        coordinate=metadata.coordinate if metadata is not None else None,
        cell_type=metadata.cell_type if metadata is not None else "",
        connectivity=metadata.connectivity if metadata is not None else (),
        centroid=metadata.centroid if metadata is not None else None,
    )


__all__ = [
    "ResultComponentValue",
    "ResultProbeRequest",
    "ResultProbeResult",
    "ResultProbeStatus",
    "ResultValueStatus",
    "SelectedResultRow",
    "SelectedResultTable",
    "build_selected_result_table",
    "probe_result_entity",
]
