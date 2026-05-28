from __future__ import annotations

import json
from pathlib import Path

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.diagnostics import DiagnosticReport
from osw.post.report_model import (
    ReportAsset,
    ReportBuildRequest,
    ReportBuildResult,
    ReportFigure,
    ReportFormat,
    ReportSection,
    ReportSummary,
    ReportTable,
)


def test_report_asset_serializes_paths_as_strings(tmp_path: Path) -> None:
    asset_path = tmp_path / "figure.png"
    asset_path.write_bytes(b"png")
    asset = ReportAsset("figure-1", asset_path, "figure", format="png", caption="Plot")

    loaded = ReportAsset.from_dict(json.loads(json.dumps(asset.to_dict())))

    assert loaded == asset
    assert isinstance(loaded.path, str)
    assert loaded.exists is True
    assert loaded.size_bytes == 3


def test_report_section_table_figure_summary_round_trip(tmp_path: Path) -> None:
    figure_path = tmp_path / "plot.svg"
    figure_path.write_text("<svg></svg>", encoding="utf-8")
    diagnostics = DiagnosticReport()
    diagnostics.add_warning("report-test", "warning")
    summary = ReportSummary(
        title="Report",
        project_name="Project",
        run_label="Run 1",
        sections=(ReportSection("overview", "Overview", content_blocks=("Ready",)),),
        tables=(ReportTable("table-1", "Table", ("a",), (("b",),)),),
        figures=(ReportFigure("fig-1", "Plot", vector_path=figure_path),),
        assets=(ReportAsset("fig-1", figure_path, "figure"),),
        warnings=("warning",),
        diagnostics=diagnostics,
    )

    loaded = ReportSummary.from_dict(json.loads(json.dumps(summary.to_dict())))

    assert loaded == summary
    assert loaded.section_titles == ("Overview",)
    assert loaded.figure_count == 1
    assert loaded.warning_count == 2
    assert loaded.figures[0].vector_path == str(figure_path)


def test_report_build_request_and_result_serialize(tmp_path: Path) -> None:
    project = create_heatsink_flow_demo_project()
    request = ReportBuildRequest(
        project,
        output_path=tmp_path / "report.html",
        format=ReportFormat.HTML,
    )
    summary = ReportSummary("Demo", project.metadata.name)
    result = ReportBuildResult("ok", tmp_path / "report.html", summary)

    request_payload = request.to_dict()
    loaded_result = ReportBuildResult.from_dict(result.to_dict())

    assert request_payload["format"] == "html"
    assert request_payload["project"]["metadata"]["name"] == "HeatSink_Flow"
    assert loaded_result == result
    assert loaded_result.ok
