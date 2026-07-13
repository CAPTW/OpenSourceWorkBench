"""PyVista-free mapping of ResultDataset fields onto mesh data arrays.

Given an already-built ``ResultField`` (per-entity rows) and a ``MeshData``, this
produces an overlay ``MeshData`` with the field's scalar values added as a
``point_data``/``cell_data`` array aligned to mesh nodes/cells, so the reviewed 3D
viewer can color a mesh by a *result* field through the scene shell's existing
``color_by`` seam.

The same module also exposes the bounded vector overlay mapper used by Mesh
Viewer glyph-preview controls/state. It runs no solver, parses no solver
artifacts, generates no meshes, and imports no rendering package: it only
rearranges already-computed values, refusing with a friendly diagnostic (rather
than fabricating data) when the values do not align to the mesh.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite

from osw.core.result_dataset import ResultField
from osw.mesh.mesh_model import MeshData

_POINT_LOCATIONS = frozenset({"point", "node", "vertex"})
_CELL_LOCATIONS = frozenset({"cell", "element"})
_CANONICAL_VECTOR_TRIPLES = (
    ("x", "y", "z"),
    ("ux", "uy", "uz"),
    ("u", "v", "w"),
    ("dx", "dy", "dz"),
)


@dataclass(frozen=True)
class ResultFieldMapping:
    """Outcome of mapping a ``ResultField`` onto a mesh (overlay + diagnostics)."""

    mesh_data: MeshData
    field_name: str
    location: str  # "point" | "cell" | ""
    applied: bool
    diagnostics: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ResultVectorFieldMapping:
    """Outcome of mapping a vector ``ResultField`` onto a mesh overlay."""

    mesh_data: MeshData
    field_name: str
    location: str  # "point" | "cell" | ""
    selected_components: tuple[str, ...]
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


def map_result_vector_field_to_mesh(
    mesh_data: MeshData,
    result_source: object,
    *,
    field: str | None = None,
    components: tuple[str, ...] | None = None,
    field_name: str | None = None,
) -> ResultVectorFieldMapping:
    """Map one 3-component vector ``ResultField`` onto a copied ``MeshData``.

    ``result_source`` may be a ``ResultField`` directly, or a dataset-like object
    with a ``fields`` iterable plus an explicit ``field`` name. The helper is
    intentionally explicit: it will not guess among dataset fields.
    """

    result_field, source_name, resolve_diagnostic = _resolve_result_field(result_source, field)
    overlay_name = field_name or f"result_vector:{source_name or 'result'}"
    if result_field is None:
        return _vector_not_applied(
            mesh_data,
            overlay_name,
            "",
            (),
            resolve_diagnostic or "Result field not found; vector overlay not applied.",
        )

    raw_location = str(getattr(result_field, "location", ""))
    location = _normalize_location(raw_location)
    if location == "":
        return _vector_not_applied(
            mesh_data,
            overlay_name,
            "",
            (),
            f"Result field '{source_name}' has an unknown location "
            f"{raw_location or '(empty)'!r}; vector overlay not applied.",
        )

    selected_components, component_diagnostic = _choose_vector_components(
        tuple(str(item) for item in getattr(result_field, "components", ()) or ()),
        components,
        source_name,
    )
    if component_diagnostic is not None:
        return _vector_not_applied(
            mesh_data,
            overlay_name,
            location,
            selected_components,
            component_diagnostic,
        )

    info = mesh_data.info(source="<memory>", mesh_format="mesh")
    target = info.node_count if location == "point" else info.element_count
    entity_label = "nodes" if location == "point" else "cells"

    rows = tuple(getattr(result_field, "rows", ()) or ())
    if target == 0 or len(rows) != target:
        return _vector_not_applied(
            mesh_data,
            overlay_name,
            location,
            selected_components,
            f"Result field '{source_name}' has {len(rows)} rows but the mesh has "
            f"{target} {entity_label}; vector overlay not applied.",
        )

    by_id: dict[int, tuple[float, float, float]] = {}
    for row in rows:
        entity_id = _coerce_vector_entity_id(getattr(row, "entity_id", 0))
        if entity_id is None:
            return _vector_not_applied(
                mesh_data,
                overlay_name,
                location,
                selected_components,
                f"Result field '{source_name}' has an entity_id that is not a finite "
                "integer; vector overlay not applied.",
            )

        if entity_id in by_id:
            return _vector_not_applied(
                mesh_data,
                overlay_name,
                location,
                selected_components,
                f"Result field '{source_name}' contains duplicate entity ID {entity_id}; "
                "vector overlay not applied.",
            )

        values = getattr(row, "values", {}) or {}
        if not isinstance(values, Mapping):
            return _vector_not_applied(
                mesh_data,
                overlay_name,
                location,
                selected_components,
                f"Result field '{source_name}' row values are not a mapping; "
                "vector overlay not applied.",
            )

        vector_values: list[float] = []
        for component_name in selected_components:
            if component_name not in values:
                return _vector_not_applied(
                    mesh_data,
                    overlay_name,
                    location,
                    selected_components,
                    f"Result field '{source_name}' component '{component_name}' is "
                    "missing from some rows; vector overlay not applied.",
                )
            component_value = _coerce_finite_float(values[component_name])
            if component_value is None:
                return _vector_not_applied(
                    mesh_data,
                    overlay_name,
                    location,
                    selected_components,
                    f"Result field '{source_name}' component '{component_name}' has a "
                    f"non-numeric or non-finite value for entity ID {entity_id}; "
                    "vector overlay not applied.",
                )
            vector_values.append(component_value)

        by_id[entity_id] = (vector_values[0], vector_values[1], vector_values[2])

    offset = _contiguous_offset(by_id, target)
    if offset is None:
        return _vector_not_applied(
            mesh_data,
            overlay_name,
            location,
            selected_components,
            f"Result field '{source_name}' entity ids are not a contiguous range for "
            f"{target} {entity_label}; vector overlay not applied.",
        )

    vector = tuple(by_id[index + offset] for index in range(target))
    overlay = _with_vector(mesh_data, location, overlay_name, vector)
    return ResultVectorFieldMapping(
        mesh_data=overlay,
        field_name=overlay_name,
        location=location,
        selected_components=selected_components,
        applied=True,
        diagnostics=(),
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


def _resolve_result_field(
    result_source: object, field_name: str | None
) -> tuple[object | None, str, str | None]:
    if isinstance(result_source, ResultField):
        name = str(getattr(result_source, "name", "")) or "result"
        return result_source, name, None

    requested = str(field_name or "").strip()
    if not requested:
        return (
            None,
            "result",
            "A result field name is required when mapping vectors from a dataset; "
            "vector overlay not applied.",
        )

    for item in getattr(result_source, "fields", ()) or ():
        if str(getattr(item, "name", "")) == requested:
            return item, requested, None

    return (
        None,
        requested,
        f"Result field '{requested}' was not found; vector overlay not applied.",
    )


def _choose_vector_components(
    available_components: tuple[str, ...],
    selected_components: tuple[str, ...] | None,
    field_name: str,
) -> tuple[tuple[str, ...], str | None]:
    if selected_components is not None:
        chosen = tuple(str(item) for item in selected_components)
        if len(chosen) != 3:
            return (
                chosen,
                f"Result field '{field_name}' requires exactly three selected vector "
                "components; vector overlay not applied.",
            )
        missing = tuple(component for component in chosen if component not in available_components)
        if missing:
            return (
                chosen,
                f"Result field '{field_name}' is missing requested vector component(s) "
                f"{', '.join(missing)}; vector overlay not applied.",
            )
        return chosen, None

    folded = [component.casefold() for component in available_components]
    if len(folded) != len(set(folded)):
        return (
            (),
            f"Result field '{field_name}' has ambiguous component names after case "
            "normalization; vector overlay not applied.",
        )

    matches = _matching_vector_triples(available_components)
    if len(matches) > 1:
        return (
            (),
            f"Result field '{field_name}' has ambiguous default vector component "
            "triples; vector overlay not applied.",
        )

    if len(available_components) < 3:
        return (
            (),
            f"Result field '{field_name}' has fewer than three vector components; "
            "2D vector padding is deferred and vector overlay not applied.",
        )

    if len(available_components) > 3:
        return (
            (),
            f"Result field '{field_name}' has more than three components; tensor-like "
            "or mixed fields are deferred and vector overlay not applied.",
        )

    if matches:
        return matches[0], None

    return (
        (),
        f"Result field '{field_name}' does not contain a supported default vector "
        "component triple; provide explicit components.",
    )


def _matching_vector_triples(components: tuple[str, ...]) -> tuple[tuple[str, str, str], ...]:
    by_folded = {component.casefold(): component for component in components}
    matches: list[tuple[str, str, str]] = []
    for triple in _CANONICAL_VECTOR_TRIPLES:
        if all(component in by_folded for component in triple):
            matches.append(
                (
                    by_folded[triple[0]],
                    by_folded[triple[1]],
                    by_folded[triple[2]],
                )
            )
    return tuple(matches)


def _coerce_vector_entity_id(value: object) -> int | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not isfinite(number) or not number.is_integer():
        return None
    return int(number)


def _coerce_finite_float(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if isfinite(number) else None


def _contiguous_offset(by_id: Mapping[int, object], target: int) -> int | None:
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


def _with_vector(
    mesh_data: MeshData,
    location: str,
    name: str,
    vector: tuple[tuple[float, float, float], ...],
) -> MeshData:
    point_data = dict(mesh_data.point_data)
    cell_data = dict(mesh_data.cell_data)
    if location == "point":
        point_data[name] = vector
    else:
        cell_data[name] = vector
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


def _vector_not_applied(
    mesh_data: MeshData,
    name: str,
    location: str,
    selected_components: tuple[str, ...],
    message: str,
) -> ResultVectorFieldMapping:
    return ResultVectorFieldMapping(
        mesh_data=mesh_data,
        field_name=name,
        location=location,
        selected_components=selected_components,
        applied=False,
        diagnostics=(message,),
    )


__all__ = [
    "ResultFieldMapping",
    "ResultVectorFieldMapping",
    "map_result_field_to_mesh",
    "map_result_vector_field_to_mesh",
    "result_field_names",
]
