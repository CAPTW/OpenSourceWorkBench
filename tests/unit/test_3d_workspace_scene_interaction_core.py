"""Qt-free tests for the interactive 3D workspace scene contract."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from osw.core.selection_resolution import NODE_ORDINAL_NAMESPACE
from osw.gui.workspace_scene_controller import (
    ActiveSceneController,
    SceneLifecycleState,
    SceneRendererInitializationError,
)
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _mesh(*, x_offset: float = 0.0) -> MeshData:
    return MeshData(
        points=(
            (x_offset, 0.0, 0.0),
            (x_offset + 1.0, 0.0, 0.0),
            (x_offset, 1.0, 0.0),
        ),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


class RecordingInteractiveSession:
    backend_kind = "fake-interactive"
    capabilities = frozenset(
        {
            "interactive",
            "hosted-widget",
            "camera",
            "representation",
            "semantic-visibility",
            "axes",
            "clipping",
        }
    )

    def __init__(self) -> None:
        self.widget = object()
        self.actors: dict[str, object] = {}
        self.calls: list[tuple[object, ...]] = []
        self.close_calls = 0
        self.closed = False

    @property
    def hosted_widget(self) -> object:
        return self.widget

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
        self.calls.append(("replace_actor", semantic_id, generation))
        return SimpleNamespace(warnings=(), rendered=True)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)

    def request_render(self) -> None:
        self.calls.append(("request_render",))

    def fit_to_scene(self) -> None:
        self.calls.append(("fit_to_scene",))

    def set_camera_preset(self, preset: str) -> None:
        self.calls.append(("set_camera_preset", preset))

    def set_interaction_mode(self, mode: str) -> None:
        self.calls.append(("set_interaction_mode", mode))

    def set_axes_visible(self, visible: bool) -> None:
        self.calls.append(("set_axes_visible", visible))

    def set_representation(self, mode: str) -> None:
        self.calls.append(("set_representation", mode))

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.calls.append(("set_actor_visible", semantic_id, visible))

    def isolate_actor(self, semantic_id: str) -> None:
        self.calls.append(("isolate_actor", semantic_id))

    def clear_isolation(self) -> None:
        self.calls.append(("clear_isolation",))

    def show_all_actors(self) -> None:
        self.calls.append(("show_all_actors",))

    def enable_clipping(self, axis: str, origin: float) -> None:
        self.calls.append(("enable_clipping", axis, origin))

    def update_clipping(self, axis: str, origin: float) -> None:
        self.calls.append(("update_clipping", axis, origin))

    def clear_clipping(self) -> None:
        self.calls.append(("clear_clipping",))

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.close_calls += 1
        self.actors.clear()


class RecordingInteractiveFactory:
    backend_kind = RecordingInteractiveSession.backend_kind
    capabilities = RecordingInteractiveSession.capabilities

    def __init__(self) -> None:
        self.host_parent: object | None = None
        self.session = RecordingInteractiveSession()
        self.create_calls = 0

    def set_host_parent(self, parent: object) -> None:
        self.host_parent = parent

    def create_session(self) -> RecordingInteractiveSession:
        self.create_calls += 1
        return self.session


def _load(controller: ActiveSceneController, mesh: MeshData | None = None) -> object:
    return controller.load_mesh(
        mesh or _mesh(),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )


def test_controller_hosts_one_interactive_session_and_routes_commands() -> None:
    factory = RecordingInteractiveFactory()
    controller = ActiveSceneController(factory)
    parent = object()

    assert controller.attach_host(parent) is factory.session.widget
    assert factory.host_parent is parent
    assert factory.create_calls == 1

    _load(controller)
    assert set(controller.actor_records) == {"base_mesh", "wireframe"}
    assert controller.set_interaction_mode("orbit") is True
    assert controller.fit_to_scene() is True
    assert controller.set_camera_preset("front") is True
    assert controller.set_axes_visible(False) is True
    assert controller.set_representation("wireframe") is True
    assert controller.set_actor_visible("wireframe", False) is True
    assert controller.isolate_actor("base_mesh") is True
    assert controller.clear_isolation() is True
    assert controller.show_all_actors() is True
    assert controller.enable_clipping("x", 0.25) is True
    assert controller.update_clipping("z", 0.5) is True
    assert controller.clear_clipping() is True

    assert ("set_interaction_mode", "orbit") in factory.session.calls
    assert ("fit_to_scene",) in factory.session.calls
    assert ("set_camera_preset", "front") in factory.session.calls
    assert ("set_axes_visible", False) in factory.session.calls
    assert ("clear_isolation",) in factory.session.calls
    assert ("enable_clipping", "x", 0.25) in factory.session.calls
    assert ("update_clipping", "z", 0.5) in factory.session.calls
    assert ("clear_clipping",) in factory.session.calls


def test_representation_visibility_is_deterministic_in_registry() -> None:
    controller = ActiveSceneController(RecordingInteractiveFactory())
    controller.attach_host(object())
    _load(controller)

    assert controller.set_representation("surface") is True
    assert controller.actor_records["base_mesh"].visible is True
    assert controller.actor_records["wireframe"].visible is False

    assert controller.set_representation("wireframe") is True
    assert controller.actor_records["base_mesh"].visible is False
    assert controller.actor_records["wireframe"].visible is True

    assert controller.set_representation("surface_with_edges") is True
    assert controller.actor_records["base_mesh"].visible is True
    assert controller.actor_records["wireframe"].visible is True

    records = controller.actor_records
    assert records["base_mesh"].category == "geometry"
    assert records["base_mesh"].pickable is True
    assert records["base_mesh"].isolation_eligible is True
    assert records["base_mesh"].is_helper is False
    with pytest.raises(TypeError):
        records["new"] = records["base_mesh"]  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        records["base_mesh"].visible = False  # type: ignore[misc]

    assert controller.set_representation("surface") is True
    assert controller.isolate_actor("base_mesh") is True
    assert controller.isolate_actor("wireframe") is True
    assert controller.actor_records["base_mesh"].visible is False
    assert controller.actor_records["wireframe"].visible is True

    assert controller.clear_isolation() is True
    assert controller.actor_records["base_mesh"].visible is True
    assert controller.actor_records["wireframe"].visible is False
    assert controller.clear_isolation() is True

    assert controller.hide_actor("base_mesh") is True
    assert controller.actor_records["base_mesh"].visible is False
    assert controller.show_actor("base_mesh") is True
    assert controller.actor_records["base_mesh"].visible is True
    assert controller.isolate_actor("missing") is False

    assert controller.show_all_actors() is True
    assert all(
        record.visible for record in controller.actor_records.values() if record.isolation_eligible
    )


def test_replacement_does_not_create_a_second_session_or_duplicate_actors() -> None:
    factory = RecordingInteractiveFactory()
    controller = ActiveSceneController(factory)
    controller.attach_host(object())

    _load(controller)
    _load(controller, _mesh(x_offset=2.0))

    assert factory.create_calls == 1
    assert set(factory.session.actors) == {"base_mesh", "wireframe"}
    assert set(controller.actor_records) == {"base_mesh", "wireframe"}
    assert all(
        record.generation == controller.generation for record in controller.actor_records.values()
    )


def test_scene_clear_preserves_axes_preference_and_close_disables_state() -> None:
    controller = ActiveSceneController(RecordingInteractiveFactory())
    controller.attach_host(object())
    _load(controller)

    assert controller.set_axes_visible(False) is True
    controller.clear()
    assert controller.axes_visible is False
    assert controller.actor_records == {}

    controller.close()
    assert controller.axes_visible is False


def test_selection_highlight_registry_clears_on_hide_isolate_and_replacement() -> None:
    class SelectionSession(RecordingInteractiveSession):
        capabilities = RecordingInteractiveSession.capabilities | frozenset(
            {"picking", "selection-overlays"}
        )

        def set_pick_mode(self, mode: str, callback: object) -> None:
            self.calls.append(("set_pick_mode", mode, callback))

        def set_current_selection(
            self,
            entity_kind: str,
            indices: tuple[int, ...],
            generation: int,
        ) -> None:
            self.actors["current_selection"] = (entity_kind, indices, generation)

        def clear_current_selection(self) -> None:
            self.actors.pop("current_selection", None)

        def clear_hover(self) -> None:
            self.actors.pop("hover", None)

    class SelectionFactory(RecordingInteractiveFactory):
        capabilities = SelectionSession.capabilities

        def __init__(self) -> None:
            self.host_parent = None
            self.session = SelectionSession()
            self.create_calls = 0

    factory = SelectionFactory()
    controller = ActiveSceneController(factory)
    controller.attach_host(object())
    _load(controller)
    assert controller.set_pick_mode("node") is True
    fingerprint = controller.current_mesh_fingerprint
    assert fingerprint is not None

    event = {
        "generation": controller.generation,
        "mesh_ref": "mesh-1",
        "mesh_fingerprint": fingerprint.digest,
        "entity_kind": "node",
        "backend_index": 1,
        "intent": "replace",
    }
    assert controller.handle_pick(event) is True
    selection = controller.actor_records["current_selection"]
    assert selection.category == "selection"
    assert selection.is_helper is True
    assert selection.isolation_eligible is False
    assert controller.hide_actor("current_selection") is False
    assert controller.fallback_reason == ""

    assert controller.hide_actor("base_mesh") is True
    assert controller.current_selection_target is None
    assert "current_selection" not in controller.actor_records
    assert "current_selection" not in factory.session.actors

    assert controller.show_actor("base_mesh") is True
    assert controller.handle_pick(event) is True
    assert controller.isolate_actor("wireframe") is True
    assert "current_selection" not in controller.actor_records

    _load(controller, _mesh(x_offset=4.0))
    assert "current_selection" not in controller.actor_records
    assert set(factory.session.actors) == {"base_mesh", "wireframe"}


def test_interaction_commands_fail_safely_without_capability_or_after_close() -> None:
    class NonInteractiveFactory(RecordingInteractiveFactory):
        capabilities = frozenset({"mesh-preview"})

        def __init__(self) -> None:
            super().__init__()
            self.session.capabilities = self.capabilities

    controller = ActiveSceneController(NonInteractiveFactory())
    controller.attach_host(object())

    assert controller.fit_to_scene() is False
    assert controller.set_camera_preset("front") is False
    assert controller.enable_clipping("x", 0.0) is False

    controller.close()
    assert controller.fit_to_scene() is False
    assert controller.set_representation("surface") is False


class FakeActor:
    def __init__(self, bounds: tuple[float, ...] | None = None) -> None:
        self.visible = True
        self.bounds = bounds

    def SetVisibility(self, visible: bool) -> None:
        self.visible = bool(visible)

    def GetBounds(self) -> tuple[float, ...] | None:
        return self.bounds


class FakeDataSet:
    def __init__(self, points: object = ()) -> None:
        self.point_data: dict[str, object] = {}
        self.cell_data: dict[str, object] = {}
        self.clip_calls: list[dict[str, object]] = []
        self.extracted_points: tuple[int, ...] = ()
        self.extracted_cells: tuple[int, ...] = ()
        normalized = tuple(tuple(float(value) for value in point) for point in points)
        self.bounds = (
            (
                min(point[0] for point in normalized),
                max(point[0] for point in normalized),
                min(point[1] for point in normalized),
                max(point[1] for point in normalized),
                min(point[2] for point in normalized),
                max(point[2] for point in normalized),
            )
            if normalized
            else None
        )

    def clip(self, **kwargs: object) -> FakeDataSet:
        clipped = FakeDataSet()
        clipped.clip_calls = [*self.clip_calls, dict(kwargs)]
        return clipped

    def extract_points(
        self,
        indices: object,
        **_kwargs: object,
    ) -> FakeDataSet:
        extracted = FakeDataSet()
        extracted.extracted_points = tuple(int(item) for item in indices)
        return extracted

    def extract_cells(self, indices: object) -> FakeDataSet:
        extracted = FakeDataSet()
        extracted.extracted_cells = tuple(int(item) for item in indices)
        return extracted


class FakePyVista:
    def __init__(self) -> None:
        self.datasets: list[FakeDataSet] = []

    def PolyData(self, _points: object, _faces: object = None) -> FakeDataSet:
        del _faces
        dataset = FakeDataSet(_points)
        self.datasets.append(dataset)
        return dataset


class FakeTimer:
    def __init__(self) -> None:
        self.stop_calls = 0

    def stop(self) -> None:
        self.stop_calls += 1


class FakeInteractor:
    def __init__(self, *, fail_background: bool = False) -> None:
        self.fail_background = fail_background
        self.render_timer = FakeTimer()
        self.add_calls: list[dict[str, object]] = []
        self.remove_calls: list[object] = []
        self.view_calls: list[tuple[object, object]] = []
        self.reset_calls = 0
        self.reset_bounds: list[tuple[float, ...] | None] = []
        self.render_calls = 0
        self.show_axes_calls = 0
        self.hide_axes_calls = 0
        self.clear_plane_widget_calls = 0
        self.close_calls = 0
        self.point_pick_kwargs: dict[str, object] = {}
        self.cell_pick_kwargs: dict[str, object] = {}
        self.disable_picking_calls = 0

    def set_background(self, _color: str) -> None:
        if self.fail_background:
            raise RuntimeError("forced background failure")

    def enable_trackball_style(self) -> None:
        return None

    def add_mesh(self, dataset: object, **kwargs: object) -> FakeActor:
        actor = FakeActor(getattr(dataset, "bounds", None))
        self.add_calls.append({"dataset": dataset, "actor": actor, **kwargs})
        return actor

    def remove_actor(self, actor: object, **_kwargs: object) -> None:
        self.remove_calls.append(actor)

    def reset_camera(
        self,
        *,
        bounds: tuple[float, ...] | None = None,
        render: bool = True,
    ) -> None:
        del render
        self.reset_calls += 1
        self.reset_bounds.append(bounds)

    def view_vector(
        self,
        vector: object,
        viewup: object,
        **kwargs: object,
    ) -> None:
        self.reset_bounds.append(kwargs.get("bounds"))
        self.view_calls.append((vector, viewup))

    def show_axes(self) -> None:
        self.show_axes_calls += 1

    def hide_axes(self) -> None:
        self.hide_axes_calls += 1

    def clear_plane_widgets(self) -> None:
        self.clear_plane_widget_calls += 1

    def enable_point_picking(self, **kwargs: object) -> None:
        self.point_pick_kwargs = dict(kwargs)

    def enable_cell_picking(self, **kwargs: object) -> None:
        self.cell_pick_kwargs = dict(kwargs)

    def disable_picking(self) -> None:
        self.disable_picking_calls += 1

    def render(self) -> None:
        self.render_calls += 1

    def close(self) -> None:
        self.close_calls += 1


def test_pyvistaqt_session_keeps_native_handles_private_and_tears_down() -> None:
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession

    fake_pyvista = FakePyVista()
    interactor = FakeInteractor()
    session = PyVistaQtRendererSession(
        object(),
        pyvista_module=fake_pyvista,
        interactor_factory=lambda **_kwargs: interactor,
    )
    payload = SimpleNamespace(
        mesh=_mesh(),
        scene_state=scene_view_state_from_toggles(),
    )

    session.replace_actor("base_mesh", payload, generation=1)
    session.replace_actor("wireframe", payload, generation=1)
    assert session.native_actor_registry["base_mesh"] is session._actors["base_mesh"]
    with pytest.raises(TypeError):
        session.native_actor_registry["extra"] = FakeActor()  # type: ignore[index]
    assert session.fit_to_scene() is True
    assert interactor.reset_bounds[-1] == (0.0, 1.0, 0.0, 1.0, 0.0, 0.0)
    session.set_representation("wireframe")
    session.set_camera_preset("isometric")
    session.enable_clipping("x", 0.25)

    assert set(session.semantic_actor_ids) == {"base_mesh", "wireframe"}
    assert len(interactor.add_calls) == 4
    assert interactor.view_calls[-1] == ((1.0, 1.0, 1.0), (0.0, 0.0, 1.0))
    assert any(
        call["dataset"].clip_calls[-1]["normal"] == (1.0, 0.0, 0.0)
        for call in interactor.add_calls[2:]
    )

    session.close()
    session.close()

    assert interactor.render_timer.stop_calls == 1
    assert interactor.clear_plane_widget_calls == 1
    assert interactor.close_calls == 1
    assert session.hosted_widget is None
    assert session.semantic_actor_ids == ()


def test_pyvistaqt_camera_axes_representation_and_isolation_contract() -> None:
    from osw.gui.setup_overlay_view_model import SetupOverlaySpec
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession

    interactor = FakeInteractor()
    session = PyVistaQtRendererSession(
        object(),
        pyvista_module=FakePyVista(),
        interactor_factory=lambda **_kwargs: interactor,
    )
    payload = SimpleNamespace(
        mesh=_mesh(),
        scene_state=scene_view_state_from_toggles(show_edges=True),
    )
    assert session.fit_to_scene() is False
    session.replace_actor("base_mesh", payload, generation=1)
    session.replace_actor("wireframe", payload, generation=1)
    session._actors["current_selection"] = FakeActor((-100.0, 100.0, -100.0, 100.0, -100.0, 100.0))
    assert session.fit_to_scene() is True
    assert interactor.reset_bounds[-1] == (0.0, 1.0, 0.0, 1.0, 0.0, 0.0)

    expected = {
        "front": ((0.0, -1.0, 0.0), (0.0, 0.0, 1.0)),
        "back": ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        "left": ((-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "right": ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0)),
        "top": ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
        "bottom": ((0.0, 0.0, -1.0), (0.0, -1.0, 0.0)),
        "isometric": ((1.0, 1.0, 1.0), (0.0, 0.0, 1.0)),
    }
    for preset, camera_call in expected.items():
        assert session.set_camera_preset(preset) is True
        assert interactor.view_calls[-1] == camera_call
        assert interactor.reset_bounds[-1] == (
            0.0,
            1.0,
            0.0,
            1.0,
            0.0,
            0.0,
        )
    camera_call_count = len(interactor.view_calls)

    axes_show_calls = interactor.show_axes_calls
    session.set_axes_visible(True)
    assert interactor.show_axes_calls == axes_show_calls
    session.set_axes_visible(False)
    session.set_axes_visible(False)
    assert interactor.hide_axes_calls == 1
    session.set_axes_visible(True)
    assert interactor.show_axes_calls == axes_show_calls + 1

    session.set_representation("surface")
    assert session.isolate_actor("base_mesh") is True
    assert session.isolate_actor("wireframe") is True
    assert interactor.add_calls[0]["actor"].visible is False
    assert interactor.add_calls[1]["actor"].visible is True
    assert session.clear_isolation() is True
    assert interactor.add_calls[0]["actor"].visible is True
    assert interactor.add_calls[1]["actor"].visible is False
    assert session.clear_isolation() is True

    assert session.isolate_actor("base_mesh") is True
    session.replace_actor(
        "setup:fixed-support:fixture",
        SetupOverlaySpec(
            actor_key="setup:fixed-support:fixture",
            record_id="fixture",
            category="fixed_support",
            target_selection_id="nodes",
            points=((0.0, 0.0, 0.0),),
            visible=True,
        ),
        generation=1,
    )
    assert session._isolation_snapshot is None
    assert interactor.add_calls[0]["actor"].visible is True
    assert interactor.add_calls[1]["actor"].visible is False

    session.show_all_actors()
    assert interactor.add_calls[0]["actor"].visible is True
    assert interactor.add_calls[1]["actor"].visible is True
    assert len(interactor.view_calls) == camera_call_count
    session.close()
    assert session.axes_visible is False


def test_pyvistaqt_partial_initialization_failure_closes_created_interactor() -> None:
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession

    interactor = FakeInteractor(fail_background=True)

    with pytest.raises(
        SceneRendererInitializationError,
        match="interactive session initialization failed",
    ):
        PyVistaQtRendererSession(
            object(),
            pyvista_module=FakePyVista(),
            interactor_factory=lambda **_kwargs: interactor,
        )

    assert interactor.render_timer.stop_calls == 1
    assert interactor.clear_plane_widget_calls == 1
    assert interactor.close_calls == 1


def test_pyvistaqt_picking_and_semantic_selection_overlays_are_session_local() -> None:
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererSession

    controller = ActiveSceneController(RecordingInteractiveFactory())
    controller.attach_host(object())
    _load(controller)
    controller.set_pick_mode("node")

    fake_pyvista = FakePyVista()
    interactor = FakeInteractor()
    session = PyVistaQtRendererSession(
        object(),
        pyvista_module=fake_pyvista,
        interactor_factory=lambda **_kwargs: interactor,
    )
    mesh = _mesh()
    payload = SimpleNamespace(
        mesh=mesh,
        scene_input=mesh_input_ref("mesh-1"),
        scene_state=scene_view_state_from_toggles(),
        mesh_fingerprint=compute_mesh_fingerprint(mesh),
    )
    events: list[dict[str, object]] = []
    notifications: list[object] = []
    controller.set_selection_listener(
        lambda: notifications.append(controller.current_selection_target)
    )

    session_generation = controller.generation
    session.replace_actor("base_mesh", payload, generation=session_generation)
    session.replace_actor("wireframe", payload, generation=session_generation)
    session.set_pick_mode(
        "node",
        controller.guard_callback(controller.handle_pick, stale_result=False),
    )
    point_callback = interactor.point_pick_kwargs["callback"]
    assert callable(point_callback)
    picked_point = (91.25, 92.5, 93.75)
    point_callback(picked_point, SimpleNamespace(GetPointId=lambda: 2))

    target = controller.current_selection_target
    assert target is not None
    assert target.kind.value == "node"
    assert target.ids == (2,)
    assert target.locator is not None
    assert target.locator.id_namespace == NODE_ORDINAL_NAMESPACE
    assert target.locator.entity_ids == (2,)
    assert target.locator.mesh_ref == "mesh-1"
    assert target.locator.mesh_fingerprint == payload.mesh_fingerprint.digest
    assert notifications == [target]
    assert events == []

    controller.clear_current_selection()
    notifications.clear()
    point_callback(
        (81.25, 82.5, 83.75),
        SimpleNamespace(GetPointId=lambda: -1),
    )
    assert controller.current_selection_target is None
    assert notifications == []

    _load(controller, _mesh(x_offset=4.0))
    notifications.clear()
    point_callback(
        (71.25, 72.5, 73.75),
        SimpleNamespace(GetPointId=lambda: 1),
    )
    assert controller.current_selection_target is None
    assert notifications == []

    session.set_hover_entities("node", (0,), session_generation)
    session.set_current_selection("node", (0, 2), session_generation)
    first_selection_actor = session._actors["current_selection"]
    session.set_current_selection("cell", (0,), session_generation)
    assert session._actors["current_selection"] is not first_selection_actor
    assert interactor.remove_calls.count(first_selection_actor) == 1
    session.set_named_selection_overlay(
        "selection-1",
        "cell",
        (0,),
        session_generation,
    )
    assert {
        "hover",
        "current_selection",
        "named_selection:selection-1",
    }.issubset(set(session.semantic_actor_ids))

    session.set_actor_visible("base_mesh", False)
    assert "hover" not in session.semantic_actor_ids
    assert "current_selection" not in session.semantic_actor_ids
    session.set_actor_visible("base_mesh", True)
    session.set_current_selection("node", (0,), session_generation)

    session.set_pick_mode("cell", events.append)
    cell_callback = interactor.cell_pick_kwargs["callback"]
    assert callable(cell_callback)
    picked_cells = FakeDataSet()
    picked_cells.cell_data["_osw_transient_cell_index"] = (0,)
    cell_callback(picked_cells)
    assert len(events) == 1
    assert events[0]["entity_kind"] == "cell"
    assert events[0]["backend_index"] == 0
    assert notifications == []

    session.clear_selection_highlights()
    session.remove_named_selection_overlay("selection-1")
    assert set(session.semantic_actor_ids) == {"base_mesh", "wireframe"}
    session.close()
    controller.close()
    assert interactor.disable_picking_calls >= 1


def test_missing_pyvistaqt_is_an_explicit_controller_fallback() -> None:
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererFactory

    def loader(name: str) -> object:
        if name == "pyvista":
            return FakePyVista()
        raise ModuleNotFoundError(name)

    controller = ActiveSceneController(PyVistaQtRendererFactory(module_loader=loader))

    assert controller.attach_host(object()) is None
    assert controller.state is SceneLifecycleState.FALLBACK
    assert "PyVistaQt is not installed" in controller.fallback_reason
    assert controller.fit_to_scene() is False
