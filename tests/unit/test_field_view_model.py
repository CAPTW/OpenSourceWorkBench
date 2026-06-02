from __future__ import annotations

import json
from pathlib import Path

from osw.core.result_dataset import ResultDataset, ResultSummaryValue
from osw.mesh.mesh_model import MeshCellBlock, MeshData, MeshInfo, mesh_data_to_model
from osw.post.field_view_model import (
    field_view_model_from_artifacts,
    field_view_model_from_mesh_info,
    field_view_model_from_mesh_model,
    field_view_model_from_result_dataset,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "fields"


def test_mesh_info_field_names_become_viewer_ready_arrays() -> None:
    mesh_info = MeshInfo(
        source_path="mesh.vtu",
        format="vtu",
        node_count=8,
        element_count=1,
        cell_blocks=(MeshCellBlock("hexahedron", count=1),),
        point_data_names=("temperature",),
        cell_data_names=("von_mises",),
    )

    view_model = field_view_model_from_mesh_info(mesh_info)

    assert view_model.dataset_id == "mesh"
    assert view_model.scalar_fields == ("temperature", "von_mises")
    assert view_model.empty_state_message == ""
    assert view_model.default_render_request.scalar_field == "temperature"


def test_mesh_model_preserves_in_memory_mesh_for_optional_rendering() -> None:
    mesh_data = MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        point_data={
            "temperature": (300.0, 310.0, 305.0),
            "velocity": ((1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        },
    )
    mesh_model = mesh_data_to_model(mesh_data, source="mesh.vtk", mesh_format="vtk")

    view_model = field_view_model_from_mesh_model(mesh_model)

    assert view_model.mesh_data is not None
    assert view_model.scalar_fields == ("temperature",)
    assert view_model.vector_fields == ("velocity",)
    assert view_model.default_render_request.scalar_field == "temperature"


def test_result_dataset_metadata_becomes_field_view_model() -> None:
    dataset = ResultDataset.from_dict(
        json.loads((FIXTURES / "scalar_field_dataset.json").read_text(encoding="utf-8"))
    )

    view_model = field_view_model_from_result_dataset(dataset)

    assert view_model.dataset_id == "scalar-field"
    assert view_model.title == "Tiny Scalar Field"
    assert view_model.scalar_fields == ("temperature",)
    assert view_model.vector_fields == ("velocity",)
    assert view_model.artifacts[0].exists


def test_summary_only_dataset_gets_friendly_empty_state() -> None:
    dataset = ResultDataset(
        dataset_id="calculix-summary",
        source="summary.json",
        solver="CalculiX",
        analysis_type="linear_static_summary",
        summaries=(ResultSummaryValue("max_displacement", 0.1, "m", "U"),),
    )

    view_model = field_view_model_from_result_dataset(dataset)

    assert view_model.arrays == ()
    assert "No mesh field arrays" in view_model.empty_state_message


def test_artifact_view_model_inspects_directory_metadata() -> None:
    view_model = field_view_model_from_artifacts(FIXTURES)

    assert view_model.dataset_id == "field-artifacts"
    assert "temperature" in view_model.scalar_fields
    assert any(artifact.path.endswith("tiny_scalar.vtk") for artifact in view_model.artifacts)
