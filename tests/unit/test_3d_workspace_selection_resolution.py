"""Pure resolution tests for durable node and cell entity locators."""

from __future__ import annotations

from importlib import import_module

from osw.core import selection as selection_contracts
from osw.core.selection import EntityKind, NamedSelection, SelectionTargetRef
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _resolution_api() -> object:
    return import_module("osw.core.selection_resolution")


def _identity_api() -> object:
    return import_module("osw.mesh.identity")


def _mesh(*, x_offset: float = 0.0) -> MeshData:
    return MeshData(
        points=(
            (x_offset, 0.0, 0.0),
            (x_offset + 1.0, 0.0, 0.0),
            (x_offset, 1.0, 0.0),
            (x_offset, 0.0, 1.0),
        ),
        cells=(
            MeshCellBlock("triangle", ((0, 1, 2), (0, 2, 3))),
            MeshCellBlock("line", ((0, 1),)),
        ),
    )


def _node_locator(*, ids: tuple[int, ...] = (0, 2)) -> object:
    api = _resolution_api()
    fingerprint = _identity_api().compute_mesh_fingerprint(_mesh())
    return selection_contracts.EntityLocator(
        identity_schema=fingerprint.schema,
        mesh_ref="mesh-1",
        mesh_fingerprint=fingerprint.digest,
        entity_kind=EntityKind.NODE,
        id_namespace=api.NODE_ORDINAL_NAMESPACE,
        entity_ids=ids,
    )


def _cell_locator(*, ids: tuple[str, ...] = ("0:1", "1:0")) -> object:
    api = _resolution_api()
    fingerprint = _identity_api().compute_mesh_fingerprint(_mesh())
    return selection_contracts.EntityLocator(
        identity_schema=fingerprint.schema,
        mesh_ref="mesh-1",
        mesh_fingerprint=fingerprint.digest,
        entity_kind=EntityKind.CELL,
        id_namespace=api.CELL_ORDINAL_NAMESPACE,
        entity_ids=ids,
    )


def test_resolution_state_enum_is_complete_and_solver_eligibility_is_fail_closed() -> None:
    api = _resolution_api()

    assert {state.value for state in api.ResolutionState} == {
        "UNRESOLVED",
        "RESOLVED",
        "PARTIAL",
        "STALE",
        "INVALID",
    }
    for state in api.ResolutionState:
        result = api.ResolutionResult(state=state)
        assert api.is_solver_handoff_eligible(result) is (
            state is api.ResolutionState.RESOLVED
        )


def test_node_and_cell_ordinal_locators_resolve_to_transient_indices() -> None:
    api = _resolution_api()
    node_result = api.resolve_entity_locator(
        _node_locator(),
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )
    cell_result = api.resolve_entity_locator(
        _cell_locator(),
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )

    assert node_result.state is api.ResolutionState.RESOLVED
    assert node_result.transient_indices == (0, 2)
    assert cell_result.state is api.ResolutionState.RESOLVED
    assert cell_result.transient_indices == (1, 2)
    assert api.is_solver_handoff_eligible(node_result)
    assert api.is_solver_handoff_eligible(cell_result)


def test_unloaded_exact_changed_and_partial_resolution_states_are_distinct() -> None:
    api = _resolution_api()
    locator = _node_locator(ids=(0, 99))

    unloaded = api.resolve_entity_locator(locator)
    changed = api.resolve_entity_locator(
        locator,
        mesh=_mesh(x_offset=0.25),
        mesh_ref="mesh-1",
    )
    partial = api.resolve_entity_locator(
        locator,
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )

    assert unloaded.state is api.ResolutionState.UNRESOLVED
    assert unloaded.reason_code == "MESH_NOT_LOADED"
    assert changed.state is api.ResolutionState.STALE
    assert changed.reason_code == "MESH_FINGERPRINT_MISMATCH"
    assert partial.state is api.ResolutionState.PARTIAL
    assert partial.resolved_count == 1
    assert partial.total_requested == 2
    assert partial.missing_ids == (99,)
    assert not api.is_solver_handoff_eligible(partial)


def test_legacy_index_only_selection_is_preserved_but_never_silently_resolved() -> None:
    api = _resolution_api()
    legacy = SelectionTargetRef(
        kind="node",
        ids=(0, 1),
        mesh_ref="mesh-1",
        provenance={"source": "legacy"},
    )
    result = api.resolve_selection_target(
        legacy,
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )

    assert legacy.ids == (0, 1)
    assert legacy.provenance == {"source": "legacy"}
    assert result.state is api.ResolutionState.STALE
    assert result.reason_code == "LEGACY_IDENTITY_UNVERIFIED"
    assert result.transient_indices == ()


