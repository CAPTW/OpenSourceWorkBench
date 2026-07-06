"""Offscreen tests for coloring the 3D mesh viewer by a ResultDataset field.

A caller-supplied ResultDataset's scalar fields appear in the viewer's scalar
selector (namespaced ``result: <name>``); selecting one maps the field onto a
MeshData overlay and colors it via the existing ``color_by`` seam. All tests run
headless with a recording fake scene adapter (no live PyVista/VTK rendering).
"""

from __future__ import annotations

import importlib.util
import os
from collections.abc import Sequence
from types import SimpleNamespace

import pytest

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
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
    def __init__(self) -> None:
        self.load_calls: list[tuple[MeshData, SceneInputRef, SceneViewState]] = []

    def load_mesh(
        self, mesh: MeshData, scene_input: SceneInputRef, scene_state: SceneViewState
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


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _result_dataset(*, aligned: bool = True) -> ResultDataset:
    ids = (0, 1, 2) if aligned else (0, 1)  # aligned -> 3 nodes; else mismatch
    stress = ResultField(
        name="stress",
        location="node",
        components=("magnitude",),
        rows=tuple(ResultRow(i, {"magnitude": float(i) * 10.0}) for i in ids),
    )
    return ResultDataset(
        dataset_id="rd-1", source="fixture", solver="fake", analysis_type="static", fields=(stress,)
    )


def _panel(app: object, adapter: object) -> object:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    assert app is not None
    return MeshViewerPanel(scene_adapter=adapter)


def test_result_fields_appear_namespaced_in_selector(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh(), mesh_ref="m1")
    panel.set_result_dataset(_result_dataset())

    items = [panel.scalar_selector.itemText(i) for i in range(panel.scalar_selector.count())]
    assert items == ["(none)", "result: stress"]
    del app


def test_selecting_result_field_colors_overlay(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    panel.set_mesh(_mesh(), mesh_ref="m1")
    panel.set_result_dataset(_result_dataset())
    panel.scalar_selector.setCurrentText("result: stress")

    panel.load_mesh_preview()

    render_mesh, scene_input, scene_state = adapter.load_calls[0]
    # The overlay carries the mapped scalar; the base mesh did not.
    assert render_mesh.point_data["stress"] == (0.0, 10.0, 20.0)
    assert scene_state.render_options.color_by == "stress"
    assert scene_input.result_dataset_ref == "rd-1"
    assert scene_input.field_id == "stress"
    del app


def test_result_field_mismatch_is_friendly(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    panel.set_mesh(_mesh(), mesh_ref="m1")
    panel.set_result_dataset(_result_dataset(aligned=False))
    panel.scalar_selector.setCurrentText("result: stress")

    result = panel.load_mesh_preview()

    assert result is not None  # preview still proceeds
    render_mesh, scene_input, scene_state = adapter.load_calls[0]
    # Not applied: no overlay array, no color_by, no result provenance.
    assert "stress" not in render_mesh.point_data
    assert scene_state.render_options.color_by is None
    assert scene_input.result_dataset_ref is None
    diagnostics = [
        panel.diagnostics_list.item(i).text() for i in range(panel.diagnostics_list.count())
    ]
    assert any("stress" in d and "not applied" in d for d in diagnostics)
    del app


def test_no_result_dataset_only_mesh_and_none(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh(), mesh_ref="m1")

    items = [panel.scalar_selector.itemText(i) for i in range(panel.scalar_selector.count())]
    assert items == ["(none)"]  # no fields on this mesh, no result dataset
    del app


def test_result_dataset_before_mesh_then_set_mesh(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_result_dataset(_result_dataset())
    panel.set_mesh(_mesh(), mesh_ref="m1")

    items = [panel.scalar_selector.itemText(i) for i in range(panel.scalar_selector.count())]
    assert items == ["(none)", "result: stress"]
    del app
