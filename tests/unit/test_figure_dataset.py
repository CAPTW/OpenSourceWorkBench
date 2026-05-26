from __future__ import annotations

import json
from pathlib import Path

from osw.scripts.mscript.figure_dataset import (
    AxisRecord,
    FigureDataset,
    FigureFormat,
    FigureRecord,
    WorkspaceVariableSummary,
)

PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def write_fake_png(path: Path) -> Path:
    path.write_bytes(PNG_BYTES)
    return path


def test_axis_record_round_trips() -> None:
    axis = AxisRecord(
        axis_id="axis-1",
        title="Temperature",
        xlabel="x",
        ylabel="T",
        xlim=(0.0, 1.0),
        legend=("centreline",),
    )

    assert AxisRecord.from_dict(axis.to_dict()) == axis
    assert axis.display_label() == "x / T"


def test_workspace_variable_summary_round_trips() -> None:
    variable = WorkspaceVariableSummary(
        name="temperature",
        type_name="double",
        shape=(1, 3),
        dtype="float64",
        size=3,
        preview="[300, 315, 330]",
        source="workspace_summary.json",
    )

    assert WorkspaceVariableSummary.from_dict(variable.to_dict()) == variable


def test_figure_record_round_trips_and_loads_png(tmp_path: Path) -> None:
    png = write_fake_png(tmp_path / "plot.png")
    record = FigureRecord(
        figure_id="fig-png",
        title="PNG figure",
        image_path=png,
        axes=("x", "temperature"),
        raw_plot_data={"x": [0.0, 1.0]},
        reproducible_python="plt.plot(x, temperature)",
    )

    restored = FigureRecord.from_dict(record.to_dict())

    assert restored == record
    assert restored.image_format == FigureFormat.PNG.value
    assert restored.load_image_bytes().startswith(b"\x89PNG")
    assert restored.axes[0].display_label() == "x"


def test_figure_dataset_json_round_trip(tmp_path: Path) -> None:
    dataset = FigureDataset(
        dataset_id="figures-1",
        figures=(
            FigureRecord(
                figure_id="figure-1",
                title="Stress plot",
                image_path=write_fake_png(tmp_path / "plot.png"),
                axes=(AxisRecord("axis-1", xlabel="x", ylabel="stress"),),
            ),
        ),
        source="unit test",
        source_run_id="run-001",
        engine="octave",
        workspace_variables=(
            WorkspaceVariableSummary("x", "double", shape=(1, 2), dtype="float64"),
        ),
        notes=("educational preview",),
    )

    restored = FigureDataset.from_dict(json.loads(json.dumps(dataset.to_dict())))

    assert restored == dataset
    assert restored.report_placeholders() == (
        f"figure-1: Stress plot [png] at {tmp_path / 'plot.png'}",
    )


def test_from_image_paths_supports_png_svg_pdf(tmp_path: Path) -> None:
    png = write_fake_png(tmp_path / "plot.png")
    svg = tmp_path / "plot.svg"
    svg.write_text("<svg></svg>", encoding="utf-8")
    pdf = tmp_path / "report.pdf"
    pdf.write_text("%PDF-1.4\n%%EOF\n", encoding="utf-8")

    dataset = FigureDataset.from_image_paths((png, svg, pdf), dataset_id="figures")

    assert dataset.formats == ("png", "svg", "pdf")
    assert dataset.figures[1].vector_path == svg
    assert dataset.figures[2].pdf_path == pdf
