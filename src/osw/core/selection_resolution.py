"""Pure fail-closed resolution and lifecycle helpers for NamedSelections."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum

from osw.mesh.identity import MESH_IDENTITY_SCHEMA, compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshData

from .selection import (
    EntityKind,
    EntityLocator,
    NamedSelection,
    SelectionTargetRef,
)

NODE_ORDINAL_NAMESPACE = "osw.mesh.point_ordinal.v1"
CELL_ORDINAL_NAMESPACE = "osw.mesh.cell_block_ordinal.v1"
_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class ResolutionState(StrEnum):
    """Authoritative state of a locator against current in-memory evidence."""

    UNRESOLVED = "UNRESOLVED"
    RESOLVED = "RESOLVED"
    PARTIAL = "PARTIAL"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class ResolutionResult:
    """Safe resolution evidence with no paths or backend-native handles."""

    state: ResolutionState = ResolutionState.UNRESOLVED
    transient_indices: tuple[int, ...] = ()
    total_requested: int = 0
    resolved_count: int = 0
    missing_ids: tuple[int | str, ...] = ()
    reason_code: str = "MESH_NOT_LOADED"
    message: str = "The required mesh is not currently loaded."


@dataclass(frozen=True)
class SelectionReference:
    """One bounded Project reference that prevents cascading deletion."""

    reference_kind: str
    owner_id: str


class NamedSelectionLifecycleError(ValueError):
    """A NamedSelection mutation would violate identity or references."""


def is_solver_handoff_eligible(resolution: ResolutionResult) -> bool:
    """Only complete exact resolution is eligible for future setup handoff."""

    return resolution.state is ResolutionState.RESOLVED


def resolve_entity_locator(
    locator: EntityLocator,
    *,
    mesh: MeshData | None = None,
    mesh_ref: str | None = None,
    source_id_maps: Mapping[str, Sequence[int | str]] | None = None,
) -> ResolutionResult:
    """Resolve one durable locator against an explicitly supplied mesh."""

    invalid = _validate_locator(locator)
    if invalid is not None:
        return invalid
    if mesh is None:
        return ResolutionResult(
            state=ResolutionState.UNRESOLVED,
            total_requested=len(locator.entity_ids),
            reason_code="MESH_NOT_LOADED",
            message="The required mesh is not currently loaded.",
        )
    if str(mesh_ref or "") != locator.mesh_ref:
        return _stale_result(
            locator,
            "MESH_REF_MISMATCH",
            "The loaded mesh reference does not match this selection.",
        )

    current_fingerprint = compute_mesh_fingerprint(mesh)
    if current_fingerprint.digest != locator.mesh_fingerprint:
        return _stale_result(
            locator,
            "MESH_FINGERPRINT_MISMATCH",
            "The loaded mesh identity differs from this selection.",
        )

    expected_namespace = (
        NODE_ORDINAL_NAMESPACE
        if locator.entity_kind is EntityKind.NODE
        else CELL_ORDINAL_NAMESPACE
    )
    if locator.id_namespace == expected_namespace:
        return _resolve_ordinal_locator(locator, mesh)
    if locator.id_namespace in {NODE_ORDINAL_NAMESPACE, CELL_ORDINAL_NAMESPACE}:
        return _stale_result(
            locator,
            "ID_NAMESPACE_MISMATCH",
            "The selection identity namespace no longer matches its entity kind.",
        )
    return _resolve_source_ids(locator, mesh, source_id_maps or {})


def resolve_selection_target(
    target: SelectionTargetRef,
    *,
    mesh: MeshData | None = None,
    mesh_ref: str | None = None,
    source_id_maps: Mapping[str, Sequence[int | str]] | None = None,
) -> ResolutionResult:
    """Resolve a target, classifying index-only legacy data as stale."""

    if target.locator is None:
        return ResolutionResult(
            state=ResolutionState.STALE,
            total_requested=len(target.ids),
            reason_code="LEGACY_IDENTITY_UNVERIFIED",
            message=(
                "This legacy selection has no verified mesh identity and must "
                "be explicitly reselected."
            ),
        )
    return resolve_entity_locator(
        target.locator,
        mesh=mesh,
        mesh_ref=mesh_ref,
        source_id_maps=source_id_maps,
    )


def resolve_named_selection(
    selection: NamedSelection,
    *,
    mesh: MeshData | None = None,
    mesh_ref: str | None = None,
    source_id_maps: Mapping[str, Sequence[int | str]] | None = None,
) -> ResolutionResult:
    """Resolve all targets without silently dropping a failing target."""

    if not selection.targets:
        return ResolutionResult(
            state=ResolutionState.INVALID,
            reason_code="EMPTY_SELECTION_TARGETS",
            message="The named selection has no entity targets.",
        )
    results = tuple(
        resolve_selection_target(
            target,
            mesh=mesh,
            mesh_ref=mesh_ref,
            source_id_maps=source_id_maps,
        )
        for target in selection.targets
    )
    if len(results) == 1:
        return results[0]

    priority = (
        ResolutionState.INVALID,
        ResolutionState.STALE,
        ResolutionState.UNRESOLVED,
        ResolutionState.PARTIAL,
        ResolutionState.RESOLVED,
    )
    state = next(candidate for candidate in priority if any(
        result.state is candidate for result in results
    ))
    first = next(result for result in results if result.state is state)
    indices = tuple(
        index for result in results for index in result.transient_indices
    )
    missing = tuple(
        item for result in results for item in result.missing_ids
    )
    return ResolutionResult(
        state=state,
        transient_indices=indices if state is ResolutionState.RESOLVED else (),
        total_requested=sum(result.total_requested for result in results),
        resolved_count=sum(result.resolved_count for result in results),
        missing_ids=missing,
        reason_code=first.reason_code,
        message=first.message,
    )


def create_named_selection(
    selections: Sequence[NamedSelection],
    target: SelectionTargetRef | None,
    resolution: ResolutionResult,
    *,
    selection_id: str,
    name: str,
    description: str = "",
) -> tuple[NamedSelection, ...]:
    """Create one selection from a non-empty exact current target."""

    _require_resolved_target(target, resolution)
    normalized_id = str(selection_id or "").strip()
    normalized_name = str(name or "").strip()
    if not normalized_id:
        raise NamedSelectionLifecycleError("Named selection ID is required.")
    if not normalized_name:
        raise NamedSelectionLifecycleError("Named selection name is required.")
    if any(item.id == normalized_id for item in selections):
        raise NamedSelectionLifecycleError(
            f"Named selection ID already exists: {normalized_id}"
        )
    _require_unique_name(selections, normalized_name)
    assert target is not None
    created = NamedSelection(
        id=normalized_id,
        name=normalized_name,
        description=str(description or ""),
        entity_kind=target.kind,
        targets=(target,),
        source_mesh_ref=target.mesh_ref,
    )
    return (*tuple(selections), created)


def rename_named_selection(
    selections: Sequence[NamedSelection],
    selection_id: str,
    name: str,
) -> tuple[NamedSelection, ...]:
    """Rename without changing the stable ID or target identity."""

    normalized_name = str(name or "").strip()
    if not normalized_name:
        raise NamedSelectionLifecycleError("Named selection name is required.")
    _require_unique_name(
        selections,
        normalized_name,
        excluding_id=selection_id,
    )
    found = False
    updated: list[NamedSelection] = []
    for item in selections:
        if item.id == selection_id:
            found = True
            updated.append(replace(item, name=normalized_name))
        else:
            updated.append(item)
    if not found:
        raise NamedSelectionLifecycleError(
            f"Named selection was not found: {selection_id}"
        )
    return tuple(updated)


def replace_named_selection_targets(
    selections: Sequence[NamedSelection],
    selection_id: str,
    target: SelectionTargetRef | None,
    resolution: ResolutionResult,
) -> tuple[NamedSelection, ...]:
    """Explicitly replace targets while preserving the NamedSelection ID."""

    _require_resolved_target(target, resolution)
    assert target is not None
    found = False
    updated: list[NamedSelection] = []
    for item in selections:
        if item.id == selection_id:
            found = True
            updated.append(
                replace(
                    item,
                    entity_kind=target.kind,
                    targets=(target,),
                    source_mesh_ref=target.mesh_ref,
                )
            )
        else:
            updated.append(item)
    if not found:
        raise NamedSelectionLifecycleError(
            f"Named selection was not found: {selection_id}"
        )
    return tuple(updated)


def delete_named_selection(
    selections: Sequence[NamedSelection],
    selection_id: str,
    *,
    references: Sequence[SelectionReference],
) -> tuple[NamedSelection, ...]:
    """Delete one unreferenced selection; never cascade."""

    if references:
        kinds = ", ".join(
            f"{item.reference_kind}:{item.owner_id}" for item in references
        )
        raise NamedSelectionLifecycleError(
            f"Named selection is referenced and cannot be deleted: {kinds}"
        )
    retained = tuple(item for item in selections if item.id != selection_id)
    if len(retained) == len(tuple(selections)):
        raise NamedSelectionLifecycleError(
            f"Named selection was not found: {selection_id}"
        )
    return retained


def find_named_selection_references(
    project: object,
    selection_id: str,
) -> tuple[SelectionReference, ...]:
    """Inspect current Project-owned reference surfaces without mutation."""

    references: list[SelectionReference] = []
    for setup in getattr(project, "physics", ()) or ():
        setup_name = str(getattr(setup, "name", "") or "physics")
        for boundary in getattr(setup, "boundary_conditions", ()) or ():
            target_ref = getattr(boundary, "target_ref", None)
            if getattr(target_ref, "selection_id", "") == selection_id:
                boundary_name = str(
                    getattr(boundary, "name", "") or "boundary_condition"
                )
                references.append(
                    SelectionReference(
                        reference_kind="boundary_condition",
                        owner_id=f"{setup_name}/{boundary_name}",
                    )
                )
        for record in getattr(setup, "material_assignment_records", ()) or ():
            if record.target_selection_id == selection_id:
                references.append(
                    SelectionReference("material_assignment", record.id)
                )
        for record in getattr(setup, "fixed_support_records", ()) or ():
            if record.target_selection_id == selection_id:
                references.append(SelectionReference("fixed_support", record.id))
        for record in getattr(setup, "force_load_records", ()) or ():
            if record.target_selection_id == selection_id:
                references.append(SelectionReference("force_load", record.id))
    for asset in getattr(project, "report_screenshots", ()) or ():
        if selection_id in tuple(getattr(asset, "selection_ids", ()) or ()):
            references.append(
                SelectionReference(
                    reference_kind="report_screenshot",
                    owner_id=str(getattr(asset, "id", "") or "screenshot"),
                )
            )
    return tuple(references)


def _validate_locator(locator: EntityLocator) -> ResolutionResult | None:
    if not isinstance(locator, EntityLocator):
        return _invalid_result("MALFORMED_LOCATOR", "The entity locator is malformed.")
    if locator.identity_schema != MESH_IDENTITY_SCHEMA:
        return _invalid_result(
            "UNSUPPORTED_IDENTITY_SCHEMA",
            "The entity locator identity schema is unsupported.",
            locator,
        )
    if locator.entity_kind not in {EntityKind.NODE, EntityKind.CELL}:
        return _invalid_result(
            "UNSUPPORTED_ENTITY_KIND",
            "Only node and cell entity locators are supported.",
            locator,
        )
    if not locator.mesh_ref or not locator.id_namespace:
        return _invalid_result(
            "MALFORMED_LOCATOR",
            "The entity locator is missing required identity fields.",
            locator,
        )
    if not _DIGEST_PATTERN.fullmatch(locator.mesh_fingerprint):
        return _invalid_result(
            "INVALID_MESH_FINGERPRINT",
            "The entity locator mesh fingerprint is invalid.",
            locator,
        )
    if not locator.entity_ids:
        return _invalid_result(
            "EMPTY_ENTITY_IDS",
            "The entity locator has no entity IDs.",
            locator,
        )
    if len(set(locator.entity_ids)) != len(locator.entity_ids):
        return _invalid_result(
            "DUPLICATE_ENTITY_IDS",
            "The entity locator contains duplicate entity IDs.",
            locator,
        )
    return None


def _resolve_ordinal_locator(
    locator: EntityLocator,
    mesh: MeshData,
) -> ResolutionResult:
    resolved: list[int] = []
    missing: list[int | str] = []
    if locator.entity_kind is EntityKind.NODE:
        for entity_id in locator.entity_ids:
            if (
                isinstance(entity_id, bool)
                or not isinstance(entity_id, int)
                or entity_id < 0
            ):
                return _invalid_result(
                    "MALFORMED_NODE_ORDINAL",
                    "A node ordinal is malformed.",
                    locator,
                )
            if entity_id >= len(mesh.points):
                missing.append(entity_id)
            else:
                resolved.append(entity_id)
    else:
        offsets = _cell_block_offsets(mesh)
        for entity_id in locator.entity_ids:
            parsed = _parse_cell_ordinal(entity_id)
            if parsed is None:
                return _invalid_result(
                    "MALFORMED_CELL_ORDINAL",
                    "A cell block/local ordinal is malformed.",
                    locator,
                )
            block_ordinal, local_ordinal = parsed
            if (
                block_ordinal >= len(mesh.cells)
                or local_ordinal >= mesh.cells[block_ordinal].count
            ):
                missing.append(entity_id)
            else:
                resolved.append(offsets[block_ordinal] + local_ordinal)
    return _resolution_from_matches(locator, resolved, missing)


def _resolve_source_ids(
    locator: EntityLocator,
    mesh: MeshData,
    source_id_maps: Mapping[str, Sequence[int | str]],
) -> ResolutionResult:
    raw_map = source_id_maps.get(locator.id_namespace)
    if raw_map is None:
        return _invalid_result(
            "SOURCE_ID_MAP_UNAVAILABLE",
            "The required validated source-ID map is unavailable.",
            locator,
        )
    normalized = tuple(_normalize_source_id(item) for item in raw_map)
    domain_count = (
        len(mesh.points)
        if locator.entity_kind is EntityKind.NODE
        else sum(block.count for block in mesh.cells)
    )
    if len(normalized) > domain_count:
        return _invalid_result(
            "INVALID_SOURCE_ID_MAP",
            "The source-ID map exceeds its entity domain.",
            locator,
        )
    if len(set(normalized)) != len(normalized):
        return _invalid_result(
            "AMBIGUOUS_SOURCE_ID_MAP",
            "The source-ID map contains ambiguous duplicate IDs.",
            locator,
        )
    lookup = {value: index for index, value in enumerate(normalized)}
    resolved: list[int] = []
    missing: list[int | str] = []
    for entity_id in locator.entity_ids:
        index = lookup.get(entity_id)
        if index is None:
            missing.append(entity_id)
        else:
            resolved.append(index)
    return _resolution_from_matches(locator, resolved, missing)


def _resolution_from_matches(
    locator: EntityLocator,
    resolved: Sequence[int],
    missing: Sequence[int | str],
) -> ResolutionResult:
    state = ResolutionState.PARTIAL if missing else ResolutionState.RESOLVED
    return ResolutionResult(
        state=state,
        transient_indices=tuple(resolved),
        total_requested=len(locator.entity_ids),
        resolved_count=len(resolved),
        missing_ids=tuple(missing),
        reason_code=(
            "ENTITY_IDS_PARTIALLY_RESOLVED"
            if missing
            else "EXACT_MESH_IDENTITY_RESOLVED"
        ),
        message=(
            "Only part of the selection resolves on the exact mesh."
            if missing
            else "All selection entities resolve on the exact mesh."
        ),
    )


def _stale_result(
    locator: EntityLocator,
    reason_code: str,
    message: str,
) -> ResolutionResult:
    return ResolutionResult(
        state=ResolutionState.STALE,
        total_requested=len(locator.entity_ids),
        reason_code=reason_code,
        message=message,
    )


def _invalid_result(
    reason_code: str,
    message: str,
    locator: EntityLocator | None = None,
) -> ResolutionResult:
    return ResolutionResult(
        state=ResolutionState.INVALID,
        total_requested=len(locator.entity_ids) if locator is not None else 0,
        reason_code=reason_code,
        message=message,
    )


def _cell_block_offsets(mesh: MeshData) -> tuple[int, ...]:
    offsets: list[int] = []
    running = 0
    for block in mesh.cells:
        offsets.append(running)
        running += block.count
    return tuple(offsets)


def _parse_cell_ordinal(value: object) -> tuple[int, int] | None:
    if not isinstance(value, str):
        return None
    pieces = value.split(":")
    if len(pieces) != 2 or not all(piece.isdecimal() for piece in pieces):
        return None
    return int(pieces[0]), int(pieces[1])


def _normalize_source_id(value: object) -> int | str:
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return value
    return str(value)


def _require_resolved_target(
    target: SelectionTargetRef | None,
    resolution: ResolutionResult,
) -> None:
    if target is None or target.locator is None or not target.locator.entity_ids:
        raise NamedSelectionLifecycleError(
            "Named selection creation requires a non-empty durable current selection."
        )
    if resolution.state is not ResolutionState.RESOLVED:
        raise NamedSelectionLifecycleError(
            "Named selection targets require RESOLVED current selection evidence."
        )


def _require_unique_name(
    selections: Sequence[NamedSelection],
    name: str,
    *,
    excluding_id: str = "",
) -> None:
    if any(item.name == name and item.id != excluding_id for item in selections):
        raise NamedSelectionLifecycleError(
            f"Named selection name already exists: {name}"
        )


__all__ = [
    "CELL_ORDINAL_NAMESPACE",
    "NODE_ORDINAL_NAMESPACE",
    "NamedSelectionLifecycleError",
    "ResolutionResult",
    "ResolutionState",
    "SelectionReference",
    "create_named_selection",
    "delete_named_selection",
    "find_named_selection_references",
    "is_solver_handoff_eligible",
    "rename_named_selection",
    "replace_named_selection_targets",
    "resolve_entity_locator",
    "resolve_named_selection",
    "resolve_selection_target",
]
