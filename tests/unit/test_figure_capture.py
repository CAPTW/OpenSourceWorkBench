from __future__ import annotations

import json
from pathlib import Path

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.scripts.mscript.figure_capture import (
    classify_figure_artifact,
    discover_figure_artifacts,
    export_figure_dataset_json,
    figure_dataset_from_artifacts,
    figure_dataset_from_octave_result,
    figure_record_from_artifact,
    generate_thumbnail,
    load_figure_dataset_json,
    octave_save_figures_snippet,
)
from osw.scripts.mscript.figure_dataset import FigureFormat
from osw.scripts.mscript.octave_runner import OctaveRunResult, OctaveRunStatus

FIXTURES = Path(__file__).parents[1] / "fixtures" / "figures"


def test_classifies_png_svg_pdf_csv_and_unknown() -> None:
    assert classify_figure_artifact("plot.png") is FigureFormat.PNG
    assert classify_figure_artifact("plot.svg") is FigureFormat.SVG
    assert classify_figure_artifact("plot.pdf") is FigureFormat.PDF
    assert classify_figure_artifact("table.csv") is FigureFormat.CSV
    assert classify_figure_artifact("notes.txt") is FigureFormat.UNKNOWN


def test_discovers_artifacts_in_directory() -> None:
    paths = discover_figure_artifacts(FIXTURES)

    names = {path.name for path in paths}
    assert {"simple_plot.png", "simple_plot.svg", "simple_report.pdf", "table_data.csv"}.issubset(
        names
    )


def test_creates_records_from_artifacts() -> None:
    png = figure_record_from_artifact(FIXTURES / "simple_plot.png", source_run_id="run-1")
    svg = figure_record_from_artifact(FIXTURES / "simple_plot.svg")
    pdf = figure_record_from_artifact(FIXTURES / "simple_report.pdf")

    assert png.image_path is not None
    assert svg.vector_path is not None
    assert pdf.pdf_path is not None
    assert png.source_run_id == "run-1"


def test_dataset_from_artifacts_preserves_sources_and_workspace_summaries() -> None:
    dataset = figure_dataset_from_artifacts(
        (
            FIXTURES / "simple_plot.png",
            FIXTURES / "simple_plot.svg",
            FIXTURES / "simple_report.pdf",
            FIXTURES / "table_data.csv",
            FIXTURES / "workspace_summary.json",
        ),
        source_script="plot.m",
        source_run_id="run-1",
        dataset_id="figures",
    )

    assert dataset.dataset_id == "figures"
    assert {record.image_format for record in dataset.figures} >= {"png", "svg", "pdf", "csv"}
    assert dataset.source_file == "plot.m"
    assert dataset.source_run_id == "run-1"
    assert {variable.name for variable in dataset.workspace_variables} >= {
        "table_data",
        "x",
        "temperature",
    }


def test_missing_and_unknown_artifacts_produce_diagnostics(tmp_path: Path) -> None:
    unknown = tmp_path / "notes.txt"
    unknown.write_text("not a figure", encoding="utf-8")
    dataset = figure_dataset_from_artifacts((tmp_path / "missing.png", unknown))

    assert any(
        message.code == "figure-artifact-missing"
        for message in dataset.diagnostics.messages
    )
    assert any(
        message.code == "figure-artifact-unknown-format"
        for message in dataset.diagnostics.messages
    )


def test_octave_result_handoff_creates_dataset(tmp_path: Path) -> None:
    png = tmp_path / "plot.png"
    png.write_text("placeholder", encoding="utf-8")
    csv = tmp_path / "table.csv"
    csv.write_text("x,y\n0,0\n", encoding="utf-8")
    result = OctaveRunResult(
        run_id="run-42",
        status=OctaveRunStatus.COMPLETED,
        script_path="plot.m",
        workspace_dir=str(tmp_path),
        stdout="ok",
        stderr="",
        artifacts=(
            RunArtifact(png, "octave_artifact", format="png"),
            RunArtifact(csv, "octave_artifact", format="csv"),
        ),
        diagnostics=DiagnosticReport(),
    )

    dataset = figure_dataset_from_octave_result(result)

    assert dataset.source_run_id == "run-42"
    assert dataset.engine == "octave"
    assert dataset.stdout == "ok"
    assert len(dataset.figures) == 2
    assert dataset.workspace_variables[0].name == "table"


def test_thumbnail_generation_skips_cleanly_without_valid_source(tmp_path: Path) -> None:
    record = figure_record_from_artifact(tmp_path / "missing.png")

    updated = generate_thumbnail(record, tmp_path)

    assert updated.thumbnail_path is None
    assert updated.diagnostics.messages


def test_dataset_json_helpers_round_trip(tmp_path: Path) -> None:
    dataset = figure_dataset_from_artifacts((FIXTURES / "simple_plot.png",), dataset_id="figures")
    output = export_figure_dataset_json(dataset, tmp_path / "dataset.json")

    restored = load_figure_dataset_json(output)

    assert restored == dataset
    assert json.loads(output.read_text(encoding="utf-8"))["dataset_id"] == "figures"


def test_octave_save_figures_snippet_is_opt_in_text_only() -> None:
    snippet = octave_save_figures_snippet(formats=("png",), basename="plot")

    assert "findall" in snippet
    assert "plot_" in snippet
