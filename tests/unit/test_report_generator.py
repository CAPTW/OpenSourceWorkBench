from __future__ import annotations

from pathlib import Path

from osw.core.boundary_curve import boundary_curve_from_xy
from osw.core.materials import IsotropicElastic, Material
from osw.core.project_schema import (
    BoundaryCondition,
    GeometryRef,
    MeshRef,
    PhysicsSetup,
    Project,
    ProjectMetadata,
    ReportConfig,
    ResultRef,
    ScriptRef,
    SolverConfig,
)
from osw.core.units import Quantity
from osw.mesh.mesh_model import MeshBoundingBox, MeshInfo
from osw.post.exporters import export_html_report
from osw.post.report_generator import (
    DEFAULT_REPORT_LIMITATIONS,
    build_report,
    build_report_model,
    build_report_summary,
    export_report_html,
    render_report_html,
    render_report_summary_html,
)
from osw.post.report_model import ReportBuildRequest
from osw.post.table_model import TablePreview
from osw.scripts.mscript.figure_dataset import FigureDataset, FigureRecord


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


def rich_project() -> Project:
    return Project(
        metadata=ProjectMetadata(
            name="Cantilever Demo",
            description="Small educational report export.",
            author="OSW tests",
            tags=["demo", "report"],
        ),
        materials=[
            Material(
                material_id="steel",
                name="Steel",
                density=Quantity(7850.0, "kg/m^3"),
                elastic=IsotropicElastic(
                    young_modulus=Quantity(210e9, "Pa"),
                    poisson_ratio=0.3,
                ),
            )
        ],
        geometry=[GeometryRef("geom-1", "geometry/beam.step", "step")],
        meshes=[MeshRef("mesh-1", "mesh/beam.vtk", "vtk")],
        scripts=[ScriptRef("script-1", "scripts/plot.m", "m")],
        boundary_curves=[
            boundary_curve_from_xy(
                curve_id="load-curve",
                name="Load curve",
                x_values=[0.0, 1.0],
                y_values=[0.0, 10.0],
                x_unit="s",
            )
        ],
        physics=[
            PhysicsSetup(
                setup_id="static",
                name="Static setup",
                analysis_type="linear_static",
                boundary_conditions=[
                    BoundaryCondition(
                        name="Fixed support",
                        kind="displacement",
                        target="face:left",
                        values={"ux": 0.0, "uy": 0.0, "uz": 0.0},
                    )
                ],
                material_assignments={"solid": "steel"},
            )
        ],
        solvers=[
            SolverConfig(
                solver_id="solver-1",
                name="CalculiX educational handoff",
                execution_mode="prepare_only",
                parameters={"analysis": "linear_static"},
            )
        ],
        results=[ResultRef("result-1", "results/displacement.json", "table")],
        report=ReportConfig(path="reports/report.html", title="Cantilever Report"),
    )


def sample_figure_dataset(tmp_path: Path) -> FigureDataset:
    figure_dir = tmp_path / "figures"
    figure_dir.mkdir()
    existing = figure_dir / "load_plot.png"
    existing.write_bytes(b"\x89PNG\r\n\x1a\n")
    missing = figure_dir / "missing_plot.png"
    return FigureDataset(
        dataset_id="script-figures",
        figures=(
            FigureRecord(
                figure_id="load-plot",
                title="Load Plot",
                image_path=existing,
                axes=("time", "load"),
            ),
            FigureRecord(
                figure_id="missing-plot",
                title="Missing Plot",
                image_path=missing,
            ),
        ),
        source="scripts/plot.m",
    )


def sample_result_table() -> TablePreview:
    return TablePreview(
        columns=("time_s", "disp_mm"),
        rows=(("0.0", "0.0"), ("1.0", "2.5")),
        title="Tip displacement",
        source="results/displacement.csv",
        notes=("fixture result",),
    )


