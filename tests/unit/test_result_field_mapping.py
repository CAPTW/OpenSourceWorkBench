"""Qt-free / PyVista-free unit tests for ResultField -> mesh scalar mapping."""

from __future__ import annotations

import ast
from pathlib import Path

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.result_field_mapping import (
    ResultFieldMapping,
    ResultVectorFieldMapping,
    map_result_field_to_mesh,
    map_result_vector_field_to_mesh,
    result_field_names,
)


def _mesh() -> MeshData:
    # 3 nodes, 1 triangle cell.
    return MeshData(
        points=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        cells=(MeshCellBlock("triangle", [[0, 1, 2]]),),
    )


def _node_field(name: str = "temp", *, ids=(0, 1, 2), comp: str = "value") -> ResultField:
    return ResultField(
        name=name,
        location="node",
        components=(comp,),
        rows=tuple(ResultRow(entity_id=i, values={comp: float(i) * 10.0}) for i in ids),
    )


def _vector_field(
    name: str = "U",
    *,
    ids=(0, 1, 2),
    location: str = "node",
    components: tuple[str, ...] = ("Ux", "Uy", "Uz"),
) -> ResultField:
    return ResultField(
        name=name,
        location=location,
        components=components,
        rows=tuple(
            ResultRow(
                entity_id=i,
                values={
                    component: float(index + row_index)
                    for index, component in enumerate(components)
                },
            )
            for row_index, i in enumerate(ids)
        ),
    )


def test_node_field_maps_to_point_data_overlay() -> None:
    mesh = _mesh()
    result = map_result_field_to_mesh(mesh, _node_field("temp"))
    assert isinstance(result, ResultFieldMapping)
    assert result.applied is True
    assert result.location == "point"
    assert result.field_name == "temp"
    assert result.mesh_data.point_data["temp"] == (0.0, 10.0, 20.0)
    assert "temp" not in result.mesh_data.cell_data
    assert "temp" not in mesh.point_data


