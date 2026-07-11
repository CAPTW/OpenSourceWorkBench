"""Unit tests for the PyVista-free 3D Workspace scene data contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.core.report_asset import ReportAssetPathKind
from osw.post.pyvista_scene import PyVistaSceneConfig
from osw.post.scene_model import (
    SceneCameraState,
    SceneInputRef,
    SceneRenderOptions,
    SceneScreenshotRecord,
    SceneViewState,
    build_screenshot_record,
)


def test_scene_camera_state_default_roundtrip() -> None:
    camera = SceneCameraState()
    assert SceneCameraState.from_dict(camera.to_dict()) == camera
    assert not camera.validate().has_errors

    populated = SceneCameraState(
        position=[1.0, 2.0, 3.0],
        focal_point=(0.0, 0.0, 0.0),
        view_up=(0.0, 0.0, 1.0),
        parallel_projection=True,
        parallel_scale=2.5,
        view_preset="iso",
    )
    assert populated.position == (1.0, 2.0, 3.0)
    restored = SceneCameraState.from_dict(json.loads(json.dumps(populated.to_dict())))
    assert restored == populated


def test_scene_camera_state_invalid_tuple_and_scale() -> None:
    # A wrong-length vector is rejected at construction time.
    with pytest.raises(ValueError, match="exactly three"):
        SceneCameraState(position=[1.0, 2.0])
    # Non-finite vector and non-positive scale are validation errors.
    assert SceneCameraState(position=(float("inf"), 0.0, 0.0)).validate().has_errors
    assert SceneCameraState(parallel_scale=-1.0).validate().has_errors
    # Unknown view preset is a warning, not an error.
    report = SceneCameraState(view_preset="spinny").validate()
    assert report.has_warnings and not report.has_errors


def test_scene_render_options_size_validation_and_config_mapping() -> None:
    options = SceneRenderOptions(
        show_edges=True, color_by="temperature", screenshot_size=(640, 480)
    )
    assert SceneRenderOptions.from_dict(options.to_dict()) == options
    assert not options.validate().has_errors

    # Zero/negative dimensions are a validation error.
    assert SceneRenderOptions(screenshot_size=(0, 480)).validate().has_errors
    with pytest.raises(ValueError, match="exactly two"):
        SceneRenderOptions(screenshot_size=(640,))

    # Mapping to the existing PyVistaSceneConfig is lossless for shared toggles.
    config = options.to_pyvista_config()
    assert isinstance(config, PyVistaSceneConfig)
    assert config.show_edges is True
    assert config.scalar_field == "temperature"
    assert config.off_screen is True
    assert options.to_pyvista_config_dict()["scalar_field"] == "temperature"


def test_scene_view_state_roundtrip() -> None:
    state = SceneViewState(
        camera=SceneCameraState(view_preset="xy"),
        render_options=SceneRenderOptions(show_grid=True),
        selected_selection_ids=["sel-2", "sel-1"],
        scalar_field_id="temperature",
    )
    # selection id order is preserved.
    assert state.selected_selection_ids == ("sel-2", "sel-1")
    restored = SceneViewState.from_dict(json.loads(json.dumps(state.to_dict())))
    assert restored == state
    assert not state.validate().has_errors
    # Empty state is valid.
    assert not SceneViewState().validate().has_errors


def test_scene_screenshot_record_roundtrip_and_required_fields() -> None:
    record = build_screenshot_record(
        "artifacts/scene/shot.png",
        record_id="shot-1",
        scene_state=SceneViewState(scalar_field_id="temperature"),
        caption="Iso view",
        dataset_ref="ds-1",
        mesh_ref="mesh-1",
        selection_ids=["sel-1"],
    )
    assert SceneScreenshotRecord.from_dict(record.to_dict()) == record
    assert not record.validate().has_errors

    missing = SceneScreenshotRecord(id="", path="")
    report = missing.validate()
    assert report.has_errors
    paths = {message.path for message in report.messages}
    assert any(path.endswith(".id") for path in paths)
    assert any(path.endswith(".path") for path in paths)


def test_scene_screenshot_record_preserves_omitted_and_explicit_path_kind() -> None:
    omitted = SceneScreenshotRecord(id="omitted", path="legacy.png")
    explicit = SceneScreenshotRecord(
        id="typed",
        path="screenshots/scene.png",
        path_kind=ReportAssetPathKind.PROJECT_RELATIVE,
    )

    assert omitted.path_kind is None
    assert "path_kind" not in omitted.to_dict()
    assert explicit.to_dict()["path_kind"] == "project_relative"
    assert SceneScreenshotRecord.from_dict(explicit.to_dict()) == explicit


def test_scene_screenshot_path_kind_does_not_shift_legacy_positional_caption() -> None:
    record = SceneScreenshotRecord("shot", "legacy.png", "Caption")

    assert record.path == "legacy.png"
    assert record.caption == "Caption"
    assert record.path_kind is None


@pytest.mark.parametrize(
    "bad_kind", ["", "unknown", "PROJECT_RELATIVE", True, 4, [], {}]
)
def test_scene_screenshot_record_direct_construction_rejects_bad_path_kind(
    bad_kind: object,
) -> None:
    with pytest.raises((TypeError, ValueError), match="path_kind"):
        SceneScreenshotRecord(
            id="shot",
            path="screenshots/scene.png",
            path_kind=bad_kind,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "bad_kind", [None, True, 4, [], {}, "managed_project_asset"]
)
def test_scene_screenshot_record_from_dict_rejects_null_nonstring_and_reserved_kind(
    bad_kind: object,
) -> None:
    payload = SceneScreenshotRecord(id="shot", path="legacy.png").to_dict()
    payload["path_kind"] = bad_kind

    with pytest.raises((TypeError, ValueError), match="path_kind|reserved"):
        SceneScreenshotRecord.from_dict(payload)


@pytest.mark.parametrize("bad_path", [None, True, 4, [], {}, "", "   "])
def test_scene_screenshot_record_from_dict_rejects_malformed_explicit_path(
    bad_path: object,
) -> None:
    payload = {
        "id": "shot",
        "path": bad_path,
        "path_kind": "legacy_raw",
    }

    with pytest.raises((TypeError, ValueError), match="path"):
        SceneScreenshotRecord.from_dict(payload)


@pytest.mark.parametrize(
    ("path_kind", "path"),
    [
        (ReportAssetPathKind.EXTERNAL_ABSOLUTE, "screenshots/scene.png"),
        (ReportAssetPathKind.PROJECT_RELATIVE, "C:/captures/scene.png"),
        (ReportAssetPathKind.LEGACY_RAW, "\x00bad.png"),
    ],
)
def test_scene_screenshot_record_rejects_path_kind_shape_contradictions(
    path_kind: ReportAssetPathKind,
    path: str,
) -> None:
    with pytest.raises(ValueError, match="path"):
        SceneScreenshotRecord(id="shot", path=path, path_kind=path_kind)


def test_build_screenshot_record_remains_unmarked_legacy() -> None:
    record = build_screenshot_record("captures/scene.png", record_id="shot")

    assert record.path_kind is None
    assert "path_kind" not in record.to_dict()


def test_scene_input_ref_field_without_dataset_warns() -> None:
    ok = SceneInputRef(source_kind="mesh", mesh_ref="mesh-1")
    assert not ok.validate().has_warnings and not ok.validate().has_errors

    field_only = SceneInputRef(source_kind="result_field", field_id="temperature")
    assert field_only.validate().has_warnings

    assert SceneInputRef(source_kind="").validate().has_errors
    assert SceneInputRef(source_kind="bogus").validate().has_warnings
    assert SceneInputRef.from_dict(ok.to_dict()) == ok


def test_scene_model_has_no_heavy_or_gui_imports() -> None:
    import osw.post.scene_model as scene_module

    source = Path(scene_module.__file__).read_text(encoding="utf-8")
    forbidden_tokens = (
        "import pyvista",
        "from pyvista ",
        "import vtk",
        "from vtk ",
        "import meshio",
        "from meshio ",
        "PySide6",
        "subprocess",
        "QProcess",
    )
    for forbidden in forbidden_tokens:
        assert forbidden not in source, f"scene_model.py must not reference {forbidden}"
