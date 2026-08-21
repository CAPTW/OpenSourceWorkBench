"""Qt/PyVista-free projection of setup records into deterministic overlays."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from osw.core.selection import EntityKind, NamedSelection
from osw.core.selection_resolution import ResolutionResult
from osw.core.solver_setup import (
    FixedSupportRecord,
    ForceLoadRecord,
    HeatFluxRecord,
    MaterialAssignmentRecord,
    PrescribedDisplacementRecord,
    PressureLoadRecord,
    SetupRecordKind,
    SetupRecordStatus,
    TemperatureRecord,
    force_direction,
    force_vector,
    iter_solver_setup_records,
    setup_record_kind,
    status_allows_overlay,
    surface_cell_centroid_and_normal,
)
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData

MAX_FORCE_GLYPHS = 128
SETUP_OVERLAY_SCHEMA = "osw.solver_setup_overlay.v1"


@dataclass(frozen=True)
class SetupOverlayDescriptor:
    schema_id: str
    setup_id: str
    setup_kind: SetupRecordKind
    named_selection_id: str
    mesh_ref: str
    mesh_fingerprint: str
    entity_kind: EntityKind
    canonical_entity_refs: tuple[int | str, ...]
    resolved_entity_indices: tuple[int, ...]
    overlay_role: str
    enabled: bool
    status: str
    color: str
    glyph_points: tuple[tuple[float, float, float], ...] = ()
    glyph_vectors: tuple[tuple[float, float, float], ...] = ()
    target_entity_refs: tuple[int | str, ...] = ()
    label_data: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class SetupOverlaySpec:
    actor_key: str
    record_id: str
    category: str
    target_selection_id: str
    overlay_role: str = "glyph"
    entity_kind: str = ""
    canonical_entity_refs: tuple[int | str, ...] = ()
    entity_indices: tuple[int, ...] = ()
    points: tuple[tuple[float, float, float], ...] = ()
    direction: tuple[float, float, float] | None = None
    vectors: tuple[tuple[float, float, float], ...] = ()
    color: str = "#f8fafc"
    visible: bool = True


def build_setup_overlay_descriptors(
    setup: object,
    *,
    mesh: MeshData,
    mesh_ref: str,
    selections: Sequence[NamedSelection],
    resolutions: Mapping[str, ResolutionResult],
    statuses: Mapping[str, SetupRecordStatus],
) -> tuple[SetupOverlayDescriptor, ...]:
    """Build immutable exact-mesh descriptors without native objects."""

    fingerprint = compute_mesh_fingerprint(mesh)
    selection_by_id = {selection.id: selection for selection in selections}
    descriptors: list[SetupOverlayDescriptor] = []
    for record in iter_solver_setup_records(setup):
        status = statuses.get(str(record.id))
        if status is None or not status_allows_overlay(status):
            continue
        resolution = resolutions.get(str(record.target_selection_id))
        if resolution is None:
            continue
        selection = selection_by_id.get(str(record.target_selection_id))
        kind = setup_record_kind(record)
        entity_kind = selection.entity_kind if selection is not None else _entity_kind(kind)
        canonical_refs = (
            _canonical_refs(selection)
            if selection is not None
            else tuple(resolution.transient_indices)
        )
        points, vectors = _glyph_geometry(
            record,
            mesh,
            resolution.transient_indices,
        )
        has_glyph_geometry = (
            bool(vectors)
            if isinstance(record, (PressureLoadRecord, HeatFluxRecord))
            else bool(vectors or points)
        )
        roles = _overlay_roles(record, has_glyph_geometry)
        descriptors.append(
            SetupOverlayDescriptor(
                SETUP_OVERLAY_SCHEMA,
                str(record.id),
                kind,
                str(record.target_selection_id),
                str(mesh_ref),
                fingerprint.digest,
                entity_kind,
                canonical_refs,
                tuple(resolution.transient_indices),
                "+".join(roles),
                bool(getattr(record, "enabled", True)),
                status.reason_code,
                _setup_color(kind),
                points,
                vectors,
                canonical_refs if "target" in roles else (),
                (("name", str(getattr(record, "name", ""))),),
            )
        )
    return tuple(descriptors)


def build_setup_overlay_specs(
    setup: object,
    *,
    mesh: MeshData,
    resolutions: Mapping[str, ResolutionResult],
    statuses: Mapping[str, SetupRecordStatus],
    category_visibility: Mapping[str, bool] | None = None,
    mesh_ref: str = "",
    selections: Sequence[NamedSelection] = (),
) -> tuple[SetupOverlaySpec, ...]:
    visibility = {
        "material": True,
        "fixed_support": True,
        "prescribed_displacement": True,
        "force": True,
        "pressure": True,
        "temperature": True,
        "heat_flux": True,
        **dict(category_visibility or {}),
    }
    descriptors = build_setup_overlay_descriptors(
        setup,
        mesh=mesh,
        mesh_ref=mesh_ref,
        selections=selections,
        resolutions=resolutions,
        statuses=statuses,
    )
    specs: list[SetupOverlaySpec] = []
    for descriptor in descriptors:
        category = _category(descriptor.setup_kind)
        roles = descriptor.overlay_role.split("+")
        if "target" in roles:
            specs.append(
                _spec(
                    descriptor,
                    category=category,
                    role="target",
                    visible=visibility[category],
                )
            )
        if "glyph" in roles:
            specs.append(
                _spec(
                    descriptor,
                    category=category,
                    role="glyph",
                    visible=visibility[category],
                )
            )
    return tuple(specs)


def _spec(
    descriptor: SetupOverlayDescriptor,
    *,
    category: str,
    role: str,
    visible: bool,
) -> SetupOverlaySpec:
    vectors = descriptor.glyph_vectors if role == "glyph" else ()
    points = descriptor.glyph_points if role == "glyph" else ()
    return SetupOverlaySpec(
        actor_key=f"setup_{role}:{descriptor.setup_id}",
        record_id=descriptor.setup_id,
        category=category,
        target_selection_id=descriptor.named_selection_id,
        overlay_role=role,
        entity_kind=descriptor.entity_kind.value,
        canonical_entity_refs=descriptor.canonical_entity_refs,
        entity_indices=descriptor.resolved_entity_indices,
        points=points,
        direction=vectors[0] if vectors else None,
        vectors=vectors,
        color=descriptor.color,
        visible=visible,
    )


def _glyph_geometry(
    record: object,
    mesh: MeshData,
    indices: tuple[int, ...],
) -> tuple[
    tuple[tuple[float, float, float], ...],
    tuple[tuple[float, float, float], ...],
]:
    bounded = tuple(indices[:MAX_FORCE_GLYPHS])
    if isinstance(record, (FixedSupportRecord, ForceLoadRecord, PrescribedDisplacementRecord)):
        points = _points(mesh, bounded)
        if isinstance(record, ForceLoadRecord):
            direction = _normalized(force_vector(record)) or force_direction(record)
            return points, tuple(direction for _point in points)
        if isinstance(record, PrescribedDisplacementRecord):
            values = tuple(
                0.0 if component is None else float(component.value)
                for component in record.components
            )
            direction = _normalized(values)
            return points, (() if direction is None else tuple(direction for _point in points))
        return points, ()
    if isinstance(record, (PressureLoadRecord, HeatFluxRecord)):
        points: list[tuple[float, float, float]] = []
        vectors: list[tuple[float, float, float]] = []
        sign = float(record.value.value)
        for index in bounded:
            centroid, outward = surface_cell_centroid_and_normal(mesh, index)
            points.append(centroid)
            if sign == 0.0:
                continue
            factor = (
                (-1.0 if sign > 0.0 else 1.0)
                if isinstance(record, PressureLoadRecord)
                else (1.0 if sign > 0.0 else -1.0)
            )
            vectors.append(tuple(factor * component for component in outward))
        return tuple(points), tuple(vectors)
    if isinstance(record, TemperatureRecord):
        if _entity_kind(setup_record_kind(record)) is EntityKind.NODE:
            return _points(mesh, bounded), ()
        return (), ()
    return (), ()


def _overlay_roles(record: object, has_glyph_geometry: bool) -> tuple[str, ...]:
    if isinstance(record, MaterialAssignmentRecord):
        return ("target",)
    if isinstance(record, (PressureLoadRecord, HeatFluxRecord)):
        return ("target", "glyph") if has_glyph_geometry else ("target",)
    if isinstance(record, TemperatureRecord):
        return ("target",)
    return ("glyph",)


def _canonical_refs(selection: NamedSelection) -> tuple[int | str, ...]:
    refs: list[int | str] = []
    for target in selection.targets:
        if target.locator is None:
            return ()
        refs.extend(target.locator.entity_ids)
    return tuple(refs)


def _points(
    mesh: MeshData,
    indices: tuple[int, ...],
) -> tuple[tuple[float, float, float], ...]:
    return tuple(tuple(float(value) for value in mesh.points[index]) for index in indices)


def _normalized(
    vector: tuple[float, float, float],
) -> tuple[float, float, float] | None:
    if not all(math.isfinite(value) for value in vector):
        return None
    length = math.sqrt(sum(value * value for value in vector))
    if length <= 0.0:
        return None
    return tuple(value / length for value in vector)


def _entity_kind(kind: SetupRecordKind) -> EntityKind:
    if kind in {
        SetupRecordKind.FIXED_SUPPORT,
        SetupRecordKind.PRESCRIBED_DISPLACEMENT,
        SetupRecordKind.FORCE,
    }:
        return EntityKind.NODE
    return EntityKind.CELL


def _category(kind: SetupRecordKind) -> str:
    return "material" if kind is SetupRecordKind.MATERIAL_REGION else kind.value


def _setup_color(kind: SetupRecordKind) -> str:
    return {
        SetupRecordKind.MATERIAL_REGION: "#60a5fa",
        SetupRecordKind.FIXED_SUPPORT: "#22c55e",
        SetupRecordKind.PRESCRIBED_DISPLACEMENT: "#14b8a6",
        SetupRecordKind.FORCE: "#ef4444",
        SetupRecordKind.PRESSURE: "#f97316",
        SetupRecordKind.TEMPERATURE: "#eab308",
        SetupRecordKind.HEAT_FLUX: "#a855f7",
    }[kind]


__all__ = [
    "MAX_FORCE_GLYPHS",
    "SETUP_OVERLAY_SCHEMA",
    "SetupOverlayDescriptor",
    "SetupOverlaySpec",
    "build_setup_overlay_descriptors",
    "build_setup_overlay_specs",
]
