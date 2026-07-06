"""Offscreen tests for scalar-field binding in the 3D workspace mesh viewer.

The panel exposes a scalar selector populated from the mesh's point/cell field
names; the chosen scalar flows into ``SceneViewState.render_options.color_by``
when the preview is built. All tests run headless with a recording fake scene
adapter, so no live PyVista/VTK rendering is required.
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


class RecordingSceneAdapter:
    """Fake scene adapter that records the scene state and never renders."""

    def __init__(self) -> None:
        self.load_calls: list[tuple[MeshData, SceneInputRef, SceneViewState]] = []

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
        return SceneScreenshotRecord(id=record_id, path=str(path), scene_state=scene_state)


def _mesh_with_fields() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
        point_data={"temperature": (1.0, 2.0, 3.0), "pressure": (4.0, 5.0, 6.0)},
        cell_data={"region": (7.0,)},
    )


def _mesh_no_fields() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _panel(app: object, adapter: object) -> object:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    assert app is not None
    return MeshViewerPanel(scene_adapter=adapter)


def test_set_mesh_populates_scalar_selector(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh_with_fields(), mesh_ref="m1")

    assert panel.scalar_selector.objectName() == "oswMeshViewerScalarSelector"
    items = [panel.scalar_selector.itemText(i) for i in range(panel.scalar_selector.count())]
    assert items == ["(none)", "temperature", "pressure", "region"]
    assert panel.scalar_selector.currentText() == "(none)"
    del app


def test_selecting_field_flows_color_by_into_scene_state(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    panel.set_mesh(_mesh_with_fields(), mesh_ref="m1")
    panel.scalar_selector.setCurrentText("temperature")

    panel.load_mesh_preview()

    _mesh, _scene_input, scene_state = adapter.load_calls[0]
    assert scene_state.render_options.color_by == "temperature"
    assert scene_state.scalar_field_id == "temperature"
    del app


def test_none_selection_leaves_color_by_none(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    panel.set_mesh(_mesh_with_fields(), mesh_ref="m1")
    # default selection is "(none)"

    panel.load_mesh_preview()

    _mesh, _scene_input, scene_state = adapter.load_calls[0]
    assert scene_state.render_options.color_by is None
    assert scene_state.scalar_field_id is None
    del app


def test_mesh_without_fields_shows_only_none(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh_no_fields(), mesh_ref="m1")

    items = [panel.scalar_selector.itemText(i) for i in range(panel.scalar_selector.count())]
    assert items == ["(none)"]
    del app


def test_absent_chosen_field_is_friendly(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    panel.set_mesh(_mesh_with_fields(), mesh_ref="m1")
    # A field not present on the mesh (e.g. a stale selection): must not crash.
    panel.scalar_selector.addItem("ghost")
    panel.scalar_selector.setCurrentText("ghost")

    result = panel.load_mesh_preview()

    assert result is not None  # preview still proceeds
    diagnostics = [
        panel.diagnostics_list.item(i).text()
        for i in range(panel.diagnostics_list.count())
    ]
    assert any("ghost" in d and "not present" in d for d in diagnostics)
    del app


def test_new_mesh_repopulates_selector(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh_with_fields(), mesh_ref="m1")
    panel.set_mesh(_mesh_no_fields(), mesh_ref="m2")

    items = [panel.scalar_selector.itemText(i) for i in range(panel.scalar_selector.count())]
    assert items == ["(none)"]
    del app
