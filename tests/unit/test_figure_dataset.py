from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from osw.scripts.mscript.figure_dataset import FigureDataset, FigureRecord
from osw.scripts.mscript.workspace_extractor import extract_figure_dataset

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def write_fake_png(path: Path) -> Path:
    path.write_bytes(PNG_BYTES)
    return path


def write_fake_svg(path: Path) -> Path:
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>',
        encoding="utf-8",
    )
    return path


def test_figure_record_loads_fake_png_and_svg(tmp_path: Path) -> None:
    png = write_fake_png(tmp_path / "plot.png")
    svg = write_fake_svg(tmp_path / "plot.svg")

    png_record = FigureRecord("fig-png", "PNG figure", png)
    svg_record = FigureRecord("fig-svg", "SVG figure", svg)

    assert png_record.image_format == "png"
    assert svg_record.image_format == "svg"
    assert png_record.load_image_bytes().startswith(b"\x89PNG")
    assert svg_record.load_image_bytes().startswith(b"<svg")


def test_workspace_extractor_builds_dataset_from_supported_images(tmp_path: Path) -> None:
    workspace = tmp_path / "octave_workspace"
    workspace.mkdir()
    write_fake_png(workspace / "simple_plot.png")
    write_fake_svg(workspace / "simple_plot.svg")
    (workspace / "notes.txt").write_text("not a figure", encoding="utf-8")

    dataset = extract_figure_dataset(workspace, dataset_id="octave-demo")

    assert dataset.dataset_id == "octave-demo"
    assert len(dataset.figures) == 2
    assert dataset.formats == ("png", "svg")
    assert [record.title for record in dataset.figures] == ["simple plot", "simple plot"]


def test_dataset_roundtrip_and_report_placeholders(tmp_path: Path) -> None:
    png = write_fake_png(tmp_path / "plot.png")
    dataset = FigureDataset(
        dataset_id="figures-1",
        figures=(
            FigureRecord(
                figure_id="figure-1",
                title="Stress plot",
                image_path=png,
                axes=("x", "stress"),
                raw_plot_data={"x": [0.0, 1.0], "stress": [0.0, 2.0]},
                reproducible_python="plt.plot(x, stress)",
            ),
        ),
        source="unit test",
        notes=("educational preview",),
    )

    restored = FigureDataset.from_dict(dataset.to_dict())

    assert restored == dataset
    assert restored.report_placeholders() == (
        f"figure-1: Stress plot [png] at {png}",
    )


def test_matplotlib_scene_exports_png_and_svg_or_skips(tmp_path: Path) -> None:
    if importlib.util.find_spec("matplotlib") is None:
        pytest.skip("Matplotlib optional viz extra is not installed.")

    from osw.post.matplotlib_scene import export_line_plot_dataset

    dataset = export_line_plot_dataset(
        x=(0.0, 1.0, 2.0),
        y=(0.0, 1.0, 4.0),
        output_dir=tmp_path,
        figure_id="simple-plot",
        title="Simple plot",
    )

    assert dataset.formats == ("png", "svg")
    assert all(record.image_path.exists() for record in dataset.figures)
    assert all(record.raw_plot_data is not None for record in dataset.figures)


def test_plot_viewer_rows_list_figures_without_pyside(tmp_path: Path) -> None:
    from osw.gui.plot_viewer import figure_display_rows

    dataset = FigureDataset(
        dataset_id="figures",
        figures=(FigureRecord("fig-1", "Sine curve", write_fake_png(tmp_path / "sine.png")),),
    )

    assert figure_display_rows(dataset) == ("fig-1 | Sine curve | png",)


def test_plot_viewer_widget_lists_figures_when_pyside_available(tmp_path: Path) -> None:
    if importlib.util.find_spec("PySide6") is None:
        pytest.skip("PySide6 optional GUI extra is not installed.")

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6 import QtWidgets

    from osw.gui.plot_viewer import PlotViewer

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    dataset = FigureDataset(
        dataset_id="figures",
        figures=(FigureRecord("fig-1", "Sine curve", write_fake_png(tmp_path / "sine.png")),),
    )

    viewer = PlotViewer()
    viewer.load_figure_dataset(dataset)

    assert viewer.objectName() == "plotViewer"
    assert viewer.figure_list.count() == 1
    assert viewer.figure_list.item(0).text() == "fig-1 | Sine curve | png"

    del app
