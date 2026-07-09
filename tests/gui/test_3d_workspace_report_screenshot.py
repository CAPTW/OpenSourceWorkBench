"""3D-workspace scene screenshot -> report bridge tests (fake adapter, no render).

These tests prove the plumbing from a 3D-workspace ``SceneViewState`` plus a
captured ``SceneScreenshotRecord`` into report figure/HTML output. They inject a
fake PyVista module (never real PyVista/VTK), write only local dummy image paths,
run no solver/parser/mesh tool, and never save a project file or mutate
ProjectSchema / ResultDataset. A scene screenshot stays a local report artifact
only -- not validation evidence and not a release asset.
"""

from __future__ import annotations

from pathlib import Path

from osw.core.project_schema import MeshRef, Project, ProjectMetadata, ReportConfig
from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.gui.workspace_scene_view_model import (
    DefaultSceneAdapter,
    scene_view_state_from_toggles,
)
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.report_generator import build_report
from osw.post.report_model import (
    SCENE_SCREENSHOT_ARTIFACT_CAVEAT,
    ReportBuildRequest,
    scene_screenshot_to_report_figure,
)
from osw.post.scene_model import SceneScreenshotRecord


class _FakePolyData:
    def __init__(self, points: object, faces: object) -> None:
        self.points = points
        self.faces = faces
        self.point_data: dict[str, object] = {}


class _FakePlotter:
    def __init__(self, *, off_screen: bool = False) -> None:
        self.off_screen = off_screen
        self.screenshots: list[str] = []

    def add_mesh(self, dataset: object, **kwargs: object) -> None:
        return None

    def add_axes(self) -> None:
        return None

    def show_grid(self) -> None:
        return None

    def screenshot(self, path: str) -> None:
        self.screenshots.append(path)
        # Write a local dummy image; no real rendering is performed.
        Path(path).write_bytes(b"\x89PNG\r\n\x1a\n")


class _FakePyVista:
    """Minimal fake PyVista module; the scene bridge never imports the real one."""

    PolyData = _FakePolyData

    def __init__(self) -> None:
        self.plotters: list[_FakePlotter] = []

    def Plotter(self, *, off_screen: bool = False) -> _FakePlotter:
        plotter = _FakePlotter(off_screen=off_screen)
        self.plotters.append(plotter)
        return plotter


def _mesh() -> MeshData:
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        point_data={"temperature": (300.0, 310.0, 305.0)},
    )


def _project() -> Project:
    return Project(
        metadata=ProjectMetadata(name="Workspace Report"),
        meshes=[MeshRef("mesh-1", "mesh/beam.vtu", "vtu")],
        report=ReportConfig(title="Workspace Report"),
    )


def _capture_record(target: Path, *, record_id: str = "shot-1") -> SceneScreenshotRecord:
    """Capture a screenshot record through the default adapter and a fake PyVista."""
    adapter = DefaultSceneAdapter(pyvista_module=_FakePyVista())
    scene_state = scene_view_state_from_toggles(
        color_by="temperature",
        glyph_enabled=True,
        glyph_vector_field="U",
        glyph_scale=1.5,
        selected_selection_ids=("sel-a",),
    )
    return adapter.export_screenshot_record(
        str(target),
        record_id=record_id,
        scene_state=scene_state,
        mesh=_mesh(),
        mesh_ref="mesh-1",
        selection_ids=("sel-a",),
        caption="Iso preview",
        created_by="mesh-viewer",
    )


def test_captured_scene_screenshot_appears_in_report_without_live_pyvista(
    tmp_path: Path,
) -> None:
    target = tmp_path / "scenes" / "iso.png"
    record = _capture_record(target)

    # The fake adapter wrote a real local dummy image; no live PyVista was used.
    assert isinstance(record, SceneScreenshotRecord)
    assert Path(record.path).exists()
    assert record.scene_state.glyph_options.enabled is True

    output = tmp_path / "report.html"
    build_report(
        ReportBuildRequest(project=_project(), output_path=output, format="html"),
        scene_screenshots=[record],
    )
    html = output.read_text(encoding="utf-8")

    assert "3D Scene Screenshots" in html
    assert '<img src="scenes/iso.png"' in html
    assert "Iso preview" in html
    assert "Mesh ref: mesh-1" in html
    assert "Scalar field: temperature" in html
    assert "Vector glyphs: U" in html
    assert SCENE_SCREENSHOT_ARTIFACT_CAVEAT in html


def test_missing_scene_screenshot_renders_friendly_placeholder(tmp_path: Path) -> None:
    record = SceneScreenshotRecord(
        id="shot-missing",
        path=str(tmp_path / "missing.png"),
        caption="Absent capture",
        mesh_ref="mesh-1",
    )
    output = tmp_path / "report.html"

    result = build_report(
        ReportBuildRequest(project=_project(), output_path=output, format="html"),
        scene_screenshots=[record],
    )
    html = output.read_text(encoding="utf-8")

    assert "Scene screenshot not available" in html
    assert "<img" not in html
    assert any(
        "Scene screenshot image missing" in warning for warning in result.summary.warnings
    )


def test_metadata_only_scene_screenshot_renders_placeholder(tmp_path: Path) -> None:
    record = SceneScreenshotRecord(id="meta-only", path="", caption="Metadata only")

    figure = scene_screenshot_to_report_figure(record)
    assert figure.diagnostics.warnings()  # a metadata-only warning is recorded

    output = tmp_path / "report.html"
    build_report(
        ReportBuildRequest(project=_project(), output_path=output, format="html"),
        scene_screenshots=[record],
    )
    html = output.read_text(encoding="utf-8")

    assert "no local image path (metadata only)" in html
    assert "<img" not in html


def test_report_screenshot_flow_mutates_no_schema_and_saves_no_project(
    tmp_path: Path,
) -> None:
    project = _project()
    before_project = project.to_dict()
    dataset = ResultDataset(
        dataset_id="rd-1",
        source="fixture",
        solver="fake",
        analysis_type="static",
        fields=(
            ResultField(
                name="temperature",
                location="node",
                components=("t",),
                rows=(ResultRow(0, {"t": 1.0}),),
            ),
        ),
    )
    before_dataset = dataset.to_dict()

    record = _capture_record(tmp_path / "scene.png")
    output = tmp_path / "report.html"
    build_report(
        ReportBuildRequest(project=project, output_path=output, format="html"),
        scene_screenshots=[record],
    )

    # No ProjectSchema or ResultDataset mutation occurred through the report flow.
    assert project.to_dict() == before_project
    assert dataset.to_dict() == before_dataset
    # No project auto-save: only the report and the local screenshot were written.
    written = sorted(path.name for path in tmp_path.iterdir() if path.is_file())
    assert written == ["report.html", "scene.png"]

    figure = scene_screenshot_to_report_figure(record)
    assert figure.metadata["is_release_asset"] is False
    assert figure.metadata["is_validation_evidence"] is False


def test_report_screenshot_modules_avoid_render_and_solver_imports() -> None:
    import osw.post.report_generator as report_generator
    import osw.post.report_model as report_model

    for module in (report_model, report_generator):
        source = Path(module.__file__).read_text(encoding="utf-8")
        assert "import pyvista" not in source
        assert "import vtk" not in source
        assert "import subprocess" not in source
        assert "osw.solvers" not in source
