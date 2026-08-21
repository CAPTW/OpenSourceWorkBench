"""Lifecycle, persistence, and controller tests for durable NamedSelections."""

from __future__ import annotations

import json
from importlib import import_module
from types import SimpleNamespace

import pytest

from osw.core.project_schema import (
    BoundaryCondition,
    PhysicsSetup,
    Project,
    ProjectMetadata,
    ProjectSchemaError,
)
from osw.core.selection import BoundaryTargetRef, EntityKind, NamedSelection
from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _apis() -> tuple[object, object, object]:
    return (
        import_module("osw.core.selection"),
        import_module("osw.core.selection_resolution"),
        import_module("osw.mesh.identity"),
    )


def _mesh(*, moved: bool = False) -> MeshData:
    return MeshData(
        points=(
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 2.0 if moved else 1.0, 0.0),
        ),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )


def _durable_target(
    *,
    kind: EntityKind = EntityKind.NODE,
    entity_ids: tuple[int | str, ...] = (0, 2),
) -> object:
    selection_api, resolution_api, identity_api = _apis()
    fingerprint = identity_api.compute_mesh_fingerprint(_mesh())
    namespace = (
        resolution_api.NODE_ORDINAL_NAMESPACE
        if kind is EntityKind.NODE
        else resolution_api.CELL_ORDINAL_NAMESPACE
    )
    locator = selection_api.EntityLocator(
        identity_schema=fingerprint.schema,
        mesh_ref="mesh-1",
        mesh_fingerprint=fingerprint.digest,
        entity_kind=kind,
        id_namespace=namespace,
        entity_ids=entity_ids,
    )
    return selection_api.SelectionTargetRef(
        kind=kind,
        ids=entity_ids,
        mesh_ref="mesh-1",
        locator=locator,
    )


def test_durable_selection_roundtrip_promotes_project_to_schema_0_3() -> None:
    _selection_api, resolution_api, _identity_api = _apis()
    node = NamedSelection(
        id="selection-node",
        name="Nodes",
        entity_kind="node",
        targets=(_durable_target(),),
        source_mesh_ref="mesh-1",
    )
    cell = NamedSelection(
        id="selection-cell",
        name="Cell",
        entity_kind="cell",
        targets=(
            _durable_target(kind=EntityKind.CELL, entity_ids=("0:0",)),
        ),
        source_mesh_ref="mesh-1",
    )
    project = Project(
        metadata=ProjectMetadata(name="Picking"),
        selections=(node, cell),
    )

    payload = json.loads(json.dumps(project.to_dict()))
    reopened = Project.from_dict(payload)

    assert payload["schema_version"] == "0.3"
    assert reopened.schema_version == "0.3"
    assert [item.id for item in reopened.selections] == [
        "selection-node",
        "selection-cell",
    ]
    assert all(item.targets[0].locator is not None for item in reopened.selections)
    assert all(
        resolution_api.resolve_named_selection(item).state
        is resolution_api.ResolutionState.UNRESOLVED
        for item in reopened.selections
    )

    exact_results = [
        resolution_api.resolve_named_selection(
            item,
            mesh=_mesh(),
            mesh_ref="mesh-1",
        )
        for item in reopened.selections
    ]
    changed_results = [
        resolution_api.resolve_named_selection(
            item,
            mesh=_mesh(moved=True),
            mesh_ref="mesh-1",
        )
        for item in reopened.selections
    ]
    assert all(
        result.state is resolution_api.ResolutionState.RESOLVED
        for result in exact_results
    )
    assert all(
        result.state is resolution_api.ResolutionState.STALE
        for result in changed_results
    )

    promoted = Project(
        metadata=ProjectMetadata(name="Previously 0.2"),
        schema_version="0.2",
        selections=(node,),
    )
    assert promoted.schema_version == "0.3"

    invalid_envelope = json.loads(json.dumps(payload))
    invalid_envelope["schema_version"] = "0.2"
    with pytest.raises(ProjectSchemaError, match="schema version 0.3"):
        Project.from_dict(invalid_envelope)


