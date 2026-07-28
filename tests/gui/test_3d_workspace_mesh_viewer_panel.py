"""Offscreen GUI tests for the 3D workspace mesh viewer panel.

All tests run headless (``QT_QPA_PLATFORM=offscreen``) and inject a recording
fake scene adapter, so no live PyVista/VTK rendering is required and no file is
written for a captured scene record.
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Sequence
from types import SimpleNamespace

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.pyvista_scene import PyVistaUnavailableError
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
        self.view_state_calls: list[SceneViewState] = []
        self.export_calls: list[str] = []
        self.clear_calls = 0

    def load_mesh(
        self,
        mesh: MeshData,
        scene_input: SceneInputRef,
        scene_state: SceneViewState,
    ) -> object:
        self.load_calls.append((mesh, scene_input, scene_state))
        return SimpleNamespace(warnings=(), rendered=False)

    def set_view_state(self, scene_state: SceneViewState) -> None:
        self.view_state_calls.append(scene_state)

    def clear(self) -> None:
        self.clear_calls += 1

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
        return SceneScreenshotRecord(
            id=record_id,
            path=str(path),
            scene_state=scene_state,
            mesh_ref=mesh_ref,
            selection_ids=tuple(str(item) for item in selection_ids),
            caption=caption,
            created_by=created_by,
        )


class MissingPyVistaAdapter:
    """Adapter that always reports PyVista as unavailable."""

    def load_mesh(self, mesh: object, scene_input: object, scene_state: object) -> object:
        raise PyVistaUnavailableError("PyVista is not installed.")

    def set_view_state(self, scene_state: object) -> None:
        return None

    def export_screenshot_record(self, path: object, **_kwargs: object) -> object:
        raise PyVistaUnavailableError("PyVista is not installed.")


def test_panel_object_names_and_no_mesh_state(app: object) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    panel = MeshViewerPanel(scene_adapter=RecordingSceneAdapter())

    assert panel.objectName() == "oswThreeDMeshViewerPanel"
    assert panel.summary_label.objectName() == "oswMeshViewerSummary"
    assert panel.status_label.objectName() == "oswMeshViewerStatus"
    assert panel.empty_state.objectName() == "oswMeshViewerEmptyState"
    assert panel.load_button.objectName() == "oswMeshViewerLoadButton"
    assert panel.capture_button.objectName() == "oswMeshViewerCaptureButton"
    assert panel.surface_toggle.objectName() == "surfaceToggle"
    assert panel.edge_toggle.objectName() == "edgeToggle"
    assert panel.axis_toggle.objectName() == "axisToggle"
    assert panel.grid_toggle.objectName() == "gridToggle"
    assert "No mesh loaded" in panel.summary_label.text()
    assert not panel.empty_state.isHidden()
    assert not panel.load_button.isEnabled()
    assert not panel.capture_button.isEnabled()
    del app


def test_load_mesh_preview_calls_adapter_once_and_shows_summary(app: object) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    adapter = RecordingSceneAdapter()
    panel = MeshViewerPanel(scene_adapter=adapter)
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")

    assert "Nodes: 3" in panel.summary_label.text()
    assert "Elements: 1" in panel.summary_label.text()
    assert panel.empty_state.isHidden()
    assert panel.load_button.isEnabled()

    result = panel.load_mesh_preview()

    assert len(adapter.load_calls) == 1
    assert result is not None
    assert "Mesh preview loaded" in panel.status_label.text()
    del app


def test_scene_input_carries_mesh_ref_and_toggles(app: object) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    adapter = RecordingSceneAdapter()
    panel = MeshViewerPanel(scene_adapter=adapter)
    panel.set_mesh(_mesh(), mesh_ref="mesh-42")
    panel.edge_toggle.setChecked(True)
    panel.grid_toggle.setChecked(True)
    panel.axis_toggle.setChecked(False)

    panel.load_mesh_preview()

    _mesh_arg, scene_input, scene_state = adapter.load_calls[0]
    assert scene_input.source_kind == "mesh"
    assert scene_input.mesh_ref == "mesh-42"
    assert scene_state.render_options.show_surface is True
    assert scene_state.render_options.show_edges is True
    assert scene_state.render_options.show_grid is True
    assert scene_state.render_options.show_axes is False
    del app


def test_replacing_panel_mesh_clears_existing_scene_resources(app: object) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    adapter = RecordingSceneAdapter()
    panel = MeshViewerPanel(scene_adapter=adapter)
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")
    panel.load_mesh_preview()

    panel.set_mesh(_mesh(), mesh_ref="mesh-2")

    assert adapter.clear_calls == 1
    assert panel.current_state().mesh_ref == "mesh-2"
    del app


def test_selected_selection_ids_flow_into_scene_state(app: object) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    adapter = RecordingSceneAdapter()
    panel = MeshViewerPanel(scene_adapter=adapter)
    panel.set_mesh(_mesh(), mesh_ref="m")
    panel.set_selected_selection_ids(("inlet", "outlet"))

    panel.load_mesh_preview()

    _mesh_arg, scene_input, scene_state = adapter.load_calls[0]
    assert scene_input.selection_ids == ("inlet", "outlet")
    assert scene_state.selected_selection_ids == ("inlet", "outlet")
    del app


def test_capture_scene_metadata_records_screenshot_record(app: object, tmp_path) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    adapter = RecordingSceneAdapter()
    panel = MeshViewerPanel(scene_adapter=adapter)
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")
    panel.load_mesh_preview()

    target = tmp_path / "scene.png"
    record = panel.capture_scene_metadata(target, record_id="rec-1")

    assert isinstance(record, SceneScreenshotRecord)
    assert record.id == "rec-1"
    assert record.mesh_ref == "mesh-1"
    assert panel.current_screenshot_record() is record
    assert "Captured scene metadata" in panel.status_label.text()
    assert len(adapter.export_calls) == 1
    assert not target.exists()  # the fake adapter writes no screenshot
    del app


def test_capture_without_mesh_is_friendly(app: object, tmp_path) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    panel = MeshViewerPanel(scene_adapter=RecordingSceneAdapter())

    record = panel.capture_scene_metadata(tmp_path / "scene.png")

    assert record is None
    assert "No mesh loaded" in panel.status_label.text()
    del app


def test_missing_pyvista_adapter_is_friendly(app: object) -> None:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    panel = MeshViewerPanel(scene_adapter=MissingPyVistaAdapter())
    panel.set_mesh(_mesh(), mesh_ref="m")

    result = panel.load_mesh_preview()

    assert result is None
    assert "PyVista unavailable" in panel.status_label.text()
    # The mesh summary is PyVista-free and remains visible.
    assert "Nodes: 3" in panel.summary_label.text()
    del app


def test_build_mesh_viewer_panel_factory(app: object) -> None:
    from osw.gui.widgets.mesh_viewer_panel import build_mesh_viewer_panel

    panel = build_mesh_viewer_panel(scene_adapter=RecordingSceneAdapter())

    assert panel.objectName() == "oswThreeDMeshViewerPanel"
    del app
