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
from enum import StrEnum
from math import isfinite

from osw.core.result_dataset import ResultField
from osw.core.result_mesh_binding import (
    ResultMeshBindingResolution,
    ResultMeshBindingResolutionState,
)
from osw.mesh.mesh_model import MeshData

_POINT_LOCATIONS = frozenset({"point", "node", "vertex"})
_CELL_LOCATIONS = frozenset({"cell", "element"})
_CANONICAL_VECTOR_TRIPLES = (
    ("x", "y", "z"),
    ("ux", "uy", "uz"),
    ("u", "v", "w"),
    ("dx", "dy", "dz"),
)
_RESULT_COLORMAPS = frozenset({"viridis", "plasma", "magma", "cividis"})


class ScalarRangeMode(StrEnum):
    """Explicit scalar display-range policy."""

    AUTO = "AUTO"
    MANUAL = "MANUAL"


@dataclass(frozen=True)
class InteractiveScalarResult:
    """Pure exact-binding scalar projection ready for one semantic actor."""

    applied: bool
    status: str
    field_name: str = ""
    component: str = ""
    association: str = ""
    unit: str = ""
    array_name: str = ""
    values: tuple[float, ...] = ()
    data_range: tuple[float, float] | None = None
    display_range: tuple[float, float] | None = None
    range_mode: ScalarRangeMode = ScalarRangeMode.AUTO
    colormap: str = "viridis"
    colorbar_visible: bool = True
    colorbar_title: str = ""
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultVectorGlyphSpec:
    """Pure bounded vector glyph projection with transient backend indices."""

    applied: bool
    status: str
    field_name: str = ""
    association: str = ""
    selected_components: tuple[str, ...] = ()
    unit: str = ""
    scale: float = 1.0
    candidate_count: int = 0
    sampled_count: int = 0
    omitted_count: int = 0
    zero_vector_count: int = 0
    selected_candidate_ranks: tuple[int, ...] = ()
    stable_entity_keys: tuple[int | str, ...] = ()
    transient_backend_indices: tuple[int, ...] = ()
    positions: tuple[tuple[float, float, float], ...] = ()
    vectors: tuple[tuple[float, float, float], ...] = ()
    diagnostics: tuple[str, ...] = ()


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

        number = _coerce_finite_float(values[chosen])
        if number is None:
            return _not_applied(
                mesh_data,
                name,
                location,
                f"Result field '{name}' component '{chosen}' has a non-numeric value "
                f"or a non-finite value for entity ID {entity_id}; not applied.",
            )
        by_id[entity_id] = number

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


