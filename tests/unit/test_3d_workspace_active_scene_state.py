"""Pure active-scene persistence and additive ProjectSchema tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def _workspace_types() -> tuple[object, ...]:
    from osw.core.workspace_3d import (
        ACTIVE_SCENE_SCHEMA,
        ActiveSceneCameraState,
        ActiveSceneClippingState,
        ActiveSceneResultState,
        ActiveSceneState,
        MeshQualityViewState,
        SemanticActorVisibility,
        active_scene_state_digest,
    )

    return (
        ACTIVE_SCENE_SCHEMA,
        ActiveSceneCameraState,
        ActiveSceneClippingState,
        ActiveSceneResultState,
        ActiveSceneState,
        MeshQualityViewState,
        SemanticActorVisibility,
        active_scene_state_digest,
    )


def _state() -> object:
    (
        schema,
        camera_type,
        clipping_type,
        result_type,
        state_type,
        quality_type,
        actor_type,
        _digest,
    ) = _workspace_types()
    return state_type(
        schema=schema,
        mesh_ref="mesh-1",
        mesh_fingerprint="a" * 64,
        camera=camera_type(
            position=(3.0, 2.0, 1.0),
            focal_point=(0.0, 0.0, 0.0),
            view_up=(0.0, 0.0, 1.0),
            parallel_projection=True,
            parallel_scale=2.0,
        ),
        representation="surface_with_edges",
        axes_visible=False,
        actor_visibility=(
            actor_type("wireframe", "mesh-1", visible=True),
            actor_type("base_mesh", "mesh-1", visible=True),
            actor_type("material_assignment", "mat-1", visible=False),
        ),
        visible_named_selection_ids=("selection-2", "selection-1"),
        active_named_selection_ids=("selection-2",),
        result_state=result_type(
            result_ref_id="result-1",
            result_dataset_id="dataset-1",
            binding_schema="osw.result_mesh_binding.v2",
            mesh_fingerprint="a" * 64,
            scalar_field="stress",
            scalar_component="von_mises",
            scalar_association="cell",
            range_mode="MANUAL",
            manual_min=0.0,
            manual_max=10.0,
            colormap="viridis",
            colorbar_visible=True,
        ),
        mesh_quality_state=quality_type(
            metric_schema="osw.mesh_quality.edge_aspect_ratio.v1",
            threshold=10.0,
            highlight_visible=True,
        ),
        clipping_state=clipping_type(
            enabled=True,
            origin=(0.5, 0.0, 0.0),
            normal=(1.0, 0.0, 0.0),
        ),
        selection_mode="cell",
        extensions={"org.opensolver.note": {"value": "보존"}},
    )


def test_active_scene_module_and_schema_contract_exist() -> None:
    assert importlib.util.find_spec("osw.core.workspace_3d") is not None
    schema, *_rest = _workspace_types()
    assert schema == "osw.active_scene.v1"


def test_active_scene_round_trip_and_digest_are_deterministic() -> None:
    (
        _schema,
        _camera,
        _clipping,
        _result,
        state_type,
        _quality,
        _actor,
        digest,
    ) = _workspace_types()
    state = _state()
    payload = state.to_dict()
    restored = state_type.from_dict(json.loads(json.dumps(payload, ensure_ascii=False)))

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    assert restored == state
    assert digest(state) == hashlib.sha256(canonical).hexdigest()
    assert digest(restored) == digest(state)
    assert [item["kind"] for item in payload["actor_visibility"]] == [
        "base_mesh",
        "material_assignment",
        "wireframe",
    ]
    assert payload["visible_named_selection_ids"] == [
        "selection-1",
        "selection-2",
    ]


def test_active_scene_rejects_malformed_camera_clipping_actor_and_extensions() -> None:
    (
        _schema,
        camera_type,
        clipping_type,
        _result_type,
        state_type,
        _quality_type,
        actor_type,
        _digest,
    ) = _workspace_types()

    with pytest.raises(ValueError, match="finite"):
        camera_type(position=(float("nan"), 0.0, 0.0))
    with pytest.raises(ValueError, match="nonzero"):
        clipping_type(enabled=True, normal=(0.0, 0.0, 0.0))
    with pytest.raises(ValueError, match="actor kind"):
        actor_type("native-vtk-actor", "pointer")
    with pytest.raises(ValueError, match="namespaced"):
        state_type(
            mesh_ref="mesh-1",
            mesh_fingerprint="a" * 64,
            extensions={"plain": {"value": 1}},
        )
    with pytest.raises((TypeError, ValueError), match="JSON"):
        state_type(
            mesh_ref="mesh-1",
            mesh_fingerprint="a" * 64,
            extensions={"org.opensolver.bytes": b"not-json"},
        )


@pytest.mark.parametrize("version", ["0.1", "0.2", "0.3"])
def test_legacy_project_without_active_scene_loads_as_none(version: str) -> None:
    from osw.core.project_schema import Project

    project = Project.from_dict(
        {"schema_version": version, "metadata": {"name": f"Legacy {version}"}}
    )

    assert project.active_scene is None
    assert "active_scene" not in project.to_dict()


def test_project_active_scene_is_additive_0_3_and_round_trips() -> None:
    from osw.core.project_schema import Project, ProjectMetadata

    project = Project(metadata=ProjectMetadata(name="Scene"), active_scene=_state())
    payload = project.to_dict()
    restored = Project.from_dict(payload)

    assert project.schema_version == "0.3"
    assert payload["active_scene"]["schema"] == "osw.active_scene.v1"
    assert restored.active_scene == project.active_scene


def test_unknown_active_scene_schema_fails_closed() -> None:
    from osw.core.project_schema import Project
    from osw.core.validation import ProjectSchemaError

    payload = {
        "schema_version": "0.3",
        "metadata": {"name": "Unknown scene"},
        "active_scene": {
            "schema": "osw.active_scene.v99",
            "mesh_ref": "mesh-1",
            "mesh_fingerprint": "a" * 64,
        },
    }

    with pytest.raises(ProjectSchemaError, match="active.scene|Active.scene|active_scene"):
        Project.from_dict(payload)


def test_project_copy_helper_preserves_active_scene_by_default() -> None:
    from osw.core.project_schema import Project, ProjectMetadata, project_with

    project = Project(metadata=ProjectMetadata(name="Before"), active_scene=_state())
    copied = project_with(project, metadata=ProjectMetadata(name="After"))

    assert copied.metadata.name == "After"
    assert copied.active_scene == project.active_scene


def test_workspace_core_module_has_no_gui_renderer_report_or_filesystem_imports() -> None:
    import osw.core.workspace_3d as workspace_module

    source = Path(workspace_module.__file__).read_text(encoding="utf-8")
    forbidden = (
        "PySide6",
        "pyvista",
        "vtk",
        "osw.gui",
        "osw.post",
        "subprocess",
        "pathlib",
        "solver",
    )
    for token in forbidden:
        assert token not in source
