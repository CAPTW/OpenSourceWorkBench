from __future__ import annotations

from osw.core.project_schema import MeshRef, Project, ProjectMetadata, ReportConfig, ResultRef
from osw.post.report_generator import build_report_model, render_report_html
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

    html = render_report_html(build_report_model(project, result_tables=(table,)))
    markers = [
        "Project Summary",
        "Input Conditions",
        "Unit System",
        "Materials",
        "Mesh Info",
        "Solver Settings",
        "Warnings",
        "Figures",
        "3D Screenshots",
        "Result Tables",
        "Result Summary",
        "Validation Summary",
        "Known Limitations",
    ]

    positions = [html.index(marker) for marker in markers]

    assert positions == sorted(positions)
    assert "Golden result table" in html
    assert "No report warnings." in html
