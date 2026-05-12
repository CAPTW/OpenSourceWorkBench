from __future__ import annotations

from pathlib import Path

from osw.core.project_schema import (
    GeometryRef,
    MeshRef,
    Project,
    ProjectMetadata,
    ReportConfig,
    ResultRef,
    ScriptRef,
)
from osw.post.report_generator import (
    DEFAULT_REPORT_LIMITATIONS,
    build_report_model,
    export_report_html,
    render_report_html,
)


def minimal_project() -> Project:
    return Project(
        metadata=ProjectMetadata(
            name="Cantilever Demo",
            description="Small educational report export.",
            author="OSW tests",
            tags=["demo", "report"],
        ),
        geometry=[GeometryRef("geom-1", "geometry/beam.step", "step")],
        meshes=[MeshRef("mesh-1", "mesh/beam.vtk", "vtk")],
        scripts=[ScriptRef("script-1", "scripts/plot.m", "m")],
        results=[ResultRef("result-1", "results/displacement.json", "table")],
        report=ReportConfig(path="reports/report.html", title="Cantilever Report"),
    )


def test_build_report_model_from_minimal_project() -> None:
    model = build_report_model(minimal_project())

    assert model.title == "Cantilever Report"
    assert model.project_name == "Cantilever Demo"
    assert ("Author", "OSW tests") in model.metadata_rows
    assert any("geometry" in item.lower() for item in model.input_summary)
    assert any("result-1" in item for item in model.result_summary)
    assert model.figure_list == ("No figure datasets registered yet.",)
    assert DEFAULT_REPORT_LIMITATIONS[0] in model.limitations


def test_render_report_html_contains_project_metadata_and_limitations() -> None:
    html = render_report_html(build_report_model(minimal_project()))

    assert "<h1>Cantilever Report</h1>" in html
    assert "Cantilever Demo" in html
    assert "Small educational report export." in html
    assert "Known Limitations" in html
    assert "educational/research artifact" in html
    assert "Industrial certification" in html


def test_render_report_html_escapes_project_text() -> None:
    project = Project(
        metadata=ProjectMetadata(name="<Unsafe>", description="A&B"),
        report=ReportConfig(title="Report <Title>"),
    )

    html = render_report_html(build_report_model(project))

    assert "&lt;Unsafe&gt;" in html
    assert "A&amp;B" in html
    assert "<Unsafe>" not in html


def test_export_report_html_writes_report_file(tmp_path: Path) -> None:
    output_path = export_report_html(minimal_project(), tmp_path)

    assert output_path == tmp_path / "report.html"
    assert output_path.exists()
    text = output_path.read_text(encoding="utf-8")
    assert "Cantilever Report" in text
    assert "Input Summary" in text
    assert "Result Summary" in text
