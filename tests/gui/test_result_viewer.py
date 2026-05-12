from __future__ import annotations

import importlib.util
import os

import pytest

from osw.mesh.mesh_model import MeshCellBlock, MeshData

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


def test_result_viewer_displays_mesh_scene_metadata(app: object) -> None:
    from osw.gui.result_viewer import ResultViewer

    viewer = ResultViewer()
    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 2.0, 0.0), (0.0, 0.0, 3.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )

    state = viewer.load_mesh_preview(mesh)

    assert viewer.objectName() == "resultViewer"
    assert state.mesh_info.nodes == 3
    assert "Nodes: 3" in viewer.summary_label.text()
    assert "Elements: 1" in viewer.summary_label.text()
    assert "Bounds: (0.0, 0.0, 0.0) to (1.0, 2.0, 3.0)" in viewer.summary_label.text()

    del app


def test_result_viewer_exposes_visualization_toggles(app: object) -> None:
    from osw.gui.result_viewer import ResultViewer

    viewer = ResultViewer()

    assert viewer.surface_toggle.objectName() == "surfaceToggle"
    assert viewer.edge_toggle.objectName() == "edgeToggle"
    assert viewer.axis_toggle.objectName() == "axisToggle"
    assert viewer.grid_toggle.objectName() == "gridToggle"
    assert viewer.scalar_field_placeholder.objectName() == "scalarFieldPlaceholder"

    del app
