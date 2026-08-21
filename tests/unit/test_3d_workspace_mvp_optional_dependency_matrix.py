"""Optional-dependency present/absent matrix for the 3D Workspace MVP journey."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.helpers.workspace_3d_mvp_e2e import (
    FailingSceneFactory,
    e2e_mesh,
    empty_e2e_project,
    fixture_quality_analyzer,
    load_e2e_mesh,
    make_controller,
    run_renderer_neutral_author_journey,
    workspace_paths,
    write_nonblank_png,
)

from osw.core.project_io import load_project, save_project
from osw.core.project_schema import project_with
from osw.core.workspace_3d import (
    ACTIVE_SCENE_SCHEMA,
    ActiveSceneRestoreStatus,
    ActiveSceneState,
)
from osw.gui.workspace_scene_controller import ActiveSceneController
from osw.mesh.quality import MeshDiagnosticsStatus, analyze_mesh_cell_quality
from osw.post.report_generator import build_report
from osw.post.report_model import (
    ReportBuildRequest,
    ReportFormat,
    report_assets_to_scene_screenshots,
)


def test_matrix_a_base_core_paths_do_not_require_native_renderer(tmp_path: Path) -> None:
    import osw.core.project_schema
    import osw.core.workspace_3d
    import osw.mesh.identity
    import osw.post.report_generator

    assert osw.core.project_schema.CURRENT_SCHEMA_VERSION == "0.4"
    assert osw.core.workspace_3d.ACTIVE_SCENE_SCHEMA == ACTIVE_SCENE_SCHEMA
    mesh = e2e_mesh()
    fingerprint = osw.mesh.identity.compute_mesh_fingerprint(mesh)
    project = empty_e2e_project()
    state = ActiveSceneState(
        mesh_ref="mesh-mvp-e2e-complete",
        mesh_fingerprint=fingerprint.digest,
    )
    target = tmp_path / "core-project.osw.json"
    saved = project_with(project, active_scene=state)
    save_project(saved, target)
    reopened = load_project(target)
    assert reopened.active_scene is not None
    assert reopened.active_scene.mesh_fingerprint == fingerprint.digest
    html = osw.post.report_generator.export_report_html(reopened, tmp_path / "core-report.html")
    assert html.is_file()


def test_matrix_c_diagnostics_provider_absent_keeps_partial_restore(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from osw.mesh import quality_pyvista

    def missing(name: str) -> object:
        if name == "pyvista":
            raise ModuleNotFoundError(name)
        raise AssertionError(name)

    monkeypatch.setattr(quality_pyvista, "import_module", missing)

    def absent_analyzer(mesh: object, **kwargs: object) -> object:
        return analyze_mesh_cell_quality(
            mesh,
            provider=quality_pyvista.PyVistaScaledJacobianProvider(),
            **kwargs,
        )

    mesh = e2e_mesh()
    analysis = absent_analyzer(mesh)
    assert analysis.status is MeshDiagnosticsStatus.UNAVAILABLE_OPTIONAL_DEPENDENCY
    assert analysis.node_count == len(mesh.points)
    workspace = tmp_path / "provider-absent"
    workspace.mkdir()
    authored = run_renderer_neutral_author_journey(workspace)
    project = load_project(workspace_paths(workspace)["project"])
    controller = ActiveSceneController(
        FailingSceneFactory(),
        mesh_quality_analyzer=absent_analyzer,
    )
    controller.set_pending_active_scene_state(project.active_scene)
    load_e2e_mesh(controller, mesh)
    result = controller.active_scene_restore_result
    assert result.status in {
        ActiveSceneRestoreStatus.PARTIAL,
        ActiveSceneRestoreStatus.STALE,
        ActiveSceneRestoreStatus.RESTORED,
    }
    assert "mesh_bad_elements" not in controller.actor_records
    assert project.active_scene is not None
    assert project.active_scene.mesh_quality_state is not None
    assert project.active_scene.mesh_quality_state.threshold == 0.3
    html = build_report(
        ReportBuildRequest(
            project=project,
            output_path=tmp_path / "provider-absent-report.html",
            format=ReportFormat.HTML,
        ),
        scene_screenshots=report_assets_to_scene_screenshots(project.report_screenshots),
    )
    assert Path(html.output_path).is_file()
    assert authored["image_byte_length"] > 0
    controller.close()


def test_matrix_d_native_renderer_absent_keeps_logical_state_and_report(tmp_path: Path) -> None:
    workspace = tmp_path / "renderer-absent"
    workspace.mkdir()
    run_renderer_neutral_author_journey(workspace)
    project = load_project(workspace_paths(workspace)["project"])
    controller = ActiveSceneController(FailingSceneFactory())
    controller.set_pending_active_scene_state(project.active_scene)
    load_e2e_mesh(controller, e2e_mesh())
    assert controller.fallback_reason
    capture = controller.capture_active_scene_screenshot
    from osw.core.workspace_3d import ActiveSceneScreenshotRequest

    blocked = capture(
        ActiveSceneScreenshotRequest(
            record_id="blocked-capture",
            output_path=str(tmp_path / "blocked.png"),
        )
    )
    assert blocked.status == "BLOCKED"
    html = build_report(
        ReportBuildRequest(
            project=project,
            output_path=tmp_path / "renderer-absent-report.html",
            format=ReportFormat.HTML,
        ),
        scene_screenshots=report_assets_to_scene_screenshots(project.report_screenshots),
    )
    assert "MVP E2E captured scene" in Path(html.output_path).read_text(encoding="utf-8")
    assert project.active_scene is not None
    controller.close()


def test_matrix_e_pdf_optional_is_explicit_and_does_not_fake_pdf(tmp_path: Path) -> None:
    workspace = tmp_path / "pdf-optional"
    workspace.mkdir()
    run_renderer_neutral_author_journey(workspace)
    project = load_project(workspace_paths(workspace)["project"])
    result = build_report(
        ReportBuildRequest(
            project=project,
            output_path=tmp_path / "optional.pdf.html",
            format=ReportFormat.PDF_OPTIONAL,
        ),
        scene_screenshots=report_assets_to_scene_screenshots(project.report_screenshots),
    )
    codes = {str(message.code) for message in result.diagnostics.messages}
    assert "report-pdf-deferred" in codes
    output = Path(result.output_path).read_text(encoding="utf-8")
    assert output.lstrip().startswith("<")
    assert b"%PDF" not in Path(result.output_path).read_bytes()


def test_matrix_f_missing_capture_asset_is_fail_closed_and_logical_restore_remains(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "missing-asset"
    workspace.mkdir()
    run_renderer_neutral_author_journey(workspace)
    paths = workspace_paths(workspace)
    paths["capture"].unlink()
    project = load_project(paths["project"])
    assert project.report_screenshots
    assert project.report_screenshots[0].id
    result = build_report(
        ReportBuildRequest(
            project=project,
            output_path=tmp_path / "missing-asset-report.html",
            format=ReportFormat.HTML,
        ),
        scene_screenshots=report_assets_to_scene_screenshots(project.report_screenshots),
    )
    codes = {str(message.code) for message in result.diagnostics.messages}
    assert "report-scene-screenshot-missing" in codes
    assert project.active_scene is not None
    controller = make_controller()
    controller.set_pending_active_scene_state(project.active_scene)
    load_e2e_mesh(controller, e2e_mesh())
    assert controller.active_scene_restore_result.status in {
        ActiveSceneRestoreStatus.PARTIAL,
        ActiveSceneRestoreStatus.RESTORED,
    }
    write_nonblank_png(paths["capture"])
    controller.close()


def test_matrix_c_fixture_provider_still_evaluates_when_injected() -> None:
    analysis = fixture_quality_analyzer(e2e_mesh(), threshold=0.3)
    assert analysis.bad_cell_keys == ("3:1",)
    assert analysis.uncovered_count == 1


def test_matrix_b_real_provider_marks_fixture_bad_tetra_when_available() -> None:
    analysis = analyze_mesh_cell_quality(e2e_mesh(), threshold=0.3)
    if analysis.status is MeshDiagnosticsStatus.UNAVAILABLE_OPTIONAL_DEPENDENCY:
        assert analysis.node_count == len(e2e_mesh().points)
        return
    assert analysis.uncovered_count == 1
    assert analysis.bad_cell_keys
    assert "3:1" in analysis.bad_cell_keys
