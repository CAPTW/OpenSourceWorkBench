from __future__ import annotations

import json
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
from osw.core.result_dataset import ResultDataset
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
    render_scene_screenshot_section,
)
from osw.post.report_model import (
    SCENE_SCREENSHOT_ARTIFACT_CAVEAT,
    ReportBuildRequest,
    scene_screenshots_to_report_figures,
)
from osw.post.scene_model import (
    SceneGlyphOptions,
    SceneRenderOptions,
    SceneScreenshotRecord,
    SceneViewState,
)
from osw.post.table_model import TablePreview
from osw.scripts.mscript.figure_dataset import FigureDataset, FigureRecord
from osw.solvers.coolprop.model import (
    CoolPropPropertyRequest,
    CoolPropPropertyResult,
    CoolPropPropertyValue,
    PropertyInputPair,
)
from osw.solvers.coolprop.results import coolprop_result_to_result_dataset
from osw.solvers.openfoam.residual_parser import parse_openfoam_residuals_from_text
from osw.solvers.openfoam.results import openfoam_residuals_to_result_dataset


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


def test_build_report_summary_accepts_openfoam_residual_dataset(tmp_path: Path) -> None:
    residuals = parse_openfoam_residuals_from_text(
        "Time = 1\n"
        "Solving for Ux, Initial residual = 0.1, Final residual = 0.01, No Iterations 2\n"
        "Solving for p, Initial residual = 0.2, Final residual = 0.02, No Iterations 2\n"
    )
    dataset = openfoam_residuals_to_result_dataset(residuals, solver="icoFoam")

    summary = build_report_summary(
        rich_project(),
        result_tables=dataset.to_report_tables(),
    )
    html = render_report_summary_html(summary, output_path=tmp_path / "report.html")

    assert "icoFoam result summary" in html
    assert "final_residual_p" in html


def test_build_report_summary_accepts_chm_result_dataset(tmp_path: Path) -> None:
    dataset = coolprop_result_to_result_dataset(
        CoolPropPropertyResult(
            "ok",
            CoolPropPropertyRequest(
                "Water",
                PropertyInputPair("T", 300.0, "P", 101325.0),
            ),
            values=(CoolPropPropertyValue("density", 997.0, "kg/m^3"),),
        )
    )

    summary = build_report_summary(
        rich_project(),
        result_tables=dataset.to_report_tables(),
    )
    html = render_report_summary_html(summary, output_path=tmp_path / "report.html")

    assert "CoolProp property table" in html
    assert "density" in html
    assert "kg/m^3" in html


def test_build_report_summary_accepts_field_dataset_metadata(tmp_path: Path) -> None:
    fixture = Path(__file__).parents[1] / "fixtures" / "fields" / "scalar_field_dataset.json"
    dataset = ResultDataset.from_dict(json.loads(fixture.read_text(encoding="utf-8")))

    summary = build_report_summary(
        rich_project(),
        result_tables=dataset.to_report_tables(),
    )
    html = render_report_summary_html(summary, output_path=tmp_path / "report.html")

    assert "Field arrays" in html
    assert "temperature" in html
    assert "velocity" in html


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


def _scene_record(path: str, *, record_id: str = "shot-1") -> SceneScreenshotRecord:
    return SceneScreenshotRecord(
        id=record_id,
        path=path,
        caption="Iso temperature view",
        scene_state=SceneViewState(
            render_options=SceneRenderOptions(color_by="temperature"),
            glyph_options=SceneGlyphOptions(enabled=True, vector_field="U", scale=2.0),
            scalar_field_id="temperature",
        ),
        dataset_ref="rd-1",
        mesh_ref="mesh-1",
        selection_ids=("sel-a",),
        created_by="mesh-viewer",
    )


def test_render_scene_screenshot_section_renders_available_image(tmp_path: Path) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    figures = scene_screenshots_to_report_figures([_scene_record(str(image))])

    html = render_scene_screenshot_section(figures, output_path=tmp_path / "report.html")

    assert "3D Scene Screenshots" in html
    assert '<img src="scene.png"' in html
    assert "Mesh ref: mesh-1" in html
    assert "Result dataset ref: rd-1" in html
    assert "Scalar field: temperature" in html
    assert "Vector glyphs: U" in html
    assert "Captured by: mesh-viewer" in html
    assert SCENE_SCREENSHOT_ARTIFACT_CAVEAT in html
    assert "Scene screenshot not available" not in html


def test_render_scene_screenshot_section_missing_image_is_friendly(tmp_path: Path) -> None:
    figures = scene_screenshots_to_report_figures(
        [_scene_record(str(tmp_path / "missing.png"))]
    )

    html = render_scene_screenshot_section(figures, output_path=tmp_path / "report.html")

    assert "Scene screenshot not available" in html
    assert "missing.png" in html
    assert "<img" not in html
    # Provenance and caveat are still shown for a missing image.
    assert "Mesh ref: mesh-1" in html
    assert SCENE_SCREENSHOT_ARTIFACT_CAVEAT in html


