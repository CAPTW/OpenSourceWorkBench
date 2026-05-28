from __future__ import annotations

from pathlib import Path

from helpers import assert_text_matches_golden

from osw.core.project_schema import MeshRef, Project, ProjectMetadata, ReportConfig, ResultRef
from osw.post.report_generator import render_report_summary_html
from osw.post.report_sections import build_report_summary
from osw.post.table_model import TablePreview


def test_report_html_contains_required_sections_in_stable_order() -> None:
    project = Project(
        metadata=ProjectMetadata(name="Golden Report"),
        meshes=[MeshRef("mesh-1", "mesh/simple.vtu", "vtu")],
        results=[ResultRef("result-1", "results/table.csv", "table")],
        report=ReportConfig(title="Golden Report"),
    )
    table = TablePreview(
        columns=("x", "value"),
        rows=(("0", "1.0"),),
        title="Golden result table",
    )

    html = render_report_summary_html(build_report_summary(project, result_tables=(table,)))
    expected = (Path(__file__).with_name("required_sections.txt")).read_text(encoding="utf-8")
    markers = tuple(line for line in expected.splitlines() if line)

    positions = [html.index(marker) for marker in markers]

    assert positions == sorted(positions)
    assert_text_matches_golden(
        "\n".join(markers),
        expected,
        label="report/required_sections.txt",
    )
    assert "Golden result table" in html
    assert "No report warnings." in html