def test_cell_field_maps_to_cell_data_overlay() -> None:
    field = ResultField(
        name="region", location="cell", components=("id",), rows=(ResultRow(0, {"id": 7.0}),)
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is True
    assert result.location == "cell"
    assert result.mesh_data.cell_data["region"] == (7.0,)
    assert "region" not in result.mesh_data.point_data


def test_one_based_entity_ids_align() -> None:
    result = map_result_field_to_mesh(_mesh(), _node_field("temp", ids=(1, 2, 3)))
    assert result.applied is True
    # id 1 -> index 0, etc; values are 10*id.
    assert result.mesh_data.point_data["temp"] == (10.0, 20.0, 30.0)


def test_length_mismatch_is_not_applied_and_does_not_fabricate() -> None:
    mesh = _mesh()
    result = map_result_field_to_mesh(mesh, _node_field("temp", ids=(0, 1)))
    assert result.applied is False
    assert result.diagnostics and "not applied" in result.diagnostics[0]
    # No fabricated array added; overlay equals the input mesh (no 'temp' key).
    assert "temp" not in result.mesh_data.point_data
    assert "temp" not in mesh.point_data


def test_raw_row_count_mismatch_rejects_duplicate_collapse() -> None:
    field = ResultField(
        name="temp",
        location="node",
        components=("value",),
        rows=(
            ResultRow(0, {"value": 0.0}),
            ResultRow(1, {"value": 10.0}),
            ResultRow(2, {"value": 20.0}),
            ResultRow(2, {"value": 999.0}),
        ),
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "4 rows" in result.diagnostics[0]
    assert "3 nodes" in result.diagnostics[0]
    assert "temp" not in result.mesh_data.point_data


def test_duplicate_entity_ids_are_rejected() -> None:
    field = ResultField(
        name="temp",
        location="node",
        components=("value",),
        rows=(
            ResultRow(0, {"value": 0.0}),
            ResultRow(1, {"value": 10.0}),
            ResultRow(1, {"value": 999.0}),
        ),
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "duplicate entity ID" in result.diagnostics[0]
    assert "temp" not in result.mesh_data.point_data


def test_duplicate_entity_ids_cannot_overwrite_values() -> None:
    field = ResultField(
        name="temp",
        location="node",
        components=("value",),
        rows=(
            ResultRow(0, {"value": 0.0}),
            ResultRow(1, {"value": 10.0}),
            ResultRow(1, {"value": 999.0}),
        ),
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "temp" not in result.mesh_data.point_data


def test_non_contiguous_ids_are_not_applied() -> None:
    result = map_result_field_to_mesh(_mesh(), _node_field("temp", ids=(0, 1, 5)))
    assert result.applied is False
    assert "temp" not in result.mesh_data.point_data


def test_unknown_location_is_not_applied() -> None:
    field = ResultField(
        name="f", location="face", components=("v",), rows=(ResultRow(0, {"v": 1.0}),)
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "unknown location" in result.diagnostics[0]


def test_missing_component_in_a_row_is_not_applied() -> None:
    field = ResultField(
        name="f",
        location="node",
        components=("value",),
        rows=(ResultRow(0, {"value": 1.0}), ResultRow(1, {}), ResultRow(2, {"value": 3.0})),
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "missing" in result.diagnostics[0]


def test_non_coercible_entity_id_is_not_applied() -> None:
    field = ResultField(
        name="temp",
        location="node",
        components=("value",),
        rows=(
            ResultRow(0, {"value": 0.0}),
            ResultRow("node-a", {"value": 10.0}),
            ResultRow(2, {"value": 20.0}),
        ),
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "entity_id" in result.diagnostics[0]
    assert "not applied" in result.diagnostics[0]


def test_non_finite_positive_entity_id_is_not_applied() -> None:
    mesh = _mesh()
    field = ResultField(
        name="temp",
        location="node",
        components=("value",),
        rows=(
            ResultRow(0, {"value": 0.0}),
            ResultRow(float("inf"), {"value": 10.0}),
            ResultRow(2, {"value": 20.0}),
        ),
    )
    result = map_result_field_to_mesh(mesh, field)
    assert result.applied is False
    assert "finite integer" in result.diagnostics[0]
    assert "not applied" in result.diagnostics[0]
    assert "temp" not in result.mesh_data.point_data
    assert "temp" not in mesh.point_data


def test_non_finite_negative_entity_id_is_not_applied() -> None:
    field = ResultField(
        name="temp",
        location="node",
        components=("value",),
        rows=(
            ResultRow(0, {"value": 0.0}),
            ResultRow(float("-inf"), {"value": 10.0}),
            ResultRow(2, {"value": 20.0}),
        ),
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "finite integer" in result.diagnostics[0]


def test_nan_entity_id_is_not_applied() -> None:
    field = ResultField(
        name="temp",
        location="node",
        components=("value",),
        rows=(
            ResultRow(0, {"value": 0.0}),
            ResultRow(float("nan"), {"value": 10.0}),
            ResultRow(2, {"value": 20.0}),
        ),
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "finite integer" in result.diagnostics[0]


def test_non_coercible_component_value_is_not_applied() -> None:
    field = ResultField(
        name="temp",
        location="node",
        components=("value",),
        rows=(
            ResultRow(0, {"value": 0.0}),
            ResultRow(1, {"value": "hot"}),
            ResultRow(2, {"value": 20.0}),
        ),
    )
    result = map_result_field_to_mesh(_mesh(), field)
    assert result.applied is False
    assert "non-numeric value" in result.diagnostics[0]
    assert "not applied" in result.diagnostics[0]


def test_component_selection() -> None:
    field = ResultField(
        name="disp",
        location="node",
        components=("x", "y"),
        rows=tuple(ResultRow(i, {"x": float(i), "y": float(i) + 100.0}) for i in range(3)),
    )
    result = map_result_field_to_mesh(_mesh(), field, component="y")
    assert result.applied is True
    assert result.mesh_data.point_data["disp"] == (100.0, 101.0, 102.0)


def test_component_not_present_is_not_applied() -> None:
    field = ResultField(
        name="disp",
        location="node",
        components=("x", "y"),
        rows=tuple(ResultRow(i, {"x": float(i), "y": 0.0}) for i in range(3)),
    )
    result = map_result_field_to_mesh(_mesh(), field, component="z")
    assert result.applied is False


def test_result_field_names_lists_field_names() -> None:
    dataset = ResultDataset(
        dataset_id="rd",
        source="fixture",
        solver="fake",
        analysis_type="static",
        fields=(_node_field("temp"), _node_field("stress")),
    )
    assert result_field_names(dataset) == ("temp", "stress")
    assert result_field_names(None) == ()


def test_vector_node_field_maps_to_point_data_overlay() -> None:
    mesh = _mesh()
    result = map_result_vector_field_to_mesh(mesh, _vector_field("U"))

    assert isinstance(result, ResultVectorFieldMapping)
    assert result.applied is True
    assert result.location == "point"
    assert result.field_name == "result_vector:U"
    assert result.selected_components == ("Ux", "Uy", "Uz")
    assert result.mesh_data.point_data["result_vector:U"] == (
        (0.0, 1.0, 2.0),
        (1.0, 2.0, 3.0),
        (2.0, 3.0, 4.0),
    )
    assert "result_vector:U" not in result.mesh_data.cell_data
    assert "result_vector:U" not in mesh.point_data


def test_vector_cell_field_maps_to_cell_data_overlay_with_one_based_ids() -> None:
    field = ResultField(
        name="force",
        location="element",
        components=("x", "y", "z"),
        rows=(ResultRow(1, {"x": 10.0, "y": 20.0, "z": 30.0}),),
    )
    result = map_result_vector_field_to_mesh(_mesh(), field)

    assert result.applied is True
    assert result.location == "cell"
    assert result.mesh_data.cell_data["result_vector:force"] == ((10.0, 20.0, 30.0),)
    assert "result_vector:force" not in result.mesh_data.point_data


def test_vector_mapping_accepts_dataset_with_explicit_field_name() -> None:
    dataset = ResultDataset(
        dataset_id="rd",
        source="fixture",
        solver="fake",
        analysis_type="static",
        fields=(_vector_field("U"),),
    )

    result = map_result_vector_field_to_mesh(_mesh(), dataset, field="U")

    assert result.applied is True
    assert result.field_name == "result_vector:U"


def test_vector_mapping_rejects_dataset_without_field_name() -> None:
    dataset = ResultDataset(
        dataset_id="rd",
        source="fixture",
        solver="fake",
        analysis_type="static",
        fields=(_vector_field("U"),),
    )

    result = map_result_vector_field_to_mesh(_mesh(), dataset)

    assert result.applied is False
    assert "field name is required" in result.diagnostics[0]


def test_vector_mapping_rejects_missing_dataset_field() -> None:
    dataset = ResultDataset(
        dataset_id="rd",
        source="fixture",
        solver="fake",
        analysis_type="static",
        fields=(_vector_field("U"),),
    )

    result = map_result_vector_field_to_mesh(_mesh(), dataset, field="V")

    assert result.applied is False
    assert "not found" in result.diagnostics[0]


def test_vector_mapping_explicit_component_selection() -> None:
    field = _vector_field("velocity", components=("vx", "vy", "vz", "magnitude"))

    result = map_result_vector_field_to_mesh(
        _mesh(),
        field,
        components=("vx", "vy", "vz"),
        field_name="custom:velocity",
    )

    assert result.applied is True
    assert result.field_name == "custom:velocity"
    assert result.selected_components == ("vx", "vy", "vz")
    assert result.mesh_data.point_data["custom:velocity"] == (
        (0.0, 1.0, 2.0),
        (1.0, 2.0, 3.0),
        (2.0, 3.0, 4.0),
    )


def test_vector_mapping_recognizes_default_canonical_triple() -> None:
    result = map_result_vector_field_to_mesh(
        _mesh(),
        _vector_field("wind", components=("u", "v", "w")),
    )

    assert result.applied is True
    assert result.selected_components == ("u", "v", "w")


def test_vector_mapping_rejects_ambiguous_default_components() -> None:
    result = map_result_vector_field_to_mesh(
        _mesh(),
        _vector_field("mixed", components=("x", "y", "z", "ux", "uy", "uz")),
    )

    assert result.applied is False
    assert "ambiguous" in result.diagnostics[0]
    assert "result_vector:mixed" not in result.mesh_data.point_data


def test_vector_mapping_rejects_requested_component_missing() -> None:
    result = map_result_vector_field_to_mesh(
        _mesh(),
        _vector_field("velocity", components=("vx", "vy", "speed")),
        components=("vx", "vy", "vz"),
    )

    assert result.applied is False
    assert "missing requested" in result.diagnostics[0]


def test_vector_mapping_rejects_too_few_components() -> None:
    result = map_result_vector_field_to_mesh(
        _mesh(),
        _vector_field("plane", components=("x", "y")),
    )

    assert result.applied is False
    assert "fewer than three" in result.diagnostics[0]
    assert "2D vector padding is deferred" in result.diagnostics[0]


def test_vector_mapping_rejects_too_many_tensor_like_components() -> None:
    result = map_result_vector_field_to_mesh(
        _mesh(),
        _vector_field("tensor", components=("xx", "xy", "yx", "yy")),
    )

    assert result.applied is False
    assert "more than three" in result.diagnostics[0]


def test_vector_mapping_rejects_wrong_explicit_component_count() -> None:
    result = map_result_vector_field_to_mesh(
        _mesh(),
        _vector_field("U"),
        components=("Ux", "Uy"),
    )

    assert result.applied is False
    assert "exactly three" in result.diagnostics[0]


def test_vector_mapping_rejects_duplicate_entity_ids() -> None:
    result = map_result_vector_field_to_mesh(_mesh(), _vector_field("U", ids=(0, 1, 1)))

    assert result.applied is False
    assert "duplicate entity ID" in result.diagnostics[0]
    assert "result_vector:U" not in result.mesh_data.point_data


def test_vector_mapping_raw_row_count_mismatch_rejects_duplicate_collapse() -> None:
    result = map_result_vector_field_to_mesh(_mesh(), _vector_field("U", ids=(0, 1, 2, 2)))

    assert result.applied is False
    assert "4 rows" in result.diagnostics[0]
    assert "3 nodes" in result.diagnostics[0]
    assert "result_vector:U" not in result.mesh_data.point_data


def test_vector_mapping_rejects_non_finite_entity_ids() -> None:
    result = map_result_vector_field_to_mesh(
        _mesh(),
        _vector_field("U", ids=(0, float("inf"), 2)),
    )

    assert result.applied is False
    assert "finite integer" in result.diagnostics[0]


def test_vector_mapping_rejects_fractional_entity_ids() -> None:
    result = map_result_vector_field_to_mesh(_mesh(), _vector_field("U", ids=(0, 1.5, 2)))

    assert result.applied is False
    assert "finite integer" in result.diagnostics[0]


def test_vector_mapping_rejects_non_coercible_entity_ids() -> None:
    result = map_result_vector_field_to_mesh(_mesh(), _vector_field("U", ids=(0, "node-a", 2)))

    assert result.applied is False
    assert "finite integer" in result.diagnostics[0]


def test_vector_mapping_rejects_non_numeric_component_values() -> None:
    field = _vector_field("U")
    bad_rows = (
        ResultRow(0, {"Ux": 0.0, "Uy": 1.0, "Uz": 2.0}),
        ResultRow(1, {"Ux": "fast", "Uy": 2.0, "Uz": 3.0}),
        ResultRow(2, {"Ux": 2.0, "Uy": 3.0, "Uz": 4.0}),
    )
    bad_field = ResultField(
        name=field.name, location=field.location, components=field.components, rows=bad_rows
    )

    result = map_result_vector_field_to_mesh(_mesh(), bad_field)

    assert result.applied is False
    assert "non-numeric or non-finite value" in result.diagnostics[0]


def test_vector_mapping_rejects_non_finite_component_values_and_does_not_mutate() -> None:
    mesh = _mesh()
    field = _vector_field("U")
    bad_rows = (
        ResultRow(0, {"Ux": 0.0, "Uy": 1.0, "Uz": 2.0}),
        ResultRow(1, {"Ux": float("nan"), "Uy": 2.0, "Uz": 3.0}),
        ResultRow(2, {"Ux": 2.0, "Uy": 3.0, "Uz": 4.0}),
    )
    bad_field = ResultField(
        name=field.name, location=field.location, components=field.components, rows=bad_rows
    )

    result = map_result_vector_field_to_mesh(mesh, bad_field)

    assert result.applied is False
    assert "non-numeric or non-finite value" in result.diagnostics[0]
    assert "result_vector:U" not in result.mesh_data.point_data
    assert "result_vector:U" not in mesh.point_data


def test_vector_mapping_rejects_oversized_component_values_without_raising() -> None:
    mesh = _mesh()
    field = _vector_field("U")
    bad_rows = (
        ResultRow(0, {"Ux": 0.0, "Uy": 1.0, "Uz": 2.0}),
        ResultRow(1, {"Ux": 10**10000, "Uy": 2.0, "Uz": 3.0}),
        ResultRow(2, {"Ux": 2.0, "Uy": 3.0, "Uz": 4.0}),
    )
    bad_field = ResultField(
        name=field.name, location=field.location, components=field.components, rows=bad_rows
    )

    result = map_result_vector_field_to_mesh(mesh, bad_field)

    assert result.applied is False
    assert "non-numeric or non-finite value" in result.diagnostics[0]
    assert "result_vector:U" not in result.mesh_data.point_data
    assert "result_vector:U" not in mesh.point_data


def test_vector_mapping_rejects_unsupported_location() -> None:
    result = map_result_vector_field_to_mesh(_mesh(), _vector_field("U", location="face"))

    assert result.applied is False
    assert "unknown location" in result.diagnostics[0]


def test_vector_mapping_rejects_non_contiguous_ids() -> None:
    result = map_result_vector_field_to_mesh(_mesh(), _vector_field("U", ids=(0, 1, 5)))

    assert result.applied is False
    assert "not a contiguous range" in result.diagnostics[0]


def test_vector_mapping_has_no_heavy_imports() -> None:
    source = Path(__file__).parents[2] / "src" / "osw" / "post" / "result_field_mapping.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".", 1)[0])

    assert not (imported & {"pyvista", "vtk", "meshio", "gmsh"})
