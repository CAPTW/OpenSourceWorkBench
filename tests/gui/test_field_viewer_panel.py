from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

from osw.core.result_dataset import ResultDataset

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

FIXTURES = Path(__file__).parents[1] / "fixtures" / "fields"


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def _field_dataset() -> ResultDataset:
    return ResultDataset.from_dict(
        json.loads((FIXTURES / "scalar_field_dataset.json").read_text(encoding="utf-8"))
    )


def test_field_viewer_panel_displays_field_metadata(app: object) -> None:
    from osw.gui.widgets.field_viewer_panel import FieldViewerPanel
    from osw.post.field_view_model import field_view_model_from_result_dataset

    panel = FieldViewerPanel()
    panel.set_field_view_model(field_view_model_from_result_dataset(_field_dataset()))

    assert panel.objectName() == "oswFieldViewerPanel"
    assert panel.array_table.objectName() == "oswFieldArrayTable"
    assert panel.artifact_table.objectName() == "oswFieldArtifactTable"
    assert panel.scalar_selector.objectName() == "oswFieldScalarSelector"
    assert panel.render_button.objectName() == "oswFieldRenderButton"
    assert panel.screenshot_button.objectName() == "oswFieldScreenshotButton"
    assert panel.array_table.rowCount() == 2
    assert panel.scalar_selector.count() == 1
    assert panel.empty_state.isHidden()
    del app


def test_field_viewer_panel_missing_pyvista_render_is_friendly(app: object) -> None:
    from osw.gui.widgets.field_viewer_panel import FieldViewerPanel
    from osw.post.field_view_model import field_view_model_from_result_dataset

    panel = FieldViewerPanel()
    panel.set_field_view_model(field_view_model_from_result_dataset(_field_dataset()))

    result = panel.render_preview(loader=lambda: None)

    assert result.status == "dependency_missing"
    assert "PyVista is not installed" in result.message
    assert "PyVista is not installed" in panel.render_status.text()
    del app
