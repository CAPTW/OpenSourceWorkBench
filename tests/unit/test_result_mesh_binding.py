from __future__ import annotations

from osw.core.project_schema import Project, ProjectMetadata, ResultRef
from osw.core.result_mesh_binding import (
    MESH_BINDING_METADATA_KEY,
    RESULT_MESH_BINDING_SCHEMA,
    SOURCE_MESH_REF_METADATA_KEY,
    ResultMeshBinding,
    ResultMeshSignature,
    check_result_mesh_binding,
    result_mesh_binding_from_metadata,
    result_ref_with_mesh_binding,
)


def test_binding_metadata_payload_round_trips() -> None:
    binding = ResultMeshBinding(
        mesh_ref="mesh-1",
        result_dataset_id="dataset-1",
        field_id="temperature",
        association_policy="explicit_user_confirmed",
        status="bound",
        mesh_signature=ResultMeshSignature(node_count=4, cell_count=1),
        diagnostics=("user selected active mesh",),
    )

    payload = binding.to_dict()

    assert payload["schema"] == RESULT_MESH_BINDING_SCHEMA
    assert payload["mesh_ref"] == "mesh-1"
    assert payload["result_dataset_id"] == "dataset-1"
    assert payload["field_id"] == "temperature"
    assert payload["association_policy"] == "explicit_user_confirmed"
    assert payload["status"] == "bound"
    assert payload["mesh_signature"] == {"node_count": 4, "cell_count": 1}
    assert payload["diagnostics"] == ["user selected active mesh"]
    assert ResultMeshBinding.from_dict(payload) == binding


def test_result_ref_binding_copy_preserves_metadata_and_original_ref() -> None:
    ref = ResultRef(
        ref_id="result-1",
        path="results/result.json",
        kind="result_dataset",
        metadata={"keep": "unchanged"},
    )
    binding = ResultMeshBinding(
        mesh_ref="mesh-1",
        result_dataset_id="dataset-1",
        field_id="temperature",
    )

    bound = result_ref_with_mesh_binding(ref, binding)

    assert bound is not ref
    assert bound.id == ref.id
    assert bound.metadata["keep"] == "unchanged"
    assert bound.metadata[SOURCE_MESH_REF_METADATA_KEY] == "mesh-1"
    assert bound.metadata[MESH_BINDING_METADATA_KEY]["schema"] == RESULT_MESH_BINDING_SCHEMA
    assert bound.metadata[MESH_BINDING_METADATA_KEY]["mesh_ref"] == "mesh-1"
    assert MESH_BINDING_METADATA_KEY not in ref.metadata
    assert SOURCE_MESH_REF_METADATA_KEY not in ref.metadata


def test_result_mesh_binding_from_metadata_returns_binding() -> None:
    binding = ResultMeshBinding(
        mesh_ref="mesh-1",
        result_dataset_id="dataset-1",
        field_id="temperature",
    )
    ref = result_ref_with_mesh_binding(
        ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset"),
        binding,
    )

    restored = result_mesh_binding_from_metadata(ref.metadata)

    assert restored == binding


def test_check_rejects_missing_mesh_ref_with_diagnostic() -> None:
    binding = ResultMeshBinding(mesh_ref="", result_dataset_id="dataset-1")

    result = check_result_mesh_binding(binding, active_mesh_ref="mesh-1")

    assert result.valid is False
    assert result.stale is False
    assert any("mesh ref" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_check_rejects_malformed_binding_metadata_with_diagnostic() -> None:
    result = check_result_mesh_binding(
        {MESH_BINDING_METADATA_KEY: "not a mapping"},
        active_mesh_ref="mesh-1",
    )

    assert result.valid is False
    assert result.binding is None
    assert any("malformed" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_check_reports_active_mesh_ref_mismatch_as_stale() -> None:
    binding = ResultMeshBinding(mesh_ref="mesh-1", result_dataset_id="dataset-1")

    result = check_result_mesh_binding(binding, active_mesh_ref="mesh-2")

    assert result.valid is False
    assert result.stale is True
    assert any("active mesh" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_check_reports_node_count_mismatch_as_stale() -> None:
    binding = ResultMeshBinding(
        mesh_ref="mesh-1",
        result_dataset_id="dataset-1",
        mesh_signature=ResultMeshSignature(node_count=4, cell_count=1),
    )

    result = check_result_mesh_binding(binding, active_mesh_ref="mesh-1", node_count=5)

    assert result.valid is False
    assert result.stale is True
    assert any("node count" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_check_reports_cell_count_mismatch_as_stale() -> None:
    binding = ResultMeshBinding(
        mesh_ref="mesh-1",
        result_dataset_id="dataset-1",
        mesh_signature=ResultMeshSignature(node_count=4, cell_count=1),
    )

    result = check_result_mesh_binding(binding, active_mesh_ref="mesh-1", cell_count=2)

    assert result.valid is False
    assert result.stale is True
    assert any("cell count" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_project_result_ref_metadata_round_trips_without_schema_bump() -> None:
    binding = ResultMeshBinding(
        mesh_ref="mesh-1",
        result_dataset_id="dataset-1",
        field_id="temperature",
        mesh_signature=ResultMeshSignature(node_count=4, cell_count=1),
    )
    bound = result_ref_with_mesh_binding(
        ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset"),
        binding,
    )
    project = Project(metadata=ProjectMetadata(name="binding-test"), results=[bound])

    restored = Project.from_dict(project.to_dict())

    assert restored.schema_version == project.schema_version
    assert restored.results[0].metadata[SOURCE_MESH_REF_METADATA_KEY] == "mesh-1"
    assert restored.results[0].metadata[MESH_BINDING_METADATA_KEY]["schema"] == (
        RESULT_MESH_BINDING_SCHEMA
    )
    assert result_mesh_binding_from_metadata(restored.results[0].metadata) == binding
