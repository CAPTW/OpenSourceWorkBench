from __future__ import annotations

from osw.core.project_schema import Project, ProjectMetadata, ResultRef
from osw.core.result_dataset import ResultDataset
from osw.core.result_mesh_binding import (
    MESH_BINDING_METADATA_KEY,
    RESULT_MESH_BINDING_SCHEMA,
    SOURCE_MESH_REF_METADATA_KEY,
    ResultMeshBinding,
    ResultMeshSignature,
    bridge_result_dataset_mesh_binding,
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


def test_bridge_explicit_context_creates_bound_result_ref_copy() -> None:
    ref = ResultRef(
        ref_id="result-1",
        path="results/result.json",
        kind="result_dataset",
        metadata={"keep": "unchanged"},
    )

    result = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id="dataset-1",
        mesh_ref="mesh-1",
        field_id="temperature",
        node_count=4,
        cell_count=1,
    )

    assert result.valid is True
    assert result.binding == ResultMeshBinding(
        mesh_ref="mesh-1",
        result_dataset_id="dataset-1",
        field_id="temperature",
        mesh_signature=ResultMeshSignature(node_count=4, cell_count=1),
    )
    assert result.result_ref is not ref
    assert result.result_ref.metadata["keep"] == "unchanged"
    assert result.result_ref.metadata[SOURCE_MESH_REF_METADATA_KEY] == "mesh-1"
    assert result.result_ref.metadata[MESH_BINDING_METADATA_KEY]["schema"] == (
        RESULT_MESH_BINDING_SCHEMA
    )
    assert ref.metadata == {"keep": "unchanged"}


def test_bridge_uses_unambiguous_result_dataset_metadata_as_proposal_only() -> None:
    dataset = ResultDataset(
        dataset_id="dataset-1",
        source="memory",
        solver="",
        analysis_type="static",
        metadata={SOURCE_MESH_REF_METADATA_KEY: "mesh-1"},
    )
    original_metadata = dict(dataset.metadata)
    ref = ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset")

    result = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id=dataset.dataset_id,
        proposal_metadata=dataset.metadata,
        node_count=4,
        cell_count=1,
    )

    assert result.valid is True
    assert result.binding is not None
    assert result.binding.mesh_ref == "mesh-1"
    assert result.result_ref.metadata[SOURCE_MESH_REF_METADATA_KEY] == "mesh-1"
    assert dataset.metadata == original_metadata
    assert MESH_BINDING_METADATA_KEY not in dataset.metadata


def test_bridge_rejects_ambiguous_proposal_metadata_without_binding() -> None:
    ref = ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset")

    result = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id="dataset-1",
        proposal_metadata={"mesh_ref": ["mesh-1", "mesh-2"]},
        node_count=4,
        cell_count=1,
    )

    assert result.valid is False
    assert result.binding is None
    assert result.result_ref is ref
    assert any("ambiguous" in diagnostic.lower() for diagnostic in result.diagnostics)
    assert MESH_BINDING_METADATA_KEY not in ref.metadata


def test_bridge_rejects_proposal_metadata_mismatch_without_binding() -> None:
    ref = ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset")

    result = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id="dataset-1",
        mesh_ref="mesh-1",
        proposal_metadata={SOURCE_MESH_REF_METADATA_KEY: "mesh-2"},
        node_count=4,
        cell_count=1,
    )

    assert result.valid is False
    assert result.binding is None
    assert any("does not match" in diagnostic.lower() for diagnostic in result.diagnostics)
    assert MESH_BINDING_METADATA_KEY not in ref.metadata


def test_bridge_rejects_missing_mesh_ref_with_friendly_diagnostic() -> None:
    ref = ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset")

    result = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id="dataset-1",
        node_count=4,
        cell_count=1,
    )

    assert result.valid is False
    assert result.binding is None
    assert any("mesh ref" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_bridge_rejects_missing_dataset_id_with_friendly_diagnostic() -> None:
    ref = ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset")

    result = bridge_result_dataset_mesh_binding(ref, result_dataset_id="", mesh_ref="mesh-1")

    assert result.valid is False
    assert result.binding is None
    assert any("dataset id" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_bridge_reports_missing_count_signature_caveat_without_blocking() -> None:
    ref = ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset")

    result = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id="dataset-1",
        mesh_ref="mesh-1",
    )

    assert result.valid is True
    assert result.binding is not None
    assert result.binding.mesh_signature.has_counts is False
    assert any("signature" in diagnostic.lower() for diagnostic in result.diagnostics)
    assert "mesh_signature" not in result.result_ref.metadata[MESH_BINDING_METADATA_KEY]


def test_bridge_can_require_field_id_for_field_specific_binding() -> None:
    ref = ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset")

    result = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id="dataset-1",
        mesh_ref="mesh-1",
        node_count=4,
        cell_count=1,
        require_field_id=True,
    )

    assert result.valid is False
    assert result.binding is None
    assert any("field id" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_bridge_rejects_active_mesh_ref_mismatch_with_diagnostic() -> None:
    ref = ResultRef(ref_id="result-1", path="results/result.json", kind="result_dataset")

    result = bridge_result_dataset_mesh_binding(
        ref,
        result_dataset_id="dataset-1",
        mesh_ref="mesh-1",
        active_mesh_ref="mesh-2",
        node_count=4,
        cell_count=1,
    )

    assert result.valid is False
    assert result.binding is None
    assert any("active mesh" in diagnostic.lower() for diagnostic in result.diagnostics)


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


def test_check_rejects_malformed_diagnostics_payload_with_diagnostic() -> None:
    result = check_result_mesh_binding(
        {
            MESH_BINDING_METADATA_KEY: {
                "schema": RESULT_MESH_BINDING_SCHEMA,
                "mesh_ref": "mesh-1",
                "result_dataset_id": "dataset-1",
                "diagnostics": 5,
            },
        },
        active_mesh_ref="mesh-1",
    )

    assert result.valid is False
    assert result.binding is None
    assert any("malformed" in diagnostic.lower() for diagnostic in result.diagnostics)
    assert any("diagnostics" in diagnostic.lower() for diagnostic in result.diagnostics)


def test_check_rejects_unsupported_schema_with_diagnostic() -> None:
    result = check_result_mesh_binding(
        {
            "schema": "osw.result_mesh_binding.v2",
            "mesh_ref": "mesh-1",
            "result_dataset_id": "dataset-1",
        },
        active_mesh_ref="mesh-1",
    )

    assert result.valid is False
    assert result.binding is None
    assert any("unsupported schema" in diagnostic.lower() for diagnostic in result.diagnostics)


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
