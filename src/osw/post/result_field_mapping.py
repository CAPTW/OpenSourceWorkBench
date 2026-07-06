"""PyVista-free mapping of ResultDataset scalar fields onto mesh scalar arrays.

Given an already-built ``ResultField`` (per-entity rows) and a ``MeshData``, this
produces an overlay ``MeshData`` with the field's scalar values added as a
``point_data``/``cell_data`` array aligned to mesh nodes/cells, so the reviewed 3D
viewer can color a mesh by a *result* field through the scene shell's existing
``color_by`` seam. It runs no solver, parses no solver artifacts, generates no
meshes, and imports no rendering package: it only rearranges already-computed
values, refusing with a friendly diagnostic (rather than fabricating data) when
the values do not align to the mesh.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite

from osw.core.result_dataset import ResultField
from osw.mesh.mesh_model import MeshData

_POINT_LOCATIONS = frozenset({"point", "node", "vertex"})
_CELL_LOCATIONS = frozenset({"cell", "element"})


@dataclass(frozen=True)
class ResultFieldMapping:
    """Outcome of mapping a ``ResultField`` onto a mesh (overlay + diagnostics)."""

    mesh_data: MeshData
    field_name: str
    location: str  # "point" | "cell" | ""
    applied: bool
    diagnostics: tuple[str, ...] = field(default_factory=tuple)


def result_field_names(result_dataset: object | None) -> tuple[str, ...]:
    """Return the result field names available for coloring (order preserved)."""
    if result_dataset is None:
        return ()
    names: list[str] = []
    seen: set[str] = set()
    for item in getattr(result_dataset, "fields", ()) or ():
        name = str(getattr(item, "name", ""))
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return tuple(names)


def map_result_field_to_mesh(
    mesh_data: MeshData,
    result_field: ResultField,
    *,
    component: str | None = None,
) -> ResultFieldMapping:
    """Map one scalar component of a ``ResultField`` onto a ``MeshData`` overlay.

    Aligns the field's per-entity rows to mesh nodes (point/node location) or
    cells (cell/element location) by ``entity_id`` (0-based or 1-based contiguous
    range). On any mismatch -- unknown location, missing component, wrong count,
    or non-contiguous ids -- the coloring is *not applied* and a friendly
    diagnostic is returned; values are never fabricated.
    """

    name = str(getattr(result_field, "name", "")) or "result"
    raw_location = str(getattr(result_field, "location", ""))
    location = _normalize_location(raw_location)
    if location == "":
        return _not_applied(
            mesh_data,
            name,
            "",
            f"Result field '{name}' has an unknown location "
            f"{raw_location or '(empty)'!r}; not applied.",
        )

    components = tuple(getattr(result_field, "components", ()) or ())
    chosen = _choose_component(components, component)
    if chosen is None:
        return _not_applied(
            mesh_data,
            name,
            location,
            f"Result field '{name}' has no scalar component to color by; not applied.",
        )

    info = mesh_data.info(source="<memory>", mesh_format="mesh")
    target = info.node_count if location == "point" else info.element_count
    entity_label = "nodes" if location == "point" else "cells"

    rows = tuple(getattr(result_field, "rows", ()) or ())
    if target == 0 or len(rows) != target:
        return _not_applied(
            mesh_data,
            name,
            location,
            f"Result field '{name}' has {len(rows)} rows but the mesh has "
            f"{target} {entity_label}; not applied.",
        )

    by_id: dict[int, float] = {}
    for row in rows:
        entity_id = _coerce_entity_id(getattr(row, "entity_id", 0))
        if entity_id is None:
            return _not_applied(
                mesh_data,
                name,
                location,
                f"Result field '{name}' has an entity_id that is not a finite integer; "
                "not applied.",
            )

        if entity_id in by_id:
            return _not_applied(
                mesh_data,
                name,
                location,
                f"Result field '{name}' contains duplicate entity ID {entity_id}; "
                "not applied.",
            )

        values = getattr(row, "values", {}) or {}
        if not isinstance(values, Mapping):
            return _not_applied(
                mesh_data,
                name,
                location,
                f"Result field '{name}' row values are not a mapping; not applied.",
            )
        if chosen not in values:
            return _not_applied(
                mesh_data,
                name,
                location,
                f"Result field '{name}' component '{chosen}' is missing from some rows; "
                "not applied.",
            )

        try:
            by_id[entity_id] = float(values[chosen])
        except (TypeError, ValueError):
            return _not_applied(
                mesh_data,
                name,
                location,
                f"Result field '{name}' component '{chosen}' has a non-numeric value "
                f"for entity ID {entity_id}; not applied.",
            )

    offset = _contiguous_offset(by_id, target)
    if offset is None:
        return _not_applied(
            mesh_data,
            name,
            location,
            f"Result field '{name}' entity ids are not a contiguous range for "
            f"{target} {entity_label}; not applied.",
        )

    scalar = tuple(by_id[index + offset] for index in range(target))
    overlay = _with_scalar(mesh_data, location, name, scalar)
    return ResultFieldMapping(
        mesh_data=overlay, field_name=name, location=location, applied=True, diagnostics=()
    )


def _normalize_location(location: object) -> str:
    text = str(location or "").strip().lower()
    if text in _POINT_LOCATIONS:
        return "point"
    if text in _CELL_LOCATIONS:
        return "cell"
    return ""


def _choose_component(components: tuple[str, ...], component: str | None) -> str | None:
    if component is not None:
        return component if component in components else None
    if len(components) == 1:
        return components[0]
    if "magnitude" in components:
        return "magnitude"
    return components[0] if components else None


def _coerce_entity_id(value: object) -> int | None:
    if isinstance(value, float) and not isfinite(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def _contiguous_offset(by_id: dict[int, float], target: int) -> int | None:
    keys = sorted(by_id)
    if keys == list(range(target)):
        return 0
    if keys == list(range(1, target + 1)):
        return 1
    return None


def _with_scalar(
    mesh_data: MeshData, location: str, name: str, scalar: tuple[float, ...]
) -> MeshData:
    point_data = dict(mesh_data.point_data)
    cell_data = dict(mesh_data.cell_data)
    if location == "point":
        point_data[name] = scalar
    else:
        cell_data[name] = scalar
    return MeshData(
        points=mesh_data.points,
        cells=mesh_data.cells,
        point_data=point_data,
        cell_data=cell_data,
        field_data=dict(mesh_data.field_data),
    )


def _not_applied(
    mesh_data: MeshData, name: str, location: str, message: str
) -> ResultFieldMapping:
    return ResultFieldMapping(
        mesh_data=mesh_data,
        field_name=name,
        location=location,
        applied=False,
        diagnostics=(message,),
    )


__all__ = ["ResultFieldMapping", "map_result_field_to_mesh", "result_field_names"]