def sample_mesh_info() -> MeshInfo:
    return MeshInfo(
        source="mesh/beam.vtk",
        format="vtk",
        nodes=4,
        elements=1,
        cell_types=("tetra",),
        bounding_box=MeshBoundingBox(minimum=(0.0, 0.0, 0.0), maximum=(1.0, 0.1, 0.1)),
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


def test_build_report_model_includes_full_report_contract(tmp_path: Path) -> None:
    model = build_report_model(
        rich_project(),
        figure_datasets=(sample_figure_dataset(tmp_path),),
        mesh_infos=(sample_mesh_info(),),
        result_tables=(sample_result_table(),),
        screenshots=(tmp_path / "viewer_missing.png",),
    )

    assert any("Steel" in item for item in model.material_summary)
    assert any("nodes=4" in item for item in model.mesh_summary)
    assert any("solver-1" in item for item in model.solver_summary)
    assert any("Boundary curves: 1" in item for item in model.input_conditions)
    assert any("missing_plot.png" in item for item in model.warning_summary)
    assert any("viewer_missing.png" in item for item in model.warning_summary)
    assert any("WARNING boundary_curves" in item for item in model.validation_summary)
    assert len(model.figures) == 2
    assert model.figures[0].status == "available"
    assert model.figures[1].status == "missing"
    assert model.result_tables[0].title == "Tip displacement"


def test_render_report_html_contains_project_metadata_and_limitations() -> None:
    html = render_report_html(build_report_model(minimal_project()))

    assert "<h1>Cantilever Report</h1>" in html
    assert "Cantilever Demo" in html
    assert "Small educational report export." in html
    assert "Known Limitations" in html
    assert "educational/research artifact" in html
    assert "Industrial certification" in html


def test_render_report_html_embeds_full_sections_and_handles_missing_images(
    tmp_path: Path,
) -> None:
    model = build_report_model(
        rich_project(),
        figure_datasets=(sample_figure_dataset(tmp_path),),
        mesh_infos=(sample_mesh_info(),),
        result_tables=(sample_result_table(),),
        screenshots=(tmp_path / "viewer_missing.png",),
    )

    html = render_report_html(model)

    for section in (
        "Input Conditions",
        "Unit System",
        "Materials",
        "Mesh Info",
        "Solver Settings",
        "Warnings",
        "Figures",
        "3D Screenshots",
        "Result Tables",
        "Validation Summary",
        "Known Limitations",
    ):
        assert section in html
    assert "Load Plot" in html
    assert "Figure image not available" in html
    assert "viewer_missing.png" in html
    assert "Tip displacement" in html
    assert "<td>2.5</td>" in html
    assert "WARNING boundary_curves[0].y_unit" in html


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


def test_export_report_html_accepts_figures_and_result_tables(tmp_path: Path) -> None:
    output_path = export_report_html(
        rich_project(),
        tmp_path / "report-output.html",
        figure_datasets=(sample_figure_dataset(tmp_path),),
        result_tables=(sample_result_table(),),
        mesh_infos=(sample_mesh_info(),),
    )

    text = output_path.read_text(encoding="utf-8")

    assert output_path == tmp_path / "report-output.html"
    assert "Figures" in text
    assert "Result Tables" in text
    assert "Tip displacement" in text


def test_exporters_wrapper_generates_html_report(tmp_path: Path) -> None:
    output_path = export_html_report(
        rich_project(),
        tmp_path,
        result_tables=(sample_result_table(),),
    )

    assert output_path == tmp_path / "report.html"
    assert "Tip displacement" in output_path.read_text(encoding="utf-8")


def test_build_report_summary_generates_full_html_and_json_summary(tmp_path: Path) -> None:
    project = rich_project()
    summary = build_report_summary(
        project,
        figure_datasets=(sample_figure_dataset(tmp_path),),
        mesh_infos=(sample_mesh_info(),),
        result_tables=(sample_result_table(),),
    )

    html = render_report_summary_html(summary, output_path=tmp_path / "report.html")
    result = build_report(
        ReportBuildRequest(project=project, output_path=tmp_path / "summary.json", format="json")
    )

    assert "Project Metadata" in html
    assert "Boundary Curves" in html
    assert "MAT / Workspace Variables" in html
    assert "FigureDataset / Figures" in html
    assert "Solver / Plugin / Execution Environment" in html
    assert "Figure artifact missing" in html
    assert result.output_path.endswith("summary.json")
    assert result.summary.title == "Cantilever Report"


def test_summary_html_escapes_user_strings_and_handles_missing_image(tmp_path: Path) -> None:
    project = Project(
        metadata=ProjectMetadata(name="<Unsafe>", description="A&B"),
        report=ReportConfig(title="Report <Title>"),
    )
    dataset = FigureDataset(
        dataset_id="figures",
        figures=(FigureRecord("bad", "<Plot>", image_path=tmp_path / "missing.png"),),
    )

    html = render_report_summary_html(
        build_report_summary(project, figure_datasets=(dataset,)),
        output_path=tmp_path / "report.html",
    )

    assert "Report &lt;Title&gt;" in html
    assert "&lt;Unsafe&gt;" in html
    assert "&lt;Plot&gt;" in html
    assert "Figure artifact missing" in html
    assert "<Unsafe>" not in html
