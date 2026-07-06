"""Offscreen tests for ResultDataset-to-active-mesh association.

The 3D workspace may stage an already-built ResultDataset for the active mesh
when the match is exact or unambiguous. These tests use a fake scene adapter and
in-memory data only: no solver, parser, mesh generation/conversion, or live
PyVista/VTK rendering is required.
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


def _mesh(*, with_scalar: bool = False) -> MeshData:
    point_data = {"temperature": (1.0, 2.0, 3.0)} if with_scalar else {}
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
        point_data=point_data,
    )


def _result_dataset(
    dataset_id: str = "rd-1",
    *,
    mesh_ref: str | None = None,
    aligned: bool = True,
) -> ResultDataset:
    ids = (0, 1, 2) if aligned else (0, 1)
    field = ResultField(
        name="stress",
        location="node",
        components=("magnitude",),
        rows=tuple(ResultRow(item, {"magnitude": float(item) * 10.0}) for item in ids),
    )
    metadata = {"mesh_ref": mesh_ref} if mesh_ref is not None else {}
    return ResultDataset(
        dataset_id=dataset_id,
        source="fixture",
        solver="fake",
        analysis_type="static",
        fields=(field,),
        metadata=metadata,
    )


def _panel(app: object, adapter: object) -> object:
    from osw.gui.widgets.mesh_viewer_panel import MeshViewerPanel

    assert app is not None
    return MeshViewerPanel(scene_adapter=adapter)


def _selector_items(panel: object) -> list[str]:
    return [panel.scalar_selector.itemText(i) for i in range(panel.scalar_selector.count())]


def _diagnostics(panel: object) -> list[str]:
    return [panel.diagnostics_list.item(i).text() for i in range(panel.diagnostics_list.count())]


def test_no_active_mesh_does_not_associate(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())

    associated = panel.set_result_dataset_candidates((_result_dataset(),))

    assert associated is None
    assert "No active mesh" in panel.status_label.text()
    assert _selector_items(panel) == ["(none)"]
    del app


def test_no_dataset_does_not_associate(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")

    associated = panel.set_result_dataset_candidates(())

    assert associated is None
    assert "No result datasets" in panel.status_label.text()
    assert _selector_items(panel) == ["(none)"]
    del app


def test_exact_metadata_match_auto_associates_clean_dataset(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    dataset = _result_dataset(mesh_ref="mesh-1")
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")

    associated = panel.set_result_dataset_candidates((dataset,))

    assert associated is dataset
    assert "Associated result dataset 'rd-1'" in panel.status_label.text()
    assert _selector_items(panel) == ["(none)", "result: stress"]
    del app


def test_one_clean_unambiguous_candidate_is_staged(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    dataset = _result_dataset()
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")

    associated = panel.set_result_dataset_candidates((dataset,))

    assert associated is dataset
    assert "Staged result dataset 'rd-1'" in panel.status_label.text()
    assert _selector_items(panel) == ["(none)", "result: stress"]
    del app


def test_ambiguous_multiple_datasets_require_explicit_choice(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")

    associated = panel.set_result_dataset_candidates(
        (_result_dataset("rd-1"), _result_dataset("rd-2"))
    )

    assert associated is None
    assert "Multiple result datasets" in panel.status_label.text()
    assert _selector_items(panel) == ["(none)"]
    del app


def test_incompatible_dataset_does_not_clobber_mesh_field_selection(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh(with_scalar=True), mesh_ref="mesh-1")
    panel.scalar_selector.setCurrentText("temperature")

    associated = panel.set_result_dataset_candidates((_result_dataset(aligned=False),))

    assert associated is None
    assert panel.scalar_selector.currentText() == "temperature"
    assert _selector_items(panel) == ["(none)", "temperature"]
    assert any("not applied" in item for item in _diagnostics(panel))
    del app


def test_stale_metadata_match_is_friendly(app: object) -> None:
    panel = _panel(app, RecordingSceneAdapter())
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")

    associated = panel.set_result_dataset_candidates((_result_dataset(mesh_ref="mesh-2"),))

    assert associated is None
    assert "refers to mesh 'mesh-2'" in panel.status_label.text()
    assert _selector_items(panel) == ["(none)"]
    del app


def test_associated_result_field_preserves_scene_input_provenance(app: object) -> None:
    adapter = RecordingSceneAdapter()
    panel = _panel(app, adapter)
    panel.set_mesh(_mesh(), mesh_ref="mesh-1")
    panel.set_result_dataset_candidates((_result_dataset(mesh_ref="mesh-1"),))
    panel.scalar_selector.setCurrentText("result: stress")

    panel.load_mesh_preview()

    render_mesh, scene_input, scene_state = adapter.load_calls[0]
    assert render_mesh.point_data["stress"] == (0.0, 10.0, 20.0)
    assert scene_state.render_options.color_by == "stress"
    assert scene_input.mesh_ref == "mesh-1"
    assert scene_input.result_dataset_ref == "rd-1"
    assert scene_input.field_id == "stress"
    del app


def test_main_window_does_not_auto_open_but_populates_on_open(app: object) -> None:
    from osw.gui.main_window import MainWindow

    adapter = RecordingSceneAdapter()
    window = MainWindow(mesh_scene_adapter_factory=lambda: adapter)

    window._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    window.add_result_dataset(_result_dataset(mesh_ref="mesh-1"))

    assert window.mesh_viewer_dialog is None
    assert adapter.load_calls == []

    window.open_mesh_viewer()

    assert window.mesh_viewer is not None
    assert "result: stress" in _selector_items(window.mesh_viewer)
    assert adapter.load_calls == []
    del app


def test_main_window_syncs_result_dataset_when_viewer_is_open(app: object) -> None:
    from osw.gui.main_window import MainWindow

    adapter = RecordingSceneAdapter()
    window = MainWindow(mesh_scene_adapter_factory=lambda: adapter)
    window._store_imported_mesh_for_viewer(_mesh(), mesh_ref="mesh-1")
    window.open_mesh_viewer()

    window.add_result_dataset(_result_dataset(mesh_ref="mesh-1"))

    assert window.mesh_viewer is not None
    assert "result: stress" in _selector_items(window.mesh_viewer)
    assert adapter.load_calls == []
    del app
