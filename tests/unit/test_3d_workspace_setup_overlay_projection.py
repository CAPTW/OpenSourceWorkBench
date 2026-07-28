from __future__ import annotations

from importlib import import_module
from types import SimpleNamespace

import pytest

from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import PhysicsSetup
from osw.core.selection import (
    EntityKind,
    EntityLocator,
    NamedSelection,
    SelectionTargetRef,
)
from osw.core.selection_resolution import (
    NODE_ORDINAL_NAMESPACE,
    ResolutionResult,
    ResolutionState,
)
from osw.core.units import Quantity
from osw.gui.workspace_scene_controller import (
    ActiveSceneController,
    SceneRendererInitializationError,
)
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _apis() -> tuple[object, object]:
    try:
        return (
            import_module("osw.core.solver_setup"),
            import_module("osw.gui.setup_overlay_view_model"),
        )
    except ModuleNotFoundError:
        pytest.fail("setup overlay contracts are missing", pytrace=False)


def _resolved(*indices: int) -> ResolutionResult:
    return ResolutionResult(
        ResolutionState.RESOLVED,
        indices,
        len(indices),
        len(indices),
        (),
        "RESOLVED",
        "Resolved.",
    )


def _material() -> Material:
    return Material(
        "steel",
        "Steel",
        elastic=IsotropicElastic(Quantity(210e9, "Pa"), 0.3),
    )


def _mesh() -> MeshData:
    return MeshData(
        points=((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)),
        cells=(MeshCellBlock("tetra", ((0, 1, 2, 3),)),),
    )


def _durable_node_selection() -> NamedSelection:
    mesh = _mesh()
    fingerprint = compute_mesh_fingerprint(mesh)
    locator = EntityLocator(
        fingerprint.schema,
        "mesh-1",
        fingerprint.digest,
        EntityKind.NODE,
        NODE_ORDINAL_NAMESPACE,
        (1,),
    )
    return NamedSelection(
        "nodes",
        "Nodes",
        entity_kind=EntityKind.NODE,
        targets=(
            SelectionTargetRef(
                EntityKind.NODE,
                (1,),
                "mesh-1",
                locator=locator,
            ),
        ),
    )


def test_ready_records_project_to_stable_semantic_actor_specs() -> None:
    api, view_model = _apis()
    mesh = _mesh()
    setup = PhysicsSetup(
        material_assignment_records=[
            api.MaterialAssignmentRecord("mat-a", "Steel", "steel", "cells")
        ],
        fixed_support_records=[
            api.FixedSupportRecord("fix-a", "Clamp", "fixed")
        ],
        force_load_records=[
            api.ForceLoadRecord(
                "force-a",
                "Push",
                "tip",
                Quantity(10.0, "N"),
                (2.0, 0.0, 0.0),
            )
        ],
    )
    selections = (
        NamedSelection("cells", "Cells", entity_kind=EntityKind.CELL),
        NamedSelection("fixed", "Fixed", entity_kind=EntityKind.NODE),
        NamedSelection("tip", "Tip", entity_kind=EntityKind.NODE),
    )
    resolutions = {
        "cells": _resolved(0),
        "fixed": _resolved(0, 2),
        "tip": _resolved(1),
    }
    statuses = {
        item.record_id: item
        for item in api.evaluate_solver_setup(
            setup,
            selections=selections,
            materials=(_material(),),
            resolutions=resolutions,
        )
    }

    specs = view_model.build_setup_overlay_specs(
        setup,
        mesh=mesh,
        resolutions=resolutions,
        statuses=statuses,
    )

    assert [item.actor_key for item in specs] == [
        "setup:material:mat-a",
        "setup:fixed-support:fix-a",
        "setup:force:force-a",
    ]
    assert specs[0].entity_indices == (0,)
    assert specs[1].points == ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0))
    assert specs[2].direction == (1.0, 0.0, 0.0)

    hidden = view_model.build_setup_overlay_specs(
        setup,
        mesh=mesh,
        resolutions=resolutions,
        statuses=statuses,
        category_visibility={
            "material": False,
            "fixed_support": True,
            "force": False,
        },
    )
    assert [item.visible for item in hidden] == [False, True, False]


def test_blocked_records_are_not_rendered_and_force_glyphs_are_bounded() -> None:
    api, view_model = _apis()
    count = view_model.MAX_FORCE_GLYPHS + 5
    mesh = MeshData(
        points=tuple((float(index), 0.0, 0.0) for index in range(count)),
        cells=(),
    )
    record = api.ForceLoadRecord(
        "force-a",
        "Load",
        "nodes",
        Quantity(1.0, "N"),
        (1.0, 0.0, 0.0),
    )
    setup = PhysicsSetup(force_load_records=[record])
    ready = api.SetupRecordStatus(
        "force-a",
        api.SetupRecordKind.FORCE,
        api.SetupReadiness.READY,
        "READY",
        "Ready.",
    )

    specs = view_model.build_setup_overlay_specs(
        setup,
        mesh=mesh,
        resolutions={"nodes": _resolved(*range(count))},
        statuses={"force-a": ready},
    )
    assert len(specs[0].points) == view_model.MAX_FORCE_GLYPHS
    assert specs[0].points[0] == (0.0, 0.0, 0.0)

    blocked = api.SetupRecordStatus(
        "force-a",
        api.SetupRecordKind.FORCE,
        api.SetupReadiness.BLOCKED,
        "STALE_SELECTION",
        "Stale.",
    )
    assert (
        view_model.build_setup_overlay_specs(
            setup,
            mesh=mesh,
            resolutions={"nodes": _resolved(0)},
            statuses={"force-a": blocked},
        )
        == ()
    )


