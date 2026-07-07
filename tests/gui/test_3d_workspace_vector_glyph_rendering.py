"""Offscreen tests for preview-only vector glyph state in the mesh viewer.

These tests inject a fake scene adapter and use already-built ResultDataset
rows. They do not require live PyVista/VTK rendering, solver execution, parser
execution, mesh generation, mesh conversion, project auto-save, or result
binding metadata mutation.
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


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _mesh_with_vector_overlay() -> MeshData:
    return MeshData(
        points=_mesh().points,
        cells=_mesh().cells,
        point_data={
            "temperature": (10.0, 20.0, 30.0),
            "result_vector:U": ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        },
    )


def _vector_dataset(*, aligned: bool = True) -> ResultDataset:
    ids = (0, 1, 2) if aligned else (0, 1)
    vector = ResultField(
        name="U",
        location="node",
        components=("Ux", "Uy", "Uz"),
        rows=tuple(
            ResultRow(i, {"Ux": float(i), "Uy": float(i) + 1.0, "Uz": float(i) + 2.0})
            for i in ids
        ),
    )
    return ResultDataset(
        dataset_id="rd-vector",
        source="fixture",
        solver="fake",
        analysis_type="static",
        fields=(vector,),
    )


def _mixed_dataset() -> ResultDataset:
    scalar = ResultField(
        name="stress",
        location="node",
        components=("magnitude",),
        rows=tuple(ResultRow(i, {"magnitude": float(i) * 10.0}) for i in (0, 1, 2)),
    )
    return ResultDataset(
        dataset_id="rd-mixed",
        source="fixture",
        solver="fake",
        analysis_type="static",
        fields=(scalar, *_vector_dataset().fields),
    )


def _panel(app: object, adapter: RecordingSceneAdapter) -> object:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    assert app is not None
    return MeshViewerPanel(scene_adapter=adapter)


def _selector_items(selector: object) -> list[str]:
    return [selector.itemText(index) for index in range(selector.count())]


def _diagnostics(panel: object) -> list[str]:
    return [panel.diagnostics_list.item(i).text() for i in range(panel.diagnostics_list.count())]


def test_vector_result_field_selector_lists_compatible_fields(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")
    panel.set_result_dataset(_vector_dataset())

    assert _selector_items(panel.vector_selector) == ["(none)", "result vector: U"]
    assert panel.vector_selector.isEnabled()
    del app


def test_glyph_state_is_sent_to_fake_adapter_from_result_vector_field(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    base_mesh = _mesh()
    dataset = _vector_dataset()
    before_dataset = dataset.to_dict()
    panel.set_mesh(base_mesh, mesh_ref="mesh-1")
    panel.set_result_dataset(dataset)
    panel.vector_selector.setCurrentText("result vector: U")
    panel.glyph_toggle.setChecked(True)
    panel.glyph_scale_input.setValue(2.5)
    panel.glyph_max_count_input.setValue(50)

    panel.load_mesh_preview()

    render_mesh, _scene_input, scene_state = adapter.load_calls[0]
    assert render_mesh.point_data["result_vector:U"] == (
        (0.0, 1.0, 2.0),
        (1.0, 2.0, 3.0),
        (2.0, 3.0, 4.0),
    )
    assert scene_state.glyph_options.enabled is True
    assert scene_state.glyph_options.vector_field == "result_vector:U"
    assert scene_state.glyph_options.scale == 2.5
    assert scene_state.glyph_options.max_glyph_count == 50
    assert "result_vector:U" not in base_mesh.point_data
    assert dataset.to_dict() == before_dataset
    del app


def test_scalar_coloring_still_works_with_glyph_controls(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")
    panel.set_result_dataset(_mixed_dataset())
    panel.scalar_selector.setCurrentText("result: stress")
    panel.vector_selector.setCurrentText("result vector: U")
    panel.glyph_toggle.setChecked(True)

    panel.load_mesh_preview()

    render_mesh, scene_input, scene_state = adapter.load_calls[0]
    assert render_mesh.point_data["stress"] == (0.0, 10.0, 20.0)
    assert render_mesh.point_data["result_vector:U"] == (
        (0.0, 1.0, 2.0),
        (1.0, 2.0, 3.0),
        (2.0, 3.0, 4.0),
    )
    assert scene_state.render_options.color_by == "stress"
    assert scene_state.glyph_options.vector_field == "result_vector:U"
    assert scene_input.result_dataset_ref == "rd-mixed"
    assert scene_input.field_id == "stress"
    del app


def test_no_compatible_vector_fields_disables_glyph_controls(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")
    panel.set_result_dataset(
        ResultDataset(
            dataset_id="rd-scalar",
            source="fixture",
            solver="fake",
            analysis_type="static",
            fields=(
                ResultField(
                    name="stress",
                    location="node",
                    components=("magnitude",),
                    rows=tuple(
                        ResultRow(i, {"magnitude": float(i)}) for i in (0, 1, 2)
                    ),
                ),
            ),
        )
    )

    assert _selector_items(panel.vector_selector) == ["(none)"]
    assert not panel.vector_selector.isEnabled()
    assert not panel.glyph_toggle.isEnabled()

    panel.load_mesh_preview()

    _render_mesh, _scene_input, scene_state = adapter.load_calls[0]
    assert scene_state.glyph_options.enabled is False
    del app


def test_vector_mapping_failure_is_friendly_and_does_not_mutate_mesh(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    base_mesh = _mesh()
    panel.set_mesh(base_mesh, mesh_ref="mesh-1")
    panel.set_result_dataset(_vector_dataset(aligned=False))
    panel.vector_selector.addItem("result vector: U")
    panel.vector_selector.setCurrentText("result vector: U")
    panel.glyph_toggle.setChecked(True)

    panel.load_mesh_preview()

    render_mesh, _scene_input, scene_state = adapter.load_calls[0]
    assert render_mesh is base_mesh
    assert scene_state.glyph_options.enabled is False
    assert "result_vector:U" not in base_mesh.point_data
    assert any("vector overlay not applied" in item for item in _diagnostics(panel))
    del app


def test_existing_mesh_vector_overlay_can_drive_glyphs(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    mesh = _mesh_with_vector_overlay()
    panel.set_mesh(mesh, mesh_ref="mesh-1")

    assert _selector_items(panel.scalar_selector) == ["(none)", "temperature"]
    assert _selector_items(panel.vector_selector) == ["(none)", "result_vector:U"]

    panel.vector_selector.setCurrentText("result_vector:U")
    panel.glyph_toggle.setChecked(True)
    panel.load_mesh_preview()

    render_mesh, _scene_input, scene_state = adapter.load_calls[0]
    assert render_mesh is mesh
    assert scene_state.glyph_options.enabled is True
    assert scene_state.glyph_options.vector_field == "result_vector:U"
    del app
