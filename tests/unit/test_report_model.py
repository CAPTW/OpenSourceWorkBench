from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.core.demo_project import create_heatsink_flow_demo_project
from osw.core.diagnostics import DiagnosticReport
from osw.core.report_asset import ReportAssetPathKind
from osw.post.report_generator import render_scene_screenshot_section
from osw.post.report_model import (
    SCENE_SCREENSHOT_ARTIFACT_CAVEAT,
    ReportAsset,
    ReportBuildRequest,
    ReportBuildResult,
    ReportFigure,
    ReportFormat,
    ReportSection,
    ReportSummary,
    ReportTable,
    report_asset_to_scene_screenshot,
    scene_screenshot_to_report_asset,
    scene_screenshot_to_report_figure,
    scene_screenshots_to_report_figures,
)
from osw.post.scene_model import (
    SceneGlyphOptions,
    SceneRenderOptions,
    SceneScreenshotRecord,
    SceneViewState,
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


def _full_screenshot_record(
    path: str,
    *,
    path_kind: ReportAssetPathKind | None = None,
) -> SceneScreenshotRecord:
    return SceneScreenshotRecord(
        id="shot-1",
        path=path,
        caption="Iso temperature view",
        scene_state=SceneViewState(
            render_options=SceneRenderOptions(show_edges=True, color_by="temperature"),
            glyph_options=SceneGlyphOptions(
                enabled=True, vector_field="U", scale=2.5, max_glyph_count=50
            ),
            scalar_field_id="temperature",
            selected_selection_ids=("sel-a",),
        ),
        dataset_ref="rd-1",
        mesh_ref="mesh-1",
        selection_ids=("sel-a", "sel-b"),
        created_by="mesh-viewer",
        metadata={"note": "captured for report"},
        path_kind=path_kind,
    )


def test_scene_screenshot_to_report_figure_preserves_provenance() -> None:
    figure = scene_screenshot_to_report_figure(_full_screenshot_record("scenes/iso.png"))

    assert figure.figure_id == "shot-1"
    assert figure.title == "Iso temperature view"
    assert figure.caption == "Iso temperature view"
    assert figure.image_path == "scenes/iso.png"
    assert figure.primary_path == "scenes/iso.png"
    assert figure.format == "png"
    # No filesystem check happens in the pure bridge, so no missing-path warning.
    assert figure.diagnostics.warnings() == []

    metadata = figure.metadata
    assert metadata["kind"] == "scene_screenshot"
    assert metadata["screenshot_id"] == "shot-1"
    assert metadata["mesh_ref"] == "mesh-1"
    assert metadata["result_dataset_ref"] == "rd-1"
    assert metadata["scalar_field_id"] == "temperature"
    assert metadata["vector_field"] == "U"
    assert metadata["glyph_enabled"] is True
    assert metadata["glyph_scale"] == 2.5
    assert metadata["glyph_max_count"] == 50
    # record.selection_ids takes priority over the scene view selection ids.
    assert metadata["selection_ids"] == ["sel-a", "sel-b"]
    assert metadata["render_options"]["show_edges"] is True
    assert metadata["glyph_options"]["vector_field"] == "U"
    assert metadata["created_by"] == "mesh-viewer"
    assert metadata["scene_metadata"] == {"note": "captured for report"}
    # Explicit local-artifact caveat and non-release / non-validation flags.
    assert metadata["artifact_caveat"] == SCENE_SCREENSHOT_ARTIFACT_CAVEAT
    assert metadata["is_release_asset"] is False
    assert metadata["is_validation_evidence"] is False
    assert "path_kind" not in metadata


def test_scene_screenshot_report_figure_round_trips_through_dict() -> None:
    figure = scene_screenshot_to_report_figure(_full_screenshot_record("scenes/iso.png"))

    loaded = ReportFigure.from_dict(json.loads(json.dumps(figure.to_dict())))

    assert loaded == figure


def test_scene_screenshot_to_report_figure_metadata_only_warns() -> None:
    record = SceneScreenshotRecord(id="meta-only", path="", caption="No image yet")

    figure = scene_screenshot_to_report_figure(record)

    assert figure.figure_id == "meta-only"
    # ReportFigure normalizes an absent path to an empty string.
    assert figure.image_path == ""
    assert figure.primary_path == ""
    warnings = figure.diagnostics.warnings()
    assert len(warnings) == 1
    assert warnings[0].code == "report-scene-screenshot-path-missing"
    assert figure.metadata["glyph_enabled"] is False
    assert figure.metadata["selection_ids"] == []


def test_explicit_legacy_raw_report_figure_keeps_existing_path_behavior() -> None:
    figure = scene_screenshot_to_report_figure(
        _full_screenshot_record(
            "legacy/../scene.png",
            path_kind=ReportAssetPathKind.LEGACY_RAW,
        )
    )

    assert figure.primary_path == "legacy/../scene.png"
    assert figure.diagnostics.warnings() == []
    assert figure.metadata["path_kind"] == "legacy_raw"


@pytest.mark.parametrize(
    ("path_kind", "stored_path"),
    [
        (ReportAssetPathKind.EXTERNAL_ABSOLUTE, "C:/private/captures/scene.png"),
        (ReportAssetPathKind.PROJECT_RELATIVE, "screenshots/private-scene.png"),
    ],
)
def test_classified_nonlegacy_report_figure_is_unresolved_without_path_leak_or_probe(
    monkeypatch: pytest.MonkeyPatch,
    path_kind: ReportAssetPathKind,
    stored_path: str,
) -> None:
    def unexpected_exists(*args: object, **kwargs: object) -> bool:
        raise AssertionError("classified raw paths must not reach Path.exists")

    monkeypatch.setattr(Path, "exists", unexpected_exists)
    record = _full_screenshot_record(stored_path, path_kind=path_kind)

    figure = scene_screenshot_to_report_figure(record)
    summary = ReportSummary(
        title="Safe report",
        project_name="Project",
        figures=(figure,),
    )

    assert figure.image_path == ""
    assert figure.primary_path == ""
    assert figure.metadata["path_status"] == "unresolved_no_resolver"
    assert figure.metadata["path_kind"] == path_kind.value
    warnings = figure.diagnostics.warnings()
    assert len(warnings) == 1
    assert warnings[0].code == "report-scene-screenshot-path-unresolved-no-resolver"
    assert record.id in warnings[0].message
    assert path_kind.value in warnings[0].message
    serialized = json.dumps(summary.to_dict(), sort_keys=True)
    html = render_scene_screenshot_section((figure,))
    assert stored_path not in serialized
    assert stored_path not in html
    assert stored_path not in figure.diagnostics.summary()


def test_scene_screenshot_selection_ids_fall_back_to_scene_state() -> None:
    record = SceneScreenshotRecord(
        id="shot-3",
        path="scenes/a.png",
        scene_state=SceneViewState(selected_selection_ids=("scene-sel",)),
    )

    figure = scene_screenshot_to_report_figure(record)

    assert figure.metadata["selection_ids"] == ["scene-sel"]


def test_scene_screenshots_to_report_figures_bridges_all() -> None:
    figures = scene_screenshots_to_report_figures(
        [
            _full_screenshot_record("scenes/iso.png"),
            SceneScreenshotRecord(id="shot-2", path="scenes/top.png"),
        ]
    )

    assert [figure.figure_id for figure in figures] == ["shot-1", "shot-2"]
    assert scene_screenshots_to_report_figures(()) == ()


def test_scene_screenshot_report_asset_bridge_round_trips() -> None:
    record = _full_screenshot_record("scenes/iso.png")

    asset = scene_screenshot_to_report_asset(record)

    assert asset.id == "shot-1"
    assert asset.path == "scenes/iso.png"
    assert asset.caption == "Iso temperature view"
    assert asset.mesh_ref == "mesh-1"
    assert asset.result_dataset_ref == "rd-1"
    assert asset.field_id == "temperature"
    assert asset.selection_ids == ("sel-a", "sel-b")
    assert asset.glyph_options["vector_field"] == "U"
    # Persisted asset is never a release asset / validation evidence.
    assert asset.metadata["is_release_asset"] is False
    assert asset.metadata["is_validation_evidence"] is False

    back = report_asset_to_scene_screenshot(asset)

    assert back.id == record.id
    assert back.path == record.path
    assert back.caption == record.caption
    assert back.mesh_ref == record.mesh_ref
    assert back.dataset_ref == record.dataset_ref
    assert back.selection_ids == record.selection_ids
    assert back.created_by == record.created_by
    assert back.scene_state.glyph_options.vector_field == "U"
    assert back.scene_state.scalar_field_id == "temperature"


@pytest.mark.parametrize(
    ("path_kind", "path"),
    [
        (None, "legacy.png"),
        (ReportAssetPathKind.LEGACY_RAW, "legacy/../scene.png"),
        (ReportAssetPathKind.EXTERNAL_ABSOLUTE, "C:/captures/scene.png"),
        (ReportAssetPathKind.PROJECT_RELATIVE, "screenshots/scene.png"),
    ],
)
def test_core_post_asset_bridge_preserves_path_kind_omission_and_provenance(
    path_kind: ReportAssetPathKind | None,
    path: str,
) -> None:
    record = _full_screenshot_record(path, path_kind=path_kind)

    asset = scene_screenshot_to_report_asset(record)
    restored = report_asset_to_scene_screenshot(asset)

    assert asset.path == path
    assert asset.path_kind is path_kind
    assert restored.path == path
    assert restored.path_kind is path_kind
    assert restored.scene_state == record.scene_state
    assert restored.selection_ids == record.selection_ids
    assert asset.metadata["artifact_caveat"]
    assert asset.metadata["is_release_asset"] is False
    if path_kind is None:
        assert "path_kind" not in asset.to_dict()
    else:
        assert asset.to_dict()["path_kind"] == path_kind.value
