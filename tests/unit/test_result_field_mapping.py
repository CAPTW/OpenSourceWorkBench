"""Qt-free / PyVista-free unit tests for ResultField -> mesh scalar mapping."""

from __future__ import annotations

from osw.core.result_dataset import ResultDataset, ResultField, ResultRow
from osw.mesh.mesh_model import MeshCellBlock, MeshData
from osw.post.result_field_mapping import (
    ResultFieldMapping,
    map_result_field_to_mesh,
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


def test_node_field_maps_to_point_data_overlay() -> None:
    result = map_result_field_to_mesh(_mesh(), _node_field("temp"))
    assert isinstance(result, ResultFieldMapping)
    assert result.applied is True
    assert result.location == "point"
    assert result.field_name == "temp"
    assert result.mesh_data.point_data["temp"] == (0.0, 10.0, 20.0)
    assert "temp" not in result.mesh_data.cell_data


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
    result = map_result_field_to_mesh(_mesh(), _node_field("temp", ids=(0, 1)))
    assert result.applied is False
    assert result.diagnostics and "not applied" in result.diagnostics[0]
    # No fabricated array added; overlay equals the input mesh (no 'temp' key).
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
