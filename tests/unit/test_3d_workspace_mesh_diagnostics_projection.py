"""Qt-free cache, projection, and semantic-actor contracts."""

from __future__ import annotations

from importlib import import_module
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
from osw.mesh.identity import compute_mesh_fingerprint
from osw.mesh.mesh_model import MeshCellBlock, MeshData


def _api() -> tuple[object, object]:
    quality = import_module("osw.mesh.quality")
    try:
        projection = import_module("osw.gui.mesh_diagnostics_view_model")
    except ModuleNotFoundError:
        pytest.fail("pure mesh diagnostics projection module is missing", pytrace=False)
    if not hasattr(ActiveSceneController, "analyze_mesh_quality"):
        pytest.fail("active-scene mesh diagnostics lifecycle is missing", pytrace=False)
    return quality, projection


def _mesh(*, scale: float = 4.0, rewire: bool = False) -> MeshData:
    connectivity = (0, 2, 1) if rewire else (0, 1, 2)
    return MeshData(
        points=((0.0, 0.0, 0.0), (scale, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", (connectivity,)),),
    )


class RecordingDiagnosticsSession:
    backend_kind = "fake-diagnostics"
    capabilities = frozenset(
        {
            "mesh-preview",
            "semantic-actors",
            "semantic-visibility",
            "selection-overlays",
            "setup-overlays",
            "mesh-quality-overlays",
        }
    )

    def __init__(self) -> None:
        self.actors: dict[str, object] = {
            "named_selection:keep": object(),
            "setup:force:keep": object(),
        }
        self.calls: list[tuple[object, ...]] = []
        self.close_calls = 0

    @property
    def hosted_widget(self) -> None:
        return None

    def clear(self) -> None:
        preserved = {
            key: value
            for key, value in self.actors.items()
            if key in {"named_selection:keep", "setup:force:keep"}
        }
        self.actors.clear()
        self.actors.update(preserved)
        self.calls.append(("clear",))

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        self.actors[semantic_id] = payload
        self.calls.append(("replace_actor", semantic_id, generation, payload))
        return SimpleNamespace(warnings=(), rendered=True)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)
        self.calls.append(("remove_actor", semantic_id))

    def request_render(self) -> None:
        self.calls.append(("request_render",))

    def set_representation(self, mode: str) -> None:
        self.calls.append(("set_representation", mode))

    def set_actor_visible(self, semantic_id: str, visible: bool) -> None:
        self.calls.append(("set_actor_visible", semantic_id, visible))

    def set_named_selection_overlay(
        self,
        selection_id: str,
        _kind: str,
        _indices: tuple[int, ...],
        _generation: int,
    ) -> None:
        self.actors[f"named_selection:{selection_id}"] = object()

    def remove_named_selection_overlay(self, selection_id: str) -> None:
        self.actors.pop(f"named_selection:{selection_id}", None)

    def clear_hover(self) -> None:
        return None

    def clear_current_selection(self) -> None:
        return None

    def disable_picking(self) -> None:
        return None

    def close(self) -> None:
        self.close_calls += 1
        self.actors.clear()


class RecordingDiagnosticsFactory:
    backend_kind = RecordingDiagnosticsSession.backend_kind
    capabilities = RecordingDiagnosticsSession.capabilities

    def __init__(self) -> None:
        self.session = RecordingDiagnosticsSession()

    def create_session(self) -> RecordingDiagnosticsSession:
        return self.session


def _load(controller: ActiveSceneController, mesh: MeshData | None = None) -> None:
    controller.load_mesh(
        mesh or _mesh(),
        mesh_input_ref("mesh-1"),
        scene_view_state_from_toggles(),
    )


def test_threshold_reuses_analysis_and_replaces_one_exact_semantic_actor() -> None:
    quality, projection = _api()
    calls: list[str] = []

    def analyze(mesh: MeshData, *, zero_edge_tolerance: float) -> object:
        calls.append("analyze")
        return quality.analyze_mesh_cell_quality(
            mesh,
            zero_edge_tolerance=zero_edge_tolerance,
        )

    factory = RecordingDiagnosticsFactory()
    controller = ActiveSceneController(
        factory,
        mesh_quality_analyzer=analyze,
    )
    _load(controller)

    analysis = controller.analyze_mesh_quality()
    assert analysis is controller.analyze_mesh_quality()
    assert calls == ["analyze"]

    assert controller.set_mesh_quality_threshold(2.0) is True
    assert controller.set_mesh_quality_highlight_visible(True) is True
    first = controller.mesh_quality_view_model
    assert first.bad_cell_keys == ("0:0",)
    assert first.table_bad_cell_keys == first.bad_cell_keys
    assert set(factory.session.actors) >= {
        "mesh_quality:bad_cells",
        "named_selection:keep",
        "setup:force:keep",
    }
    first_payload = factory.session.actors["mesh_quality:bad_cells"]
    assert first_payload.actor_key == "mesh_quality:bad_cells"
    assert first_payload.stable_cell_keys == first.bad_cell_keys
    assert first_payload.entity_indices == (0,)

    assert controller.set_mesh_quality_threshold(3.0) is True
    second_payload = factory.session.actors["mesh_quality:bad_cells"]
    assert second_payload is not first_payload
    assert calls == ["analyze"]
    assert list(factory.session.actors).count("mesh_quality:bad_cells") == 1

    assert controller.set_mesh_quality_threshold(10.0) is True
    assert "mesh_quality:bad_cells" not in factory.session.actors
    assert controller.mesh_quality_view_model.bad_cell_keys == ()
    assert calls == ["analyze"]
    assert projection.MESH_QUALITY_ACTOR_KEY == "mesh_quality:bad_cells"


def test_isolate_restore_clear_are_idempotent_and_preserve_unrelated_actors() -> None:
    _api()
    factory = RecordingDiagnosticsFactory()
    controller = ActiveSceneController(factory)
    _load(controller)
    controller.set_representation("wireframe")
    controller.analyze_mesh_quality()
    controller.set_mesh_quality_threshold(2.0)
    controller.set_mesh_quality_highlight_visible(True)
    before = {
        key: record.visible
        for key, record in controller.actor_records.items()
        if key in {"base_mesh", "wireframe"}
    }

    assert controller.set_mesh_quality_isolated(True) is True
    assert controller.set_mesh_quality_isolated(True) is True
    assert controller.mesh_quality_view_model.highlight_visible is True
    assert controller.mesh_quality_view_model.isolated is True
    assert controller.actor_records["base_mesh"].visible is False
    assert controller.actor_records["wireframe"].visible is False
    controller.set_mesh_quality_threshold(3.0)
    assert "named_selection:keep" in factory.session.actors
    assert "setup:force:keep" in factory.session.actors

    assert controller.restore_mesh_quality_visibility() is True
    assert controller.restore_mesh_quality_visibility() is True
    assert controller.mesh_quality_view_model.isolated is False
    assert {
        key: controller.actor_records[key].visible for key in before
    } == before

    cached = controller.mesh_quality_analysis
    assert controller.clear_mesh_quality_overlay() is True
    assert controller.mesh_quality_analysis is cached
    assert "mesh_quality:bad_cells" not in factory.session.actors
    assert "named_selection:keep" in factory.session.actors
    assert "setup:force:keep" in factory.session.actors


def test_zero_bad_or_disabling_highlight_restores_an_isolated_base_mesh() -> None:
    _api()
    factory = RecordingDiagnosticsFactory()
    controller = ActiveSceneController(factory)
    _load(controller)
    controller.analyze_mesh_quality()
    controller.set_mesh_quality_threshold(2.0)
    controller.set_mesh_quality_highlight_visible(True)
    controller.set_mesh_quality_isolated(True)

    assert controller.set_mesh_quality_threshold(10.0) is True
    assert controller.actor_records["base_mesh"].visible is True
    assert controller.mesh_quality_view_model.isolated is False
    assert "mesh_quality:bad_cells" not in factory.session.actors

    controller.set_mesh_quality_threshold(2.0)
    controller.set_mesh_quality_isolated(True)
    assert controller.set_mesh_quality_highlight_visible(False) is True
    assert controller.actor_records["base_mesh"].visible is True
    assert controller.mesh_quality_view_model.highlight_visible is False
    assert controller.mesh_quality_view_model.isolated is False


def test_mesh_replacement_invalidates_fingerprint_cache_actor_and_restoration() -> None:
    quality, _projection = _api()
    calls: list[str] = []

    def analyze(mesh: MeshData, *, zero_edge_tolerance: float) -> object:
        calls.append("analyze")
        return quality.analyze_mesh_cell_quality(
            mesh,
            zero_edge_tolerance=zero_edge_tolerance,
        )

    factory = RecordingDiagnosticsFactory()
    controller = ActiveSceneController(
        factory,
        mesh_quality_analyzer=analyze,
    )
    _load(controller)
    first = controller.analyze_mesh_quality()
    controller.set_mesh_quality_threshold(2.0)
    controller.set_mesh_quality_highlight_visible(True)
    controller.set_mesh_quality_isolated(True)

    _load(controller, _mesh(rewire=True))

    assert controller.mesh_quality_analysis is None
    assert controller.mesh_quality_view_model.analysis_available is False
    assert "mesh_quality:bad_cells" not in factory.session.actors
    second = controller.analyze_mesh_quality()
    assert first.mesh_fingerprint.digest != second.mesh_fingerprint.digest
    assert calls == ["analyze", "analyze"]

    controller.clear()
    assert controller.mesh_quality_analysis is None
    controller.close()
    controller.close()
    assert controller.state is SceneLifecycleState.CLOSED
    assert factory.session.close_calls == 1


class FailingFactory:
    backend_kind = "pyvistaqt"
    capabilities = frozenset({"mesh-preview", "semantic-actors"})

    def create_session(self) -> object:
        raise SceneRendererInitializationError("interactive backend unavailable")


def test_renderer_fallback_retains_analysis_table_but_disables_overlay_actions() -> None:
    _api()
    controller = ActiveSceneController(FailingFactory())
    _load(controller)

    analysis = controller.analyze_mesh_quality()
    view_model = controller.mesh_quality_view_model

    assert analysis.records
    assert view_model.analysis_available is True
    assert len(view_model.rows) == 1
    assert view_model.renderer_available is False
    assert view_model.overlay_actions_enabled is False
    assert "unavailable" in view_model.backend_diagnostic.lower()
    assert controller.set_mesh_quality_highlight_visible(True) is False
    assert controller.set_mesh_quality_isolated(True) is False


def test_pyvista_session_replaces_one_transient_bad_cell_collection_actor() -> None:
    quality, projection = _api()
    renderer_api = import_module("osw.gui.workspace_scene_pyvistaqt")

    class Actor:
        def __init__(self) -> None:
            self.visible = True

        def SetVisibility(self, visible: bool) -> None:
            self.visible = bool(visible)

    class DataSet:
        def __init__(self) -> None:
            self.point_data: dict[str, object] = {}
            self.cell_data: dict[str, object] = {}
            self.extracted_cells: tuple[int, ...] = ()

        def extract_cells(self, indices: object) -> object:
            extracted = DataSet()
            extracted.extracted_cells = tuple(int(index) for index in indices)
            return extracted

    class PyVista:
        def PolyData(self, _points: object, _faces: object) -> DataSet:
            return DataSet()

    class Interactor:
        def __init__(self) -> None:
            self.add_calls: list[dict[str, object]] = []
            self.removed: list[object] = []

        def set_background(self, _color: str) -> None:
            return None

        def enable_trackball_style(self) -> None:
            return None

        def show_axes(self) -> None:
            return None

        def hide_axes(self) -> None:
            return None

        def render(self) -> None:
            return None

        def add_mesh(self, dataset: object, **kwargs: object) -> Actor:
            actor = Actor()
            self.add_calls.append({"dataset": dataset, "actor": actor, **kwargs})
            return actor

        def remove_actor(self, actor: object, **_kwargs: object) -> None:
            self.removed.append(actor)

        def clear_plane_widgets(self) -> None:
            return None

        def close(self) -> None:
            return None

    mesh = _mesh()
    analysis = quality.analyze_mesh_cell_quality(mesh)
    overlay = projection.build_mesh_quality_overlay_spec(analysis, threshold=2.0)
    assert overlay is not None
    interactor = Interactor()
    session = renderer_api.PyVistaQtRendererSession(
        object(),
        pyvista_module=PyVista(),
        interactor_factory=lambda **_kwargs: interactor,
    )
    base_payload = SimpleNamespace(
        mesh=mesh,
        scene_state=scene_view_state_from_toggles(),
        mesh_fingerprint=compute_mesh_fingerprint(mesh),
    )

    session.replace_actor("base_mesh", base_payload, generation=1)
    session.replace_actor(projection.MESH_QUALITY_ACTOR_KEY, overlay, generation=1)
    first_actor = interactor.add_calls[-1]["actor"]
    session.replace_actor(projection.MESH_QUALITY_ACTOR_KEY, overlay, generation=1)

    assert set(session.semantic_actor_ids) == {
        "base_mesh",
        "mesh_quality:bad_cells",
    }
    assert interactor.removed == [first_actor]
    assert interactor.add_calls[-1]["dataset"].extracted_cells == (0,)
    assert interactor.add_calls[-1]["name"] == "osw-mesh_quality:bad_cells"

    session.remove_actor(projection.MESH_QUALITY_ACTOR_KEY)
    assert session.semantic_actor_ids == ("base_mesh",)
    session.close()
