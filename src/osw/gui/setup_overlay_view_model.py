"""Qt/PyVista-free projection of ready setup records into overlay payloads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from osw.core.selection_resolution import ResolutionResult
from osw.core.solver_setup import (
    SetupReadiness,
    SetupRecordStatus,
    force_direction,
)
from osw.mesh.mesh_model import MeshData

MAX_FORCE_GLYPHS = 128


@dataclass(frozen=True)
class SetupOverlaySpec:
    actor_key: str
    record_id: str
    category: str
    target_selection_id: str
    entity_indices: tuple[int, ...] = ()
    points: tuple[tuple[float, float, float], ...] = ()
    direction: tuple[float, float, float] | None = None
    visible: bool = True


def build_setup_overlay_specs(
    setup: object,
    *,
    mesh: MeshData,
    resolutions: Mapping[str, ResolutionResult],
    statuses: Mapping[str, SetupRecordStatus],
    category_visibility: Mapping[str, bool] | None = None,
) -> tuple[SetupOverlaySpec, ...]:
    visibility = {
        "material": True,
        "fixed_support": True,
        "force": True,
        **dict(category_visibility or {}),
    }
    specs: list[SetupOverlaySpec] = []
    for record in getattr(setup, "material_assignment_records", ()) or ():
        if not _ready(record.id, statuses):
            continue
        indices = resolutions[record.target_selection_id].transient_indices
        specs.append(
            SetupOverlaySpec(
                actor_key=f"setup:material:{record.id}",
                record_id=record.id,
                category="material",
                target_selection_id=record.target_selection_id,
                entity_indices=indices,
                visible=visibility["material"],
            )
        )
    for record in getattr(setup, "fixed_support_records", ()) or ():
        if not _ready(record.id, statuses):
            continue
        indices = resolutions[record.target_selection_id].transient_indices
        specs.append(
            SetupOverlaySpec(
                actor_key=f"setup:fixed-support:{record.id}",
                record_id=record.id,
                category="fixed_support",
                target_selection_id=record.target_selection_id,
                entity_indices=indices,
                points=_points(mesh, indices),
                visible=visibility["fixed_support"],
            )
        )
    for record in getattr(setup, "force_load_records", ()) or ():
        if not _ready(record.id, statuses):
            continue
        indices = resolutions[record.target_selection_id].transient_indices[
            :MAX_FORCE_GLYPHS
        ]
        specs.append(
            SetupOverlaySpec(
                actor_key=f"setup:force:{record.id}",
                record_id=record.id,
                category="force",
                target_selection_id=record.target_selection_id,
                entity_indices=indices,
                points=_points(mesh, indices),
                direction=force_direction(record),
                visible=visibility["force"],
            )
        )
    return tuple(specs)


def _ready(
    record_id: str,
    statuses: Mapping[str, SetupRecordStatus],
) -> bool:
    status = statuses.get(record_id)
    return status is not None and status.state is SetupReadiness.READY


def _points(
    mesh: MeshData,
    indices: tuple[int, ...],
) -> tuple[tuple[float, float, float], ...]:
    return tuple(tuple(float(value) for value in mesh.points[index]) for index in indices)


__all__ = [
    "MAX_FORCE_GLYPHS",
    "SetupOverlaySpec",
    "build_setup_overlay_specs",
]
