from __future__ import annotations

from osw.mesh.mesh_model import MeshBounds, MeshCellBlock, MeshInfo, MeshModel


def test_mesh_info_serializes_and_deserializes() -> None:
    info = MeshInfo(
        source_path="mesh/tiny.vtu",
        format="vtu",
        node_count=3,
        cell_blocks=(MeshCellBlock("triangle", count=1),),
        bounds=MeshBounds(0.0, 0.0, 0.0, 1.0, 1.0, 0.0),
        point_data_names=("temperature",),
        cell_data_names=("material",),
        field_data_names=("physical",),
        physical_groups={"inlet": 1},
        warnings=("preview only",),
        metadata={"source": "test"},
    )

    round_tripped = MeshInfo.from_dict(info.to_dict())

    assert round_tripped.source_path == "mesh/tiny.vtu"
    assert round_tripped.format == "vtu"
    assert round_tripped.node_count == 3
    assert round_tripped.element_count == 1
    assert round_tripped.cell_types == ("triangle",)
    assert round_tripped.bounds.maximum == (1.0, 1.0, 0.0)
    assert round_tripped.point_data_names == ("temperature",)
    assert round_tripped.physical_groups == {"inlet": 1}
    assert round_tripped.warnings == ("preview only",)


def test_mesh_model_serializes_with_optional_arrays() -> None:
    model = MeshModel(
        id="tiny",
        name="tiny.vtu",
        source_path="mesh/tiny.vtu",
        points=((0, 0, 0), (1, 0, 0), (0, 1, 0)),
        cells=(MeshCellBlock("triangle", ((0, 1, 2),)),),
        point_data={"temperature": [300.0, 301.0, 302.0]},
        cell_data={"region": [1]},
    )

    payload = model.to_dict()
    summary_payload = model.to_dict(include_arrays=False)
    round_tripped = MeshModel.from_dict(payload)

    assert payload["points"] == [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    assert "points" not in summary_payload
    assert round_tripped.id == "tiny"
    assert round_tripped.info.node_count == 3
    assert round_tripped.info.element_count == 1
    assert round_tripped.to_mesh_data().cells[0].cell_type == "triangle"


def test_empty_mesh_info_records_preview_warnings() -> None:
    model = MeshModel(name="empty")

    assert model.info.node_count == 0
    assert model.info.element_count == 0
    assert "Mesh contains zero nodes." in model.info.warnings
    assert "Mesh contains zero elements." in model.info.warnings
