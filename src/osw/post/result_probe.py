"""Pure exact-identity result probes and bounded selected-entity tables."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

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
class ResultProbeResult:
    """Resolved stored value or an explicit fail-closed diagnostic."""

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


@dataclass(frozen=True)
class SelectedResultRow:
    """One deterministic table row produced through the probe lookup."""

    stable_entity_key: int | str
    entity_display_id: str
    value: float
    unit: str


@dataclass(frozen=True)
class SelectedResultTable:
    """Bounded table of exact stored values for selected stable entities."""

    rows: tuple[SelectedResultRow, ...]
    total_count: int
    truncated_count: int
    limit: int
    field_name: str
    component: str
    association: str


def probe_result_entity(
    mesh: MeshData,
    result_dataset: object,
    request: ResultProbeRequest,
    *,
    binding_resolution: ResultMeshBindingResolution,
) -> ResultProbeResult:
    """Return one exact stored value; never interpolate or remap geometrically."""

    association = _normalize_association(request.association)
    display = _entity_display(association, request.stable_entity_key)
    if binding_resolution.state is not ResultMeshBindingResolutionState.RESOLVED:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.STALE,
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
            "MESH_FINGERPRINT_MISMATCH",
            "Probe request does not match the exact active mesh fingerprint.",
        )
    if str(getattr(result_dataset, "dataset_id", "")) != request.dataset_id:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.INVALID,
            "RESULT_DATASET_ID_MISMATCH",
            "Probe request does not match the active ResultDataset.",
        )
    field = _find_field(result_dataset, request.field_name)
    if field is None:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.NOT_FOUND,
            "RESULT_FIELD_NOT_FOUND",
            "Requested result field is not available.",
        )
    field_association = _normalize_association(getattr(field, "location", ""))
    if not association or association != field_association:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.ASSOCIATION_MISMATCH,
            "ASSOCIATION_MISMATCH",
            "Probe association does not match the field association.",
        )
    components = tuple(str(item) for item in getattr(field, "components", ()) or ())
    if request.component not in components:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.NOT_FOUND,
            "RESULT_COMPONENT_NOT_FOUND",
            "Requested result component is not available.",
        )
    ordinal = _stable_key_ordinal(mesh, association, request.stable_entity_key)
    if ordinal is None:
        return _probe_failure(
            request,
            display,
            ResultProbeStatus.NOT_FOUND,
            "STABLE_ENTITY_NOT_FOUND",
            "Stable entity key is outside the active mesh domain.",
        )
    rows = tuple(getattr(field, "rows", ()) or ())
    target = len(mesh.points) if association == "point" else _cell_count(mesh)
    value, reason = _value_for_ordinal(
        rows,
        target=target,
        ordinal=ordinal,
        component=request.component,
    )
    if reason:
        status = (
            ResultProbeStatus.NOT_FOUND
            if reason == "RESULT_ROW_NOT_FOUND"
            else ResultProbeStatus.INVALID
        )
        return _probe_failure(request, display, status, reason, reason)
    assert value is not None
    return ResultProbeResult(
        status=ResultProbeStatus.RESOLVED,
        stable_entity_key=request.stable_entity_key,
        entity_display_id=display,
        field_name=request.field_name,
        component=request.component,
        association=association,
        value=value,
        unit=str(getattr(field, "unit", "") or ""),
        reason_code="EXACT_STORED_VALUE",
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
    """Build a deterministic table through the exact probe path."""

    if (
        not isinstance(limit, int)
        or isinstance(limit, bool)
        or not 1 <= limit <= 500
    ):
        raise ValueError("Selected-result table limit must be between 1 and 500.")
    normalized = _normalize_association(association)
    ordered = tuple(
        sorted(
            set(stable_entity_keys),
            key=lambda item: _stable_sort_key(normalized, item),
        )
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
        if result.status is not ResultProbeStatus.RESOLVED or result.value is None:
            continue
        rows.append(
            SelectedResultRow(
                stable_entity_key=key,
                entity_display_id=result.entity_display_id,
                value=result.value,
                unit=result.unit,
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


def _stable_key_ordinal(
    mesh: MeshData,
    association: str,
    key: int | str,
) -> int | None:
    if association == "point":
        if isinstance(key, bool):
            return None
        try:
            ordinal = int(key)
        except (TypeError, ValueError, OverflowError):
            return None
        return ordinal if 0 <= ordinal < len(mesh.points) else None
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
    if not 0 <= local_ordinal < block.count:
        return None
    return sum(item.count for item in mesh.cells[:block_ordinal]) + local_ordinal


def _value_for_ordinal(
    rows: tuple[object, ...],
    *,
    target: int,
    ordinal: int,
    component: str,
) -> tuple[float | None, str]:
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
    zero_based = list(range(target))
    one_based = list(range(1, target + 1))
    if keys == zero_based:
        offset = 0
    elif keys == one_based:
        offset = 1
    else:
        return None, "RESULT_ROW_NOT_FOUND"
    row = by_id.get(ordinal + offset)
    if row is None:
        return None, "RESULT_ROW_NOT_FOUND"
    values = getattr(row, "values", None)
    if not isinstance(values, Mapping) or component not in values:
        return None, "RESULT_COMPONENT_NOT_FOUND"
    try:
        number = float(values[component])
    except (TypeError, ValueError, OverflowError):
        return None, "NONFINITE_RESULT_VALUE"
    if not isfinite(number):
        return None, "NONFINITE_RESULT_VALUE"
    return number, ""


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


def _stable_sort_key(association: str, key: int | str) -> tuple[int, int]:
    if association == "point":
        try:
            return (0, int(key))
        except (TypeError, ValueError, OverflowError):
            return (1, 0)
    parts = str(key).split(":")
    if len(parts) == 2:
        try:
            return (int(parts[0]), int(parts[1]))
        except (TypeError, ValueError, OverflowError):
            pass
    return (2**31 - 1, 2**31 - 1)


def _probe_failure(
    request: ResultProbeRequest,
    display: str,
    status: ResultProbeStatus,
    reason: str,
    message: str,
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
    )


__all__ = [
    "ResultProbeRequest",
    "ResultProbeResult",
    "ResultProbeStatus",
    "SelectedResultRow",
    "SelectedResultTable",
    "build_selected_result_table",
    "probe_result_entity",
]