def project_interactive_scalar_result(
    mesh_data: MeshData,
    result_dataset: object,
    *,
    binding_resolution: ResultMeshBindingResolution,
    field_name: str,
    component: str | None = None,
    range_mode: ScalarRangeMode | str = ScalarRangeMode.AUTO,
    manual_range: tuple[float, float] | None = None,
    colormap: str = "viridis",
    colorbar_visible: bool = True,
) -> InteractiveScalarResult:
    """Project one exact point/cell scalar field without renderer state."""

    blocked = _binding_diagnostic(binding_resolution)
    if blocked is not None:
        return _scalar_invalid(field_name, "STALE", blocked)
    result_field, resolved_name, diagnostic = _resolve_result_field(
        result_dataset,
        field_name,
    )
    if result_field is None:
        return _scalar_invalid(
            field_name,
            "INVALID",
            diagnostic or f"Result field {field_name!r} was not found.",
        )
    chosen = _choose_component(
        tuple(str(item) for item in getattr(result_field, "components", ()) or ()),
        component,
    )
    if chosen is None:
        return _scalar_invalid(
            resolved_name,
            "INVALID",
            f"Result field {resolved_name!r} has no selectable scalar component.",
        )
    mapping = map_result_field_to_mesh(
        mesh_data,
        result_field,
        component=chosen,
    )
    if not mapping.applied:
        return _scalar_invalid(
            resolved_name,
            "INVALID",
            mapping.diagnostics[0],
            component=chosen,
        )
    values = tuple(
        float(item)
        for item in (
            mapping.mesh_data.point_data[mapping.field_name]
            if mapping.location == "point"
            else mapping.mesh_data.cell_data[mapping.field_name]
        )
    )
    if not values or any(not isfinite(item) for item in values):
        return _scalar_invalid(
            resolved_name,
            "INVALID",
            f"Result field {resolved_name!r} contains no finite scalar values.",
            component=chosen,
        )
    try:
        selected_mode = ScalarRangeMode(str(range_mode))
    except ValueError:
        return _scalar_invalid(
            resolved_name,
            "INVALID",
            "Scalar range mode must be AUTO or MANUAL.",
            component=chosen,
        )
    normalized_colormap = str(colormap).strip().lower()
    if normalized_colormap not in _RESULT_COLORMAPS:
        return _scalar_invalid(
            resolved_name,
            "INVALID",
            f"Colormap {colormap!r} is not in the bounded interactive-result set.",
            component=chosen,
        )
    minimum = min(values)
    maximum = max(values)
    data_range = (minimum, maximum)
    display_range = _automatic_scalar_range(minimum, maximum)
    if selected_mode is ScalarRangeMode.MANUAL:
        if manual_range is None or len(manual_range) != 2:
            return _scalar_invalid(
                resolved_name,
                "INVALID",
                "Manual scalar range requires finite minimum and maximum values.",
                component=chosen,
            )
        lower = _coerce_finite_float(manual_range[0])
        upper = _coerce_finite_float(manual_range[1])
        if lower is None or upper is None or lower >= upper:
            return _scalar_invalid(
                resolved_name,
                "INVALID",
                "Manual scalar range must be finite with minimum less than maximum.",
                component=chosen,
            )
        display_range = (lower, upper)
    unit = str(getattr(result_field, "unit", "") or "")
    title = f"{resolved_name} / {chosen}"
    if unit:
        title = f"{title} [{unit}]"
    return InteractiveScalarResult(
        applied=True,
        status="RESOLVED",
        field_name=resolved_name,
        component=chosen,
        association=mapping.location,
        unit=unit,
        array_name=mapping.field_name,
        values=values,
        data_range=data_range,
        display_range=display_range,
        range_mode=selected_mode,
        colormap=normalized_colormap,
        colorbar_visible=bool(colorbar_visible),
        colorbar_title=title,
    )


