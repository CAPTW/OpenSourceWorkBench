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

    # The injected fake adapter is wired through the panel's own preview path.
    panel.load_mesh_preview()
    assert len(adapter.load_calls) == 1
    _mesh_arg, scene_input, _scene_state = adapter.load_calls[0]
    assert scene_input.source_kind == "mesh"
    assert scene_input.mesh_ref == "demo-mesh"
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
