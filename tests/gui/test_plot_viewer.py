from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

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

FIXTURES = Path(__file__).parents[1] / "fixtures" / "figures"


@pytest.fixture
def app() -> object:
    assert QtWidgets is not None
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


def test_plot_viewer_displays_figure_dataset(app: object) -> None:
    from osw.gui.plot_viewer import PlotViewer
    from osw.scripts.mscript.figure_capture import figure_dataset_from_artifacts

    dataset = figure_dataset_from_artifacts(
        (
            FIXTURES / "simple_plot.png",
            FIXTURES / "simple_plot.svg",
            FIXTURES / "table_data.csv",
        ),
        dataset_id="gui-figures",
    )
    viewer = PlotViewer()
    viewer.set_figure_dataset(dataset)

    assert viewer.objectName() == "oswPlotViewer"
    assert viewer.figure_list.objectName() == "oswFigureList"
    assert viewer.image_view.objectName() == "oswFigureImageView"
    assert viewer.metadata_panel.objectName() == "oswFigureMetadataPanel"
    assert viewer.workspace_table.objectName() == "oswWorkspaceVariablesTable"
    assert viewer.figure_list.count() == 3
    assert "gui-figures" in viewer.summary_label.text()
    assert viewer.workspace_table.rowCount() == 1

    del app


def test_plot_viewer_missing_image_uses_placeholder(app: object, tmp_path: Path) -> None:
    from osw.gui.plot_viewer import PlotViewer
    from osw.scripts.mscript.figure_capture import figure_dataset_from_artifacts

    dataset = figure_dataset_from_artifacts((tmp_path / "missing.png",), dataset_id="missing")
    viewer = PlotViewer()
    viewer.set_figure_dataset(dataset)

    assert "unavailable" in viewer.image_view.text().lower()
    del app


def test_plot_viewer_theme_updates(app: object) -> None:
    from osw.gui.plot_viewer import PlotViewer
    from osw.gui.theme_tokens import get_theme_tokens

    viewer = PlotViewer()
    viewer.set_theme_tokens(get_theme_tokens("dark"))
    viewer.set_theme_tokens(get_theme_tokens("light"))

    assert viewer.styleSheet()
    del app
