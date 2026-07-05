"""Unit tests for the PyVista-free 3D Workspace scene data contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

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