def build_result_vector_glyph_spec(
    mesh_data: MeshData,
    result_dataset: object,
    *,
    binding_resolution: ResultMeshBindingResolution,
    field_name: str,
    components: tuple[str, ...] | None = None,
    maximum_glyph_count: int = 500,
    scale: float = 1.0,
) -> ResultVectorGlyphSpec:
    """Build one deterministic, rank-sampled vector glyph collection."""

    blocked = _binding_diagnostic(binding_resolution)
    if blocked is not None:
        return _vector_spec_invalid(field_name, "STALE", blocked)
    if (
        not isinstance(maximum_glyph_count, int)
        or isinstance(maximum_glyph_count, bool)
        or maximum_glyph_count <= 0
    ):
        return _vector_spec_invalid(
            field_name,
            "INVALID",
            "Maximum glyph count must be a positive integer.",
        )
    finite_scale = _coerce_finite_float(scale)
    if finite_scale is None or finite_scale <= 0.0:
        return _vector_spec_invalid(
            field_name,
            "INVALID",
            "Vector glyph scale must be finite and positive.",
        )
    result_field, resolved_name, diagnostic = _resolve_result_field(
        result_dataset,
        field_name,
    )
    if result_field is None:
        return _vector_spec_invalid(
            field_name,
            "INVALID",
            diagnostic or f"Result field {field_name!r} was not found.",
        )
    mapping = map_result_vector_field_to_mesh(
        mesh_data,
        result_field,
        components=components,
    )
    if not mapping.applied:
        return _vector_spec_invalid(
            resolved_name,
            "INVALID",
            mapping.diagnostics[0],
            selected_components=mapping.selected_components,
        )
    vectors = tuple(
        tuple(float(component) for component in item)
        for item in (
            mapping.mesh_data.point_data[mapping.field_name]
            if mapping.location == "point"
            else mapping.mesh_data.cell_data[mapping.field_name]
        )
    )
    positions = (
        tuple(tuple(float(value) for value in point) for point in mesh_data.points)
        if mapping.location == "point"
        else _cell_centroids(mesh_data)
    )
    stable_keys = (
        tuple(range(len(mesh_data.points)))
        if mapping.location == "point"
        else _cell_stable_keys(mesh_data)
    )
    candidates = tuple(
        (index, stable_keys[index], positions[index], vector)
        for index, vector in enumerate(vectors)
        if any(component != 0.0 for component in vector)
    )
    zero_count = len(vectors) - len(candidates)
    ranks = _bounded_sample_ranks(len(candidates), maximum_glyph_count)
    selected = tuple(candidates[rank] for rank in ranks)
    unit = str(getattr(result_field, "unit", "") or "")
    return ResultVectorGlyphSpec(
        applied=True,
        status="RESOLVED",
        field_name=resolved_name,
        association=mapping.location,
        selected_components=mapping.selected_components,
        unit=unit,
        scale=finite_scale,
        candidate_count=len(candidates),
        sampled_count=len(selected),
        omitted_count=len(candidates) - len(selected),
        zero_vector_count=zero_count,
        selected_candidate_ranks=ranks,
        stable_entity_keys=tuple(item[1] for item in selected),
        transient_backend_indices=tuple(item[0] for item in selected),
        positions=tuple(item[2] for item in selected),
        vectors=tuple(item[3] for item in selected),
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
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not isfinite(number) or not number.is_integer():
        return None
    return int(number)


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


def _binding_diagnostic(
    resolution: ResultMeshBindingResolution,
) -> str | None:
    if resolution.state is ResultMeshBindingResolutionState.RESOLVED:
        return None
    return (
        f"Result binding is {resolution.state.value}: "
        f"{resolution.reason_code}. {resolution.message}"
    )


def _automatic_scalar_range(
    minimum: float,
    maximum: float,
) -> tuple[float, float]:
    if minimum != maximum:
        return (minimum, maximum)
    delta = max(abs(minimum) * 1e-12, 1e-12)
    return (minimum - delta, maximum + delta)


def _scalar_invalid(
    field_name: str,
    status: str,
    message: str,
    *,
    component: str = "",
) -> InteractiveScalarResult:
    return InteractiveScalarResult(
        applied=False,
        status=status,
        field_name=str(field_name),
        component=str(component),
        diagnostics=(str(message),),
    )


def _vector_spec_invalid(
    field_name: str,
    status: str,
    message: str,
    *,
    selected_components: tuple[str, ...] = (),
) -> ResultVectorGlyphSpec:
    return ResultVectorGlyphSpec(
        applied=False,
        status=status,
        field_name=str(field_name),
        selected_components=selected_components,
        diagnostics=(str(message),),
    )


def _cell_stable_keys(mesh_data: MeshData) -> tuple[str, ...]:
    return tuple(
        f"{block_ordinal}:{cell_ordinal}"
        for block_ordinal, block in enumerate(mesh_data.cells)
        for cell_ordinal in range(block.count)
    )


def _cell_centroids(
    mesh_data: MeshData,
) -> tuple[tuple[float, float, float], ...]:
    centroids: list[tuple[float, float, float]] = []
    for block in mesh_data.cells:
        for connectivity in block.data:
            if not connectivity:
                centroids.append((0.0, 0.0, 0.0))
                continue
            points = tuple(mesh_data.points[index] for index in connectivity)
            scale = 1.0 / len(points)
            centroids.append(
                (
                    sum(float(point[0]) for point in points) * scale,
                    sum(float(point[1]) for point in points) * scale,
                    sum(float(point[2]) for point in points) * scale,
                )
            )
    return tuple(centroids)


def _bounded_sample_ranks(
    candidate_count: int,
    maximum_count: int,
) -> tuple[int, ...]:
    if candidate_count <= maximum_count:
        return tuple(range(candidate_count))
    if maximum_count == 1:
        return (0,)
    return tuple(
        (rank * (candidate_count - 1)) // (maximum_count - 1)
        for rank in range(maximum_count)
    )


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
    "InteractiveScalarResult",
    "ResultFieldMapping",
    "ResultVectorGlyphSpec",
    "ResultVectorFieldMapping",
    "ScalarRangeMode",
    "build_result_vector_glyph_spec",
    "map_result_field_to_mesh",
    "map_result_vector_field_to_mesh",
    "project_interactive_scalar_result",
    "result_field_names",
]
