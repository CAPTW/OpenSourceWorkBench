from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

from osw.core.result_dataset import ResultDataset
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.solvers.coolprop.model import (
    CoolPropPropertyRequest,
    CoolPropPropertyResult,
    CoolPropPropertyValue,
    PropertyInputPair,
)
from osw.solvers.coolprop.results import coolprop_result_to_result_dataset

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

FIXTURES = Path(__file__).parents[1] / "fixtures" / "results"
FIELD_FIXTURES = Path(__file__).parents[1] / "fixtures" / "fields"


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _dataset(name: str) -> ResultDataset:
    return ResultDataset.from_dict(json.loads((FIXTURES / name).read_text(encoding="utf-8")))


def test_result_viewer_displays_mesh_scene_metadata(app: object) -> None:
    from osw.gui.result_viewer import ResultViewer

    viewer = ResultViewer()
    mesh = MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 2.0, 0.0), (0.0, 0.0, 3.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
    )

    state = viewer.load_mesh_preview(mesh)

    assert viewer.objectName() == "oswResultViewer"
    assert state.mesh_info.nodes == 3
    assert "Nodes: 3" in viewer.summary_label.text()
    assert "Elements: 1" in viewer.summary_label.text()
    assert "Bounds: (0.0, 0.0, 0.0) to (1.0, 2.0, 3.0)" in viewer.summary_label.text()
    assert viewer.dataset_selector.objectName() == "oswResultDatasetSelector"

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


def test_result_viewer_displays_catalog_scalars_and_series(app: object) -> None:
    from osw.gui.result_viewer import ResultViewer
    from osw.post.result_view_model import result_catalog_from_result_datasets

    viewer = ResultViewer()
    catalog = result_catalog_from_result_datasets(
        (
            _dataset("calculix_summary_result.json"),
            _dataset("openfoam_residual_result.json"),
        )
    )

    viewer.set_result_catalog(catalog)

    assert viewer.dataset_selector.count() == 2
    assert viewer.scalar_cards.objectName() == "oswResultScalarCards"
    assert viewer.series_panel.objectName() == "oswResultSeriesPanel"
    assert viewer.table_viewer.objectName() == "oswResultTableViewer"
    assert viewer.artifacts_panel.objectName() == "oswResultArtifactsPanel"
    assert viewer.diagnostics_list.objectName() == "oswResultDiagnosticsList"
    assert viewer.catalog_summary_panel.objectName() == "oswResultCatalogSummaryPanel"
    assert viewer.handoff_panel.objectName() == "oswResultHandoffPanel"
    assert "Datasets: 2" in viewer.catalog_summary_panel.text()
    assert viewer.scalar_cards.rowCount() == 2

    viewer.dataset_selector.setCurrentIndex(1)
    assert viewer.series_panel.rowCount() >= 4
    assert "OpenFOAM" in viewer.summary_panel.text()
    assert "Shown in Plot Viewer" in viewer.handoff_panel.text()
    assert "Shown in Table Viewer" in viewer.handoff_panel.text()

    del app


def test_result_viewer_handles_missing_artifacts_and_empty_catalog(app: object) -> None:
    from osw.gui.result_viewer import ResultViewer

    viewer = ResultViewer()
    viewer.set_result_datasets([_dataset("broken_artifact_result.json")])

    diagnostics = [
        viewer.diagnostics_list.item(index).text()
        for index in range(viewer.diagnostics_list.count())
    ]
    assert any("Missing artifact" in item for item in diagnostics)

    viewer.set_result_datasets([])
    assert viewer.empty_state.objectName() == "oswResultEmptyState"
    assert not viewer.empty_state.isHidden()

    del app


def test_result_viewer_accepts_chm_dataset(app: object) -> None:
    from osw.gui.result_viewer import ResultViewer

    dataset = coolprop_result_to_result_dataset(
        CoolPropPropertyResult(
            "ok",
            CoolPropPropertyRequest(
                "Water",
                PropertyInputPair("T", 300.0, "P", 101325.0),
            ),
            values=(CoolPropPropertyValue("density", 997.0, "kg/m^3"),),
        )
    )
    viewer = ResultViewer()

    viewer.set_result_datasets([dataset])

    assert viewer.dataset_selector.count() == 1
    assert viewer.scalar_cards.rowCount() == 1
    assert "CoolProp" in viewer.summary_panel.text()
    del app


def test_result_viewer_theme_and_placeholder_do_not_require_pyvista(app: object) -> None:
    from osw.gui.result_viewer import ResultViewer
    from osw.gui.theme_tokens import get_theme_tokens

    viewer = ResultViewer()
    viewer.set_result_datasets([_dataset("openfoam_residual_result.json")])
    viewer.set_theme_tokens(get_theme_tokens("dark"))
    viewer.set_theme_tokens(get_theme_tokens("light"))
    placeholder = viewer.contour_placeholder("U")

    assert viewer.styleSheet()
    assert not placeholder.available
    assert "placeholder" in placeholder.warning.lower()
    del app


def test_result_viewer_displays_field_capable_dataset(app: object) -> None:
    from osw.gui.result_viewer import ResultViewer

    dataset = ResultDataset.from_dict(
        json.loads((FIELD_FIXTURES / "scalar_field_dataset.json").read_text(encoding="utf-8"))
    )
    viewer = ResultViewer()

    viewer.set_result_datasets([dataset])

    assert viewer.field_viewer.objectName() == "oswFieldViewerPanel"
    assert viewer.field_viewer.array_table.rowCount() == 2
    assert viewer.current_field_view_model().scalar_fields == ("temperature",)
    assert "Fields: 2" in viewer.summary_panel.text()
    assert "Shown in Field Viewer" in viewer.handoff_panel.text()
    assert "Full CalculiX FRD contour parsing" in viewer.handoff_panel.text()
    del app
