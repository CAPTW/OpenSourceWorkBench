"""Qt-free lifecycle tests for the active 3D workspace scene owner."""

from __future__ import annotations

from types import SimpleNamespace

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


class RecordingSession:
    backend_kind = "fake"
    capabilities = frozenset({"mesh-preview", "semantic-actors"})

    def __init__(self) -> None:
        self.clear_calls = 0
        self.render_calls = 0
        self.close_calls = 0
        self.active_actors: dict[str, object] = {}
        self.replacements: list[tuple[str, int]] = []
        self.closed = False

    def clear(self) -> None:
        self.clear_calls += 1
        self.active_actors.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        self.active_actors[semantic_id] = payload
        self.replacements.append((semantic_id, generation))
        return SimpleNamespace(warnings=(), rendered=False)

    def remove_actor(self, semantic_id: str) -> None:
        self.active_actors.pop(semantic_id, None)

    def request_render(self) -> None:
        self.render_calls += 1

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.close_calls += 1
        self.active_actors.clear()


class RecordingFactory:
    backend_kind = "fake"
    capabilities = RecordingSession.capabilities

    def __init__(self, session: RecordingSession | None = None) -> None:
        self.session = session or RecordingSession()
        self.create_calls = 0

    def create_session(self) -> RecordingSession:
        self.create_calls += 1
        return self.session


class FailingFactory:
    backend_kind = "fake-failure"
    capabilities = frozenset()

    def __init__(self, partial_session: RecordingSession) -> None:
        self.partial_session = partial_session

    def create_session(self) -> RecordingSession:
        raise SceneRendererInitializationError(
            "forced initialization failure",
            partial_session=self.partial_session,
        )


def _load(
    controller: ActiveSceneController,
    mesh: MeshData,
    *,
    show_edges: bool = False,
) -> object:
    return controller.load_mesh(
        mesh,
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(show_edges=show_edges),
    )


def test_one_controller_owns_exactly_one_session_and_close_is_idempotent() -> None:
    session = RecordingSession()
    factory = RecordingFactory(session)
    controller = ActiveSceneController(factory)

    assert controller.state is SceneLifecycleState.DETACHED

    _load(controller, _mesh())
    _load(controller, _mesh(x_offset=2.0))

    assert factory.create_calls == 1
    assert controller.session is session
    assert controller.backend_kind == "fake"
    assert controller.capabilities == session.capabilities

    controller.close()
    controller.close()

    assert session.close_calls == 1
    assert controller.session is None
    assert controller.state is SceneLifecycleState.CLOSED


def test_mesh_replacement_clears_old_resources_without_duplicate_actor_records() -> None:
    session = RecordingSession()
    controller = ActiveSceneController(RecordingFactory(session))

    _load(controller, _mesh(), show_edges=True)
    first_generation = controller.generation
    assert set(controller.actor_records) == {"base_mesh", "wireframe"}
    assert set(session.active_actors) == {"base_mesh", "wireframe"}

    _load(controller, _mesh(x_offset=2.0), show_edges=True)

    assert controller.generation == first_generation + 1
    assert session.clear_calls == 1
    assert set(controller.actor_records) == {"base_mesh", "wireframe"}
    assert set(session.active_actors) == {"base_mesh", "wireframe"}
    assert all(
        record.generation == controller.generation
        for record in controller.actor_records.values()
    )


def test_scene_generation_guard_rejects_callback_after_mesh_replacement() -> None:
    controller = ActiveSceneController(RecordingFactory())
    calls: list[str] = []
    _load(controller, _mesh())
    guarded = controller.guard_callback(calls.append)

    guarded("current")
    _load(controller, _mesh(x_offset=2.0))
    stale_result = guarded("stale")

    assert calls == ["current"]
    assert stale_result is None


def test_partial_initialization_failure_closes_partial_session_and_falls_back() -> None:
    partial_session = RecordingSession()
    controller = ActiveSceneController(FailingFactory(partial_session))

    result = _load(controller, _mesh())

    assert controller.state is SceneLifecycleState.FALLBACK
    assert controller.session is None
    assert controller.actor_records == {}
    assert partial_session.close_calls == 1
    assert result.rendered is False
    assert "forced initialization failure" in controller.fallback_reason


def test_clear_invalidates_callbacks_and_returns_ready_empty() -> None:
    session = RecordingSession()
    controller = ActiveSceneController(RecordingFactory(session))
    calls: list[str] = []
    _load(controller, _mesh())
    guarded = controller.guard_callback(calls.append)

    controller.clear()
    guarded("stale")

    assert calls == []
    assert controller.actor_records == {}
    assert session.active_actors == {}
    assert controller.state is SceneLifecycleState.READY_EMPTY
