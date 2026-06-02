from __future__ import annotations

import json
from pathlib import Path

from osw.core.result_dataset import ResultDataset
from osw.mesh.mesh_model import MeshBounds, MeshCellBlock, MeshInfo
from osw.post.field_dataset import (
    FieldArraySummary,
    FieldArtifactSummary,
    FieldRenderRequest,
    FieldRenderResult,
    field_dataset_from_result_dataset,
    inspect_field_artifact,
    inspect_field_artifacts,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "fields"


def test_field_summary_models_round_trip() -> None:
    mesh_info = MeshInfo(
        source_path="tiny.vtk",
        format="vtk",
        node_count=4,
        cell_blocks=(MeshCellBlock("triangle", count=2),),
        bounds=MeshBounds(minimum=(0.0, 0.0, 0.0), maximum=(1.0, 1.0, 0.0)),
    )
    array = FieldArraySummary(
        name="temperature",
        location="point",
        field_type="scalar",
        components=("temperature",),
        value_count=4,
        unit="K",
        minimum=295.0,
        maximum=310.0,
    )
    artifact = FieldArtifactSummary(
        path="tiny.vtk",
        format="vtk",
        exists=True,
        size_bytes=128,
        mesh_info=mesh_info,
        arrays=(array,),
    )
    request = FieldRenderRequest(
        dataset_id="scalar-field",
        scalar_field="temperature",
        screenshot_path="artifacts/field/temperature.png",
    )
    result = FieldRenderResult(
        status="placeholder",
        message="No in-memory mesh geometry is attached.",
        request=request,
    )

    assert FieldArraySummary.from_dict(array.to_dict()) == array
    assert FieldArtifactSummary.from_dict(artifact.to_dict()) == artifact
    assert FieldRenderRequest.from_dict(request.to_dict()) == request
    assert FieldRenderResult.from_dict(result.to_dict()).message == result.message
    assert array.is_scalar
    assert not array.is_vector


def test_legacy_vtk_artifact_inspection_extracts_field_metadata() -> None:
    artifact = inspect_field_artifact(FIXTURES / "tiny_scalar.vtk")

    assert artifact.exists
    assert artifact.format == "vtk"
    assert artifact.mesh_info is not None
    assert artifact.mesh_info.node_count == 4
    assert artifact.mesh_info.element_count == 2
    assert {array.name for array in artifact.arrays} == {"temperature", "velocity"}
    assert artifact.scalar_arrays[0].name == "temperature"
    assert artifact.vector_arrays[0].name == "velocity"


def test_missing_field_artifact_reports_friendly_diagnostic(tmp_path: Path) -> None:
    artifact = inspect_field_artifact(tmp_path / "missing.vtu")

    assert not artifact.exists
    assert artifact.diagnostics == ("Missing field artifact: " + str(tmp_path / "missing.vtu"),)
    assert artifact.arrays == ()


def test_result_dataset_field_metadata_converts_to_field_summary() -> None:
    dataset = ResultDataset.from_dict(
        json.loads((FIXTURES / "scalar_field_dataset.json").read_text(encoding="utf-8"))
    )

    field_dataset = field_dataset_from_result_dataset(dataset)

    assert field_dataset.dataset_id == "scalar-field"
    assert field_dataset.title == "Tiny Scalar Field"
    assert field_dataset.mesh_info is not None
    assert field_dataset.mesh_info.node_count == 4
    assert [array.name for array in field_dataset.scalar_arrays] == ["temperature"]
    assert [array.name for array in field_dataset.vector_arrays] == ["velocity"]
    assert field_dataset.artifacts[0].exists


def test_field_artifact_directory_inspection_is_read_only() -> None:
    artifacts = inspect_field_artifacts(FIXTURES)

    assert any(artifact.path.endswith("tiny_scalar.vtk") for artifact in artifacts)
    assert all(artifact.role == "field" for artifact in artifacts)


def test_field_cli_inspection_commands_emit_text(capsys: object) -> None:
    from osw.cli.main import main

    assert main(["field-dataset-inspect", str(FIXTURES / "scalar_field_dataset.json")]) == 0
    dataset_output = capsys.readouterr().out
    assert "Field Dataset: Tiny Scalar Field" in dataset_output
    assert "Scalar fields: temperature" in dataset_output

    assert main(["field-artifacts-inspect", str(FIXTURES)]) == 0
    artifact_output = capsys.readouterr().out
    assert "Field artifacts" in artifact_output
    assert "tiny_scalar.vtk" in artifact_output
