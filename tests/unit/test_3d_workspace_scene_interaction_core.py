"""Qt-free tests for the interactive 3D workspace scene contract."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from osw.gui.workspace_scene_controller import (
    ActiveSceneController,
    SceneLifecycleState,
    SceneRendererInitializationError,
)
from osw.gui.workspace_scene_view_model import (
    mesh_input_ref,
    scene_view_state_from_toggles,
)
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
    assert controller.show_all_actors() is True
    assert controller.enable_clipping("x", 0.25) is True
    assert controller.update_clipping("z", 0.5) is True
    assert controller.clear_clipping() is True

    assert ("set_interaction_mode", "orbit") in factory.session.calls
    assert ("fit_to_scene",) in factory.session.calls
    assert ("set_camera_preset", "front") in factory.session.calls
    assert ("set_axes_visible", False) in factory.session.calls
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

    assert controller.isolate_actor("wireframe") is True
    assert controller.actor_records["base_mesh"].visible is False
    assert controller.actor_records["wireframe"].visible is True

    assert controller.show_all_actors() is True
    assert all(record.visible for record in controller.actor_records.values())


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
        record.generation == controller.generation
        for record in controller.actor_records.values()
    )


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
    def __init__(self) -> None:
        self.visible = True

    def SetVisibility(self, visible: bool) -> None:
        self.visible = bool(visible)


class FakeDataSet:
    def __init__(self) -> None:
        self.point_data: dict[str, object] = {}
        self.clip_calls: list[dict[str, object]] = []

    def clip(self, **kwargs: object) -> FakeDataSet:
        clipped = FakeDataSet()
        clipped.clip_calls = [*self.clip_calls, dict(kwargs)]
        return clipped


class FakePyVista:
    def __init__(self) -> None:
        self.datasets: list[FakeDataSet] = []

    def PolyData(self, _points: object, _faces: object) -> FakeDataSet:
        dataset = FakeDataSet()
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
        self.render_calls = 0
        self.show_axes_calls = 0
        self.hide_axes_calls = 0
        self.clear_plane_widget_calls = 0
        self.close_calls = 0

    def set_background(self, _color: str) -> None:
        if self.fail_background:
            raise RuntimeError("forced background failure")

    def enable_trackball_style(self) -> None:
        return None

    def add_mesh(self, dataset: object, **kwargs: object) -> FakeActor:
        actor = FakeActor()
        self.add_calls.append({"dataset": dataset, "actor": actor, **kwargs})
        return actor

    def remove_actor(self, actor: object, **_kwargs: object) -> None:
        self.remove_calls.append(actor)

    def reset_camera(self) -> None:
        self.reset_calls += 1

    def view_vector(self, vector: object, viewup: object) -> None:
        self.view_calls.append((vector, viewup))

    def show_axes(self) -> None:
        self.show_axes_calls += 1

    def hide_axes(self) -> None:
        self.hide_axes_calls += 1

    def clear_plane_widgets(self) -> None:
        self.clear_plane_widget_calls += 1

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


def test_missing_pyvistaqt_is_an_explicit_controller_fallback() -> None:
    from osw.gui.workspace_scene_pyvistaqt import PyVistaQtRendererFactory

    def loader(name: str) -> object:
        if name == "pyvista":
            return FakePyVista()
        raise ModuleNotFoundError(name)

    controller = ActiveSceneController(
        PyVistaQtRendererFactory(module_loader=loader)
    )

    assert controller.attach_host(object()) is None
    assert controller.state is SceneLifecycleState.FALLBACK
    assert "PyVistaQt is not installed" in controller.fallback_reason
    assert controller.fit_to_scene() is False