def test_legacy_projects_remain_versions_0_1_and_0_2_until_reselected() -> None:
    _selection_api, resolution_api, _identity_api = _apis()
    for version in ("0.1", "0.2"):
        payload = {
            "schema_version": version,
            "metadata": {"name": f"Legacy {version}"},
            "selections": [
                {
                    "id": "legacy",
                    "name": "Legacy Nodes",
                    "entity_kind": "node",
                    "targets": [
                        {
                            "kind": "node",
                            "ids": [0, 1],
                            "mesh_ref": "mesh-1",
                            "label": "",
                            "provenance": {"kept": True},
                            "metadata": {},
                        }
                    ],
                    "source_mesh_ref": "mesh-1",
                    "solver_labels": {},
                    "metadata": {"owner": "user"},
                }
            ],
        }
        project = Project.from_dict(payload)
        result = resolution_api.resolve_named_selection(
            project.selections[0],
            mesh=_mesh(),
            mesh_ref="mesh-1",
        )

        assert project.schema_version == version
        assert project.to_dict()["schema_version"] == version
        assert project.selections[0].metadata == {"owner": "user"}
        assert project.selections[0].targets[0].provenance == {"kept": True}
        assert result.state is resolution_api.ResolutionState.STALE
        assert result.reason_code == "LEGACY_IDENTITY_UNVERIFIED"


def test_named_selection_crud_preserves_stable_identity_and_blocks_references() -> None:
    _selection_api, api, _identity_api = _apis()
    target = _durable_target()
    resolution = api.resolve_selection_target(
        target,
        mesh=_mesh(),
        mesh_ref="mesh-1",
    )

    created = api.create_named_selection(
        (),
        target,
        resolution,
        selection_id="selection-stable",
        name="Support",
        description="Original",
    )
    renamed = api.rename_named_selection(
        created,
        "selection-stable",
        "Fixed Support",
    )
    replacement = _durable_target(entity_ids=(1,))
    replaced = api.replace_named_selection_targets(
        renamed,
        "selection-stable",
        replacement,
        api.resolve_selection_target(
            replacement,
            mesh=_mesh(),
            mesh_ref="mesh-1",
        ),
    )

    assert renamed[0].id == created[0].id == "selection-stable"
    assert renamed[0].targets == created[0].targets
    assert renamed[0].description == "Original"
    assert replaced[0].id == "selection-stable"
    assert replaced[0].targets == (replacement,)
    assert replaced[0].name == "Fixed Support"

    project = Project(
        metadata=ProjectMetadata(name="Referenced"),
        selections=replaced,
        physics=(
            PhysicsSetup(
                name="structural",
                boundary_conditions=(
                    BoundaryCondition(
                        name="fix",
                        kind="fixed",
                        target_ref=BoundaryTargetRef(
                            selection_id="selection-stable"
                        ),
                    ),
                ),
            ),
        ),
    )
    references = api.find_named_selection_references(
        project,
        "selection-stable",
    )
    assert references
    assert references[0].reference_kind == "boundary_condition"
    with pytest.raises(api.NamedSelectionLifecycleError, match="referenced"):
        api.delete_named_selection(
            project.selections,
            "selection-stable",
            references=references,
        )
    assert api.delete_named_selection(
        project.selections,
        "selection-stable",
        references=(),
    ) == ()


def test_named_selection_create_and_replace_require_resolved_current_selection() -> None:
    _selection_api, api, _identity_api = _apis()
    target = _durable_target()
    unresolved = api.resolve_selection_target(target)

    with pytest.raises(api.NamedSelectionLifecycleError, match="RESOLVED"):
        api.create_named_selection(
            (),
            target,
            unresolved,
            selection_id="selection-1",
            name="Unsafe",
        )
    with pytest.raises(api.NamedSelectionLifecycleError, match="non-empty"):
        api.create_named_selection(
            (),
            None,
            api.ResolutionResult(state=api.ResolutionState.RESOLVED),
            selection_id="selection-1",
            name="Empty",
        )