def test_target_and_locator_identity_mismatch_is_invalid_not_silently_rebound() -> None:
    api = _resolution_api()
    target = SelectionTargetRef(
        kind="node",
        ids=(1,),
        mesh_ref="mesh-1",
        locator=_node_locator(ids=(0,)),
    )

    result = api.resolve_selection_target(
        target,
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )

    assert result.state is api.ResolutionState.INVALID
    assert result.reason_code == "TARGET_LOCATOR_IDENTITY_MISMATCH"
    assert result.transient_indices == ()


def test_malformed_unknown_and_ambiguous_locators_are_invalid() -> None:
    api = _resolution_api()
    fingerprint = _identity_api().compute_mesh_fingerprint(_mesh())

    unknown_schema = selection_contracts.EntityLocator(
        identity_schema="osw.mesh_identity.v99",
        mesh_ref="mesh-1",
        mesh_fingerprint=fingerprint.digest,
        entity_kind="node",
        id_namespace=api.NODE_ORDINAL_NAMESPACE,
        entity_ids=(0,),
    )
    duplicate = selection_contracts.EntityLocator(
        identity_schema=fingerprint.schema,
        mesh_ref="mesh-1",
        mesh_fingerprint=fingerprint.digest,
        entity_kind="node",
        id_namespace=api.NODE_ORDINAL_NAMESPACE,
        entity_ids=(0, 0),
    )
    unsupported = selection_contracts.EntityLocator(
        identity_schema=fingerprint.schema,
        mesh_ref="mesh-1",
        mesh_fingerprint=fingerprint.digest,
        entity_kind="face",
        id_namespace="osw.mesh.face_ordinal.v1",
        entity_ids=(0,),
    )

    assert api.resolve_entity_locator(unknown_schema).reason_code == (
        "UNSUPPORTED_IDENTITY_SCHEMA"
    )
    assert api.resolve_entity_locator(duplicate).reason_code == "DUPLICATE_ENTITY_IDS"
    assert api.resolve_entity_locator(unsupported).reason_code == (
        "UNSUPPORTED_ENTITY_KIND"
    )
    assert all(
        result.state is api.ResolutionState.INVALID
        for result in (
            api.resolve_entity_locator(unknown_schema),
            api.resolve_entity_locator(duplicate),
            api.resolve_entity_locator(unsupported),
        )
    )


def test_explicit_source_namespace_reports_partial_or_invalid_maps() -> None:
    api = _resolution_api()
    fingerprint = _identity_api().compute_mesh_fingerprint(_mesh())
    locator = selection_contracts.EntityLocator(
        identity_schema=fingerprint.schema,
        mesh_ref="mesh-1",
        mesh_fingerprint=fingerprint.digest,
        entity_kind="node",
        id_namespace="meshio:point-id",
        entity_ids=("n-1", "n-4"),
    )

    partial = api.resolve_entity_locator(
        locator,
        mesh=_mesh(),
        mesh_ref="mesh-1",
        source_id_maps={"meshio:point-id": ("n-1", "n-2", "n-3")},
    )
    invalid = api.resolve_entity_locator(
        locator,
        mesh=_mesh(),
        mesh_ref="mesh-1",
        source_id_maps={"meshio:point-id": ("n-1", "n-1", "n-3", "n-4")},
    )

    assert partial.state is api.ResolutionState.PARTIAL
    assert partial.transient_indices == (0,)
    assert partial.missing_ids == ("n-4",)
    assert invalid.state is api.ResolutionState.INVALID
    assert invalid.reason_code == "AMBIGUOUS_SOURCE_ID_MAP"


def test_named_selection_resolution_aggregates_one_durable_target() -> None:
    api = _resolution_api()
    target = SelectionTargetRef(
        kind="cell",
        ids=("0:1",),
        mesh_ref="mesh-1",
        locator=_cell_locator(ids=("0:1",)),
    )
    selection = NamedSelection(
        id="selection-1",
        name="Cells",
        entity_kind="cell",
        targets=(target,),
        source_mesh_ref="mesh-1",
    )

    result = api.resolve_named_selection(
        selection,
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )

    assert result.state is api.ResolutionState.RESOLVED
    assert result.transient_indices == (1,)
