"""Offscreen tests for wiring the 3D workspace mesh viewer into the main window.

All tests run headless (``QT_QPA_PLATFORM=offscreen``) and inject a recording
fake scene adapter through the MainWindow constructor, so no live PyVista/VTK
rendering is required and no screenshot file is written.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Sequence
from types import SimpleNamespace

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.scene_model import SceneInputRef, SceneScreenshotRecord, SceneViewState

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
PYSIDE6_AVAILABLE = importlib.util.find_spec("PySide6") is not None
pytestmark = pytest.mark.skipif(
    not PYSIDE6_AVAILABLE,
    reason="PySide6 optional GUI extra is not installed.",
)

if PYSIDE6_AVAILABLE:
    from PySide6 import QtWidgets
else:
    QtWidgets = None


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


class RecordingSceneAdapter:
    """Fake scene adapter that records calls and never renders or writes a file."""

    def __init__(self) -> None:
        self.load_calls: list[tuple[MeshData, SceneInputRef, SceneViewState]] = []
        self.export_calls: list[str] = []

    def load_mesh(
        self,
        mesh: MeshData,
        scene_input: SceneInputRef,
        scene_state: SceneViewState,
    ) -> object:
        self.load_calls.append((mesh, scene_input, scene_state))
        return SimpleNamespace(warnings=(), rendered=False)

    def set_view_state(self, scene_state: SceneViewState) -> None:
        return None

    def export_screenshot_record(
        self,
        path: str,
        *,
        record_id: str,
        scene_state: SceneViewState,
        mesh: MeshData,
        mesh_ref: str | None = None,
        selection_ids: Sequence[str] = (),
        caption: str | None = None,
        created_by: str | None = None,
    ) -> SceneScreenshotRecord:
        self.export_calls.append(str(path))
        return SceneScreenshotRecord(id=record_id, path=str(path), scene_state=scene_state)


class RecordingRendererSession:
    backend_kind = "fake-window"
    capabilities = frozenset({"mesh-preview", "semantic-actors"})

    def __init__(self) -> None:
        self.close_calls = 0
        self.closed = False
        self.actors: dict[str, object] = {}

    def clear(self) -> None:
        self.actors.clear()

    def replace_actor(
        self,
        semantic_id: str,
        payload: object,
        *,
        generation: int,
    ) -> object:
        self.actors[semantic_id] = (payload, generation)
        return SimpleNamespace(warnings=(), rendered=False)

    def remove_actor(self, semantic_id: str) -> None:
        self.actors.pop(semantic_id, None)

    def request_render(self) -> None:
        return None

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.close_calls += 1
        self.actors.clear()


class RecordingRendererFactory:
    backend_kind = RecordingRendererSession.backend_kind
    capabilities = RecordingRendererSession.capabilities

    def __init__(self) -> None:
        self.sessions: list[RecordingRendererSession] = []

    def create_session(self) -> RecordingRendererSession:
        session = RecordingRendererSession()
        self.sessions.append(session)
        return session


def test_main_window_exposes_mesh_viewer_action_and_dialog(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow(mesh_scene_adapter_factory=RecordingSceneAdapter)

    assert window.menu_actions["3D Mesh Preview"].objectName() == "oswActionOpenMeshViewer"

    dialog = window.open_mesh_viewer()

    assert dialog.objectName() == "oswMeshViewerDialog"
    assert window.mesh_viewer is not None
    assert window.mesh_viewer.objectName() == "oswThreeDMeshViewerPanel"
    del app


def test_open_mesh_viewer_is_idempotent(app: object) -> None:
    from osw.gui.main_window import MainWindow

    window = MainWindow(mesh_scene_adapter_factory=RecordingSceneAdapter)

    first = window.open_mesh_viewer()
    second = window.open_mesh_viewer()

    assert first is second
    assert window.mesh_viewer is not None
    del app


def test_load_mesh_into_viewer_updates_panel_and_uses_fake_adapter(app: object) -> None:
    from osw.gui.main_window import MainWindow

    adapter = RecordingSceneAdapter()
    window = MainWindow(mesh_scene_adapter_factory=lambda: adapter)

    dialog = window.load_mesh_into_viewer(_mesh(), mesh_ref="demo-mesh")

    assert dialog.objectName() == "oswMeshViewerDialog"
    panel = window.mesh_viewer
    assert panel is not None
    assert "Nodes: 3" in panel.summary_label.text()
    assert panel.current_state().mesh_ref == "demo-mesh"

    # One MainWindow load request updates the panel and active scene exactly once.
    assert window.active_scene_controller.current_mesh_ref == "demo-mesh"
    assert len(adapter.load_calls) == 1
    _mesh_arg, scene_input, _scene_state = adapter.load_calls[0]
    assert scene_input.source_kind == "mesh"
    assert scene_input.mesh_ref == "demo-mesh"
    del app


def test_main_window_document_owns_controller_used_by_mesh_panel(app: object) -> None:
    from osw.gui.main_window import MainWindow

    factory = RecordingRendererFactory()
    window = MainWindow(scene_renderer_factory=factory)
    controller = window.active_scene_controller

    window.load_mesh_into_viewer(_mesh(), mesh_ref="demo-mesh")
    assert window.mesh_viewer is not None
    assert window.mesh_viewer._adapter is controller

    window.mesh_viewer.load_mesh_preview()

    assert len(factory.sessions) == 1
    assert controller.session is factory.sessions[0]
    del app


def test_project_replacement_closes_old_scene_and_installs_new_controller(app: object) -> None:
    from osw.gui.main_window import MainWindow

    factory = RecordingRendererFactory()
    window = MainWindow(scene_renderer_factory=factory)
    old_controller = window.active_scene_controller
    window.load_mesh_into_viewer(_mesh(), mesh_ref="demo-mesh")
    assert window.mesh_viewer is not None
    window.mesh_viewer.load_mesh_preview()
    session = factory.sessions[0]

    assert window.new_project() is True

    assert session.close_calls == 1
    assert old_controller.session is None
    assert window.active_scene_controller is not old_controller
    assert window.mesh_viewer is None
    del app


def test_application_close_closes_scene_session_once(app: object) -> None:
    from osw.gui.main_window import MainWindow

    factory = RecordingRendererFactory()
    window = MainWindow(scene_renderer_factory=factory)
    window.load_mesh_into_viewer(_mesh(), mesh_ref="demo-mesh")
    assert window.mesh_viewer is not None
    window.mesh_viewer.load_mesh_preview()
    session = factory.sessions[0]

    window.close()
    assert session.close_calls == 1

    window.active_scene_controller.close()
    assert session.close_calls == 1
    del app


def test_default_none_factory_uses_panel_default_adapter(app: object) -> None:
    # No factory injected: the dialog opens with the panel's own lazy default
    # adapter and shows the friendly no-mesh state (no crash, no live render).
    from osw.gui.main_window import MainWindow

    window = MainWindow()

    dialog = window.open_mesh_viewer()

    assert dialog.objectName() == "oswMeshViewerDialog"
    assert window.mesh_viewer is not None
    assert "No mesh loaded" in window.mesh_viewer.summary_label.text()
    del app