class PickingSession:
    backend_kind = "fake-picking"
    capabilities = frozenset(
        {
            "mesh-preview",
            "semantic-actors",
            "picking",
            "selection-overlays",
        }
    )

    def __init__(self) -> None:
        self.callback: object | None = None
        self.pick_mode = ""
        self.calls: list[tuple[object, ...]] = []
        self.actors: dict[str, object] = {}
        self.closed = False

    def clear(self) -> None:
        self.calls.append(("clear",))
        self.actors.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        self.actors[semantic_id] = (payload, generation)
        return SimpleNamespace(warnings=(), rendered=True)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)

    def request_render(self) -> None:
        return None

    def set_pick_mode(self, mode: str, callback: object) -> None:
        self.pick_mode = mode
        self.callback = callback
        self.calls.append(("pick_mode", mode))

    def set_selection_operation(self, operation: str) -> None:
        self.calls.append(("selection_operation", operation))

    def disable_picking(self) -> None:
        self.callback = None
        self.calls.append(("disable_picking",))

    def set_hover_entities(
        self,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(("hover", entity_kind, indices, generation))

    def clear_hover(self) -> None:
        self.calls.append(("clear_hover",))

    def set_current_selection(
        self,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(("current", entity_kind, indices, generation))

    def clear_current_selection(self) -> None:
        self.calls.append(("clear_current",))

    def set_named_selection_overlay(
        self,
        selection_id: str,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(
            ("named", selection_id, entity_kind, indices, generation)
        )

    def remove_named_selection_overlay(self, selection_id: str) -> None:
        self.calls.append(("remove_named", selection_id))

    def set_active_named_selection_overlay(
        self,
        selection_id: str,
        entity_kind: str,
        indices: tuple[int, ...],
        generation: int,
    ) -> None:
        self.calls.append(
            ("active_named", selection_id, entity_kind, indices, generation)
        )

    def remove_active_named_selection_overlay(self, selection_id: str) -> None:
        self.calls.append(("remove_active_named", selection_id))

    def close(self) -> None:
        self.closed = True

    def emit(self, event: object) -> object:
        assert callable(self.callback)
        return self.callback(event)


class PickingFactory:
    backend_kind = PickingSession.backend_kind
    capabilities = PickingSession.capabilities

    def __init__(self) -> None:
        self.session = PickingSession()

    def create_session(self) -> PickingSession:
        return self.session


def _loaded_controller() -> tuple[ActiveSceneController, PickingSession]:
    factory = PickingFactory()
    controller = ActiveSceneController(factory)
    controller.load_mesh(
        _mesh(),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    return controller, factory.session


def test_controller_maps_generation_guarded_node_cell_picks_to_durable_locators() -> None:
    _selection_api, api, _identity_api = _apis()
    controller, session = _loaded_controller()

    assert controller.set_pick_mode("node")
    fingerprint = controller.current_mesh_fingerprint
    assert fingerprint is not None
    session.emit(
        {
            "generation": controller.generation,
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": "node",
            "backend_index": 2,
            "intent": "replace",
        }
    )
    session.emit(
        {
            "generation": controller.generation,
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": "node",
            "backend_index": 0,
            "intent": "add",
        }
    )
    assert controller.current_selection_target is not None
    assert controller.current_selection_target.locator is not None
    assert controller.current_selection_target.locator.entity_ids == (0, 2)
    assert controller.current_selection_resolution.state is api.ResolutionState.RESOLVED
    assert ("current", "node", (0, 2), controller.generation) in session.calls

    controller.set_hover_target(1)
    assert controller.hover_target is not None
    assert controller.hover_target.locator.entity_ids == (1,)
    assert controller.current_selection_target.locator.entity_ids == (0, 2)

    assert controller.set_pick_mode("cell")
    assert controller.current_selection_target is None
    session.emit(
        {
            "generation": controller.generation,
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": "cell",
            "backend_index": 0,
            "intent": "replace",
        }
    )
    assert controller.current_selection_target is not None
    assert controller.current_selection_target.locator.entity_ids == ("0:0",)


def test_controller_toggle_clear_replacement_and_stale_callbacks_are_deterministic() -> None:
    _selection_api, _api, _identity_api = _apis()
    controller, session = _loaded_controller()
    controller.set_pick_mode("node")
    fingerprint = controller.current_mesh_fingerprint
    assert fingerprint is not None
    base_event = {
        "generation": controller.generation,
        "mesh_ref": "mesh-1",
        "mesh_fingerprint": fingerprint.digest,
        "entity_kind": "node",
        "backend_index": 1,
        "intent": "toggle",
    }

    assert session.emit(base_event) is True
    assert session.emit(base_event) is True
    assert controller.current_selection_target is None
    assert controller.clear_current_selection() is True

    stale_callback = session.callback
    controller.load_mesh(
        _mesh(moved=True),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    assert callable(stale_callback)
    assert stale_callback(base_event) is False
    assert controller.hover_target is None
    assert controller.current_selection_target is None

    controller.close()
    controller.close()
    assert ("disable_picking",) in session.calls
    assert session.closed


def test_controller_subtract_invert_and_operation_forwarding_are_deterministic() -> (
    None
):
    _selection_api, api, _identity_api = _apis()
    controller, session = _loaded_controller()
    assert controller.set_pick_mode("node")
    assert controller.set_selection_operation("add")
    assert ("selection_operation", "add") in session.calls
    fingerprint = controller.current_mesh_fingerprint
    assert fingerprint is not None

    for backend_index in (0, 1, 2):
        assert session.emit(
            {
                "generation": controller.generation,
                "mesh_ref": "mesh-1",
                "mesh_fingerprint": fingerprint.digest,
                "entity_kind": "node",
                "backend_index": backend_index,
                "intent": "add",
            }
        )
    assert controller.current_selection_target is not None
    assert controller.current_selection_target.locator is not None
    assert controller.current_selection_target.locator.entity_ids == (0, 1, 2)

    assert session.emit(
        {
            "generation": controller.generation,
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": fingerprint.digest,
            "entity_kind": "node",
            "backend_index": 1,
            "intent": "subtract",
        }
    )
    assert controller.current_selection_target.locator.entity_ids == (0, 2)
    assert controller.invert_current_selection()
    assert controller.current_selection_target.locator.entity_ids == (1,)
    assert controller.current_selection_resolution.state is api.ResolutionState.RESOLVED
    assert ("current", "node", (1,), controller.generation) in session.calls


def test_named_selection_activation_restores_only_on_exact_fingerprint() -> None:
    _selection_api, api, _identity_api = _apis()
    controller, session = _loaded_controller()
    selection = NamedSelection(
        id="selection-active",
        name="Active Nodes",
        entity_kind="node",
        targets=(_durable_target(entity_ids=(0, 2)),),
        source_mesh_ref="mesh-1",
    )
    controller.set_named_selections((selection,))

    assert controller.set_active_named_selection_ids((selection.id,))
    assert controller.active_named_selection_ids == (selection.id,)
    assert (
        "active_named",
        selection.id,
        "node",
        (0, 2),
        controller.generation,
    ) in session.calls
    assert controller.clear_current_selection()
    assert controller.active_named_selection_ids == ()
    assert ("remove_active_named", selection.id) in session.calls
    assert controller.set_active_named_selection_ids((selection.id,))

    controller.load_mesh(
        _mesh(),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    assert controller.named_selection_resolutions[selection.id].state is (
        api.ResolutionState.RESOLVED
    )
    assert any(
        call[:2] == ("active_named", selection.id)
        and call[3] == (0, 2)
        and call[4] == controller.generation
        for call in session.calls
    )

    controller.load_mesh(
        _mesh(moved=True),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    assert controller.named_selection_resolutions[selection.id].state is (
        api.ResolutionState.STALE
    )
    assert controller.active_named_selection_ids == (selection.id,)
    assert ("remove_active_named", selection.id) in session.calls
