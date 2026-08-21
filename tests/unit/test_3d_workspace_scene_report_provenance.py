"""Active-scene screenshot provenance and report-consumption tests."""

from __future__ import annotations

from pathlib import Path


def _active_state() -> object:
    from osw.core.workspace_3d import (
        ActiveSceneCameraState,
        ActiveSceneResultState,
        ActiveSceneState,
        MeshQualityViewState,
        SemanticActorVisibility,
    )

    return ActiveSceneState(
        mesh_ref="mesh-1",
        mesh_fingerprint="b" * 64,
        camera=ActiveSceneCameraState(
            position=(2.0, 2.0, 2.0),
            focal_point=(0.0, 0.0, 0.0),
            view_up=(0.0, 0.0, 1.0),
        ),
        representation="surface_with_edges",
        axes_visible=True,
        actor_visibility=(
            SemanticActorVisibility(
                "material_assignment",
                "material-record-1",
                visible=True,
            ),
        ),
        visible_named_selection_ids=("selection-1",),
        active_named_selection_ids=("selection-1",),
        result_state=ActiveSceneResultState(
            result_ref_id="result-1",
            result_dataset_id="dataset-1",
            binding_schema="osw.result_mesh_binding.v2",
            mesh_fingerprint="b" * 64,
            scalar_field="stress",
            scalar_component="von_mises",
            scalar_association="cell",
            range_mode="MANUAL",
            manual_min=0.0,
            manual_max=250.0,
            colormap="viridis",
            colorbar_visible=True,
            vector_field="disp",
            vector_visible=True,
            deformation_field="disp",
            deformation_mode="DEFORMED",
        ),
        mesh_quality_state=MeshQualityViewState(
            metric_schema="osw.mesh_quality.edge_aspect_ratio.v1",
            threshold=8.0,
            highlight_visible=True,
        ),
    )


def _record(image: Path) -> object:
    from osw.core.workspace_3d import active_scene_provenance
    from osw.post.scene_model import SceneScreenshotRecord

    state = _active_state()
    return SceneScreenshotRecord(
        id="shot-1",
        path=str(image),
        caption="Explicit current-session capture",
        mesh_ref="mesh-1",
        metadata={
            "osw.active_scene.provenance": active_scene_provenance(
                state,
                image_sha256="c" * 64,
                image_byte_length=123,
                image_size=(640, 480),
                capture_backend_kind="fake-current-session",
            )
        },
    )


def test_scene_record_asset_bridge_preserves_active_scene_provenance() -> None:
    from osw.post.report_model import (
        report_asset_to_scene_screenshot,
        scene_screenshot_to_report_asset,
        scene_screenshot_to_report_figure,
    )

    record = _record(Path("scene.png"))
    asset = scene_screenshot_to_report_asset(record)
    reopened = report_asset_to_scene_screenshot(asset)
    figure = scene_screenshot_to_report_figure(reopened)

    provenance = asset.metadata["osw.active_scene.provenance"]
    assert provenance["active_scene_schema"] == "osw.active_scene.v1"
    assert provenance["mesh_fingerprint"] == "b" * 64
    assert provenance["active_scene_digest"]
    assert provenance["capture_backend_kind"] == "fake-current-session"
    assert reopened.metadata == asset.metadata
    assert figure.metadata["active_scene_provenance"] == provenance


def test_report_provenance_lines_are_deterministic_compact_and_path_free(
    tmp_path: Path,
) -> None:
    from osw.post.report_generator import _scene_screenshot_provenance_lines
    from osw.post.report_model import scene_screenshot_to_report_figure

    record = _record(tmp_path / "private" / "scene.png")
    figure = scene_screenshot_to_report_figure(record)

    lines = _scene_screenshot_provenance_lines(figure.metadata)
    rendered = "\n".join(lines)

    assert lines == _scene_screenshot_provenance_lines(figure.metadata)
    assert "Active scene: osw.active_scene.v1" in rendered
    assert "Mesh fingerprint: bbbbbbbbbbbb…" in rendered
    assert "Scalar: stress / von_mises / cell" in rendered
    assert "Display range: 0 / 250" in rendered
    assert "Named selections: 1 visible / 1 active" in rendered
    assert "Setup overlays: 1 visible" in rendered
    assert "Mesh Diagnostics: osw.mesh_quality.edge_aspect_ratio.v1 / threshold 8" in rendered
    assert "Vector glyphs: disp" in rendered
    assert "Deformed shape: DEFORMED / disp" in rendered
    assert "Representation: surface_with_edges" in rendered
    assert "Capture backend: fake-current-session" in rendered
    assert str(tmp_path) not in rendered


def test_missing_or_unresolved_image_keeps_placeholder_and_provenance() -> None:
    from osw.core.report_asset import ReportAssetPathKind
    from osw.post.report_generator import render_scene_screenshot_section
    from osw.post.report_model import scene_screenshot_to_report_figure

    record = _record(Path("missing.png"))
    payload = record.to_dict()
    payload["path"] = "screenshots/missing.png"
    record = record.__class__(
        **{
            **payload,
            "path_kind": ReportAssetPathKind.PROJECT_RELATIVE.value,
        }
    )
    figure = scene_screenshot_to_report_figure(record)
    html = render_scene_screenshot_section((figure,))

    assert "metadata only" in html
    assert "Active scene: osw.active_scene.v1" in html
    assert "local report artifact only" in html


def test_report_build_consumes_persisted_asset_without_capture_side_effect(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from osw.core.project_schema import Project, ProjectMetadata
    from osw.post import report_generator
    from osw.post.report_model import (
        ReportBuildRequest,
        scene_screenshot_to_report_asset,
    )

    image = tmp_path / "scene.png"
    image.write_bytes(b"\x89PNG\r\n\x1a\n")
    asset = scene_screenshot_to_report_asset(_record(image))
    project = Project(
        metadata=ProjectMetadata(name="Persisted report"),
        report_screenshots=(asset,),
    )
    capture_calls: list[object] = []
    monkeypatch.setattr(
        report_generator,
        "render_scene_screenshot_section",
        (
            lambda figures, **kwargs: (
                capture_calls.append(tuple(figures)) or "<section>persisted</section>"
            )
        ),
    )

    result = report_generator.build_report(
        ReportBuildRequest(
            project=project,
            output_path=tmp_path / "report.html",
            format="html",
        ),
        scene_screenshots=(),
    )

    assert result.ok
    assert capture_calls == [()]
    source = Path(report_generator.__file__).read_text(encoding="utf-8")
    assert "capture_active_scene_screenshot" not in source
    assert image.read_bytes() == b"\x89PNG\r\n\x1a\n"