class SetupSession:
    backend_kind = "fake-setup"
    capabilities = frozenset(
        {
            "mesh-preview",
            "semantic-actors",
            "semantic-visibility",
            "setup-overlays",
        }
    )

    def __init__(self) -> None:
        self.actors: dict[str, object] = {}
        self.calls: list[tuple[object, ...]] = []
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
        self.actors[semantic_id] = payload
        self.calls.append(("replace", semantic_id, generation))
        return SimpleNamespace(warnings=(), rendered=True)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)
        self.calls.append(("remove", semantic_id))

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.calls.append(("visible", semantic_id, visible))

    def request_render(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class SetupFactory:
    backend_kind = SetupSession.backend_kind
    capabilities = SetupSession.capabilities

    def __init__(self) -> None:
        self.session = SetupSession()

    def create_session(self) -> SetupSession:
        return self.session


def _force_setup() -> PhysicsSetup:
    api, _view_model = _apis()
    return PhysicsSetup(
        force_load_records=[
            api.ForceLoadRecord(
                "force-a",
                "Force",
                "nodes",
                Quantity(10.0, "N"),
                (1.0, 0.0, 0.0),
            )
        ]
    )


def test_controller_replaces_deletes_visibility_and_mesh_identity() -> None:
    api, _view_model = _apis()
    factory = SetupFactory()
    controller = ActiveSceneController(factory)
    controller.set_named_selections((_durable_node_selection(),))
    controller.set_solver_setup(_force_setup())

    controller.load_mesh(
        _mesh(),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    assert controller.setup_statuses["force-a"].state is api.SetupReadiness.READY
    assert "setup:force:force-a" in factory.session.actors

    assert controller.set_setup_category_visible("force", False) is True
    assert ("visible", "setup:force:force-a", False) in factory.session.calls

    controller.set_solver_setup(PhysicsSetup())
    assert "setup:force:force-a" not in factory.session.actors
    assert ("remove", "setup:force:force-a") in factory.session.calls

    controller.set_solver_setup(_force_setup())
    changed = MeshData(
        points=((0, 0, 0), (2, 0, 0), (0, 1, 0), (0, 0, 1)),
        cells=(MeshCellBlock("tetra", ((0, 1, 2, 3),)),),
    )
    controller.load_mesh(
        changed,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    assert controller.setup_statuses["force-a"].state is api.SetupReadiness.BLOCKED
    assert controller.setup_statuses["force-a"].reason_code == "MESH_FINGERPRINT_MISMATCH"
    assert "setup:force:force-a" not in factory.session.actors

    controller.load_mesh(
        _mesh(),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )
    assert controller.setup_statuses["force-a"].state is api.SetupReadiness.READY
    assert "setup:force:force-a" in factory.session.actors

    controller.clear()
    assert controller.setup_statuses == {}
    assert "setup:force:force-a" not in factory.session.actors


class FailingSetupFactory:
    backend_kind = "pyvistaqt"
    capabilities = SetupSession.capabilities

    def create_session(self) -> SetupSession:
        raise SceneRendererInitializationError("renderer unavailable")


def test_fallback_still_recomputes_setup_readiness_from_exact_mesh() -> None:
    api, _view_model = _apis()
    controller = ActiveSceneController(FailingSetupFactory())
    controller.set_named_selections((_durable_node_selection(),))
    controller.set_solver_setup(_force_setup())

    controller.load_mesh(
        _mesh(),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )

    assert controller.setup_statuses["force-a"].state is api.SetupReadiness.READY


class _NativeActor:
    def __init__(self) -> None:
        self.visible = True

    def SetVisibility(self, visible: bool) -> None:
        self.visible = bool(visible)


class _NativeInteractor:
    def __init__(self) -> None:
        self.actors: list[_NativeActor] = []

    def show_axes(self) -> None:
        return None

    def add_mesh(self, _dataset: object, **_kwargs: object) -> _NativeActor:
        actor = _NativeActor()
        self.actors.append(actor)
        return actor

    def remove_actor(self, _actor: object, **_kwargs: object) -> None:
        return None

    def render(self) -> None:
        return None


class _NativePyVista:
    @staticmethod
    def PolyData(points: object) -> object:
        return points


def test_pyvista_setup_visibility_registry_survives_show_all_and_removal() -> None:
    _api, view_model = _apis()
    renderer_api = import_module("osw.gui.workspace_scene_pyvistaqt")
    interactor = _NativeInteractor()
    session = renderer_api.PyVistaQtRendererSession(
        object(),
        pyvista_module=_NativePyVista(),
        interactor_factory=lambda **_kwargs: interactor,
    )
    spec = view_model.SetupOverlaySpec(
        actor_key="setup:fixed-support:fix-a",
        record_id="fix-a",
        category="fixed_support",
        target_selection_id="nodes",
        points=((0.0, 0.0, 0.0),),
        visible=False,
    )
    session.replace_actor(spec.actor_key, spec, generation=1)

    session.show_all_actors()
    assert interactor.actors[-1].visible is True

    session.remove_actor(spec.actor_key)
    assert spec.actor_key not in session._visibility
    session.clear()
    assert set(session._visibility) == {"base_mesh", "wireframe"}