def test_render_scene_screenshot_section_links_existing_non_image_artifact(
    tmp_path: Path,
) -> None:
    # A file that exists but is not an inline image format must be linked as an
    # artifact, not mislabeled "not available".
    artifact = tmp_path / "scene.tif"
    artifact.write_bytes(b"II*\x00")
    figures = scene_screenshots_to_report_figures([_scene_record(str(artifact))])

    html = render_scene_screenshot_section(figures, output_path=tmp_path / "report.html")

    assert 'href="scene.tif"' in html
    assert "Scene screenshot artifact (TIF)" in html
    assert "Scene screenshot not available" not in html
    assert "<img" not in html


def test_build_report_existing_non_image_scene_screenshot_emits_no_missing_warning(
    tmp_path: Path,
) -> None:
    artifact = tmp_path / "scene.tif"
    artifact.write_bytes(b"II*\x00")
    output = tmp_path / "report.html"

    result = build_report(
        ReportBuildRequest(project=minimal_project(), output_path=output, format="html"),
        scene_screenshots=[_scene_record(str(artifact))],
    )

    # The file exists, so no missing-screenshot warning or diagnostic is raised.
    assert not any(
        "Scene screenshot" in warning and "missing" in warning
        for warning in result.summary.warnings
    )
    assert not any(
        message.code == "report-scene-screenshot-missing"
        for message in result.diagnostics.messages
    )


def test_render_scene_screenshot_section_metadata_only_placeholder() -> None:
    figures = scene_screenshots_to_report_figures(
        [SceneScreenshotRecord(id="meta-only", path="", caption="No image yet")]
    )

    html = render_scene_screenshot_section(figures)

    assert "no local image path (metadata only)" in html
    assert "<img" not in html


def test_render_scene_screenshot_section_empty_returns_blank() -> None:
    assert render_scene_screenshot_section(()) == ""


def test_render_report_summary_html_unchanged_without_scene_screenshots(tmp_path: Path) -> None:
    summary = build_report_summary(minimal_project())
    output = tmp_path / "report.html"

    baseline = render_report_summary_html(summary, output_path=output)
    with_empty = render_report_summary_html(summary, output_path=output, scene_screenshots=())

    assert baseline == with_empty
    assert "3D Scene Screenshots" not in baseline


def test_build_report_html_includes_scene_screenshots(tmp_path: Path) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    available = _scene_record(str(image), record_id="shot-available")
    missing = _scene_record(str(tmp_path / "missing.png"), record_id="shot-missing")
    output = tmp_path / "report.html"

    result = build_report(
        ReportBuildRequest(project=minimal_project(), output_path=output, format="html"),
        scene_screenshots=[available, missing],
    )
    html = output.read_text(encoding="utf-8")

    assert "3D Scene Screenshots" in html
    assert '<img src="scene.png"' in html
    assert "Scene screenshot not available" in html
    # The missing screenshot surfaces as a report warning and a diagnostic.
    assert any("Scene screenshot image missing" in warning for warning in result.summary.warnings)
    assert any(
        message.code == "report-scene-screenshot-missing"
        for message in result.diagnostics.messages
    )
    # Provenance is recorded in the summary metadata for the JSON summary too.
    scene_meta = result.summary.metadata["scene_screenshots"]
    assert [entry["figure_id"] for entry in scene_meta] == ["shot-available", "shot-missing"]
    assert scene_meta[0]["metadata"]["mesh_ref"] == "mesh-1"
    assert scene_meta[0]["metadata"]["artifact_caveat"] == SCENE_SCREENSHOT_ARTIFACT_CAVEAT


def test_build_report_json_summary_includes_scene_screenshots(tmp_path: Path) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    output = tmp_path / "summary.json"

    build_report(
        ReportBuildRequest(project=minimal_project(), output_path=output, format="json"),
        scene_screenshots=[_scene_record(str(image))],
    )
    data = json.loads(output.read_text(encoding="utf-8"))

    scene_meta = data["metadata"]["scene_screenshots"]
    assert scene_meta[0]["metadata"]["scalar_field_id"] == "temperature"
    assert scene_meta[0]["metadata"]["is_validation_evidence"] is False
    assert scene_meta[0]["metadata"]["is_release_asset"] is False


def test_build_report_without_scene_screenshots_has_no_scene_section(tmp_path: Path) -> None:
    output = tmp_path / "report.html"
    result = build_report(
        ReportBuildRequest(project=minimal_project(), output_path=output, format="html")
    )

    assert "3D Scene Screenshots" not in output.read_text(encoding="utf-8")
    assert "scene_screenshots" not in result.summary.metadata


def test_export_report_html_threads_scene_screenshots(tmp_path: Path) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")

    output_path = export_report_html(
        minimal_project(),
        tmp_path / "report.html",
        scene_screenshots=[_scene_record(str(image))],
    )

    html = output_path.read_text(encoding="utf-8")
    assert "3D Scene Screenshots" in html
    assert '<img src="scene.png"' in html


def test_export_html_report_wrapper_threads_scene_screenshots(tmp_path: Path) -> None:
    image = tmp_path / "scene.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")

    output_path = export_html_report(
        minimal_project(),
        tmp_path,
        scene_screenshots=[_scene_record(str(image))],
    )

    assert "3D Scene Screenshots" in output_path.read_text(encoding="utf-8")
