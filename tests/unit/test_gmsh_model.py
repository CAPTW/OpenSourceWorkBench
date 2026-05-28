from __future__ import annotations

import json
from pathlib import Path

from osw.mesh.gmsh_model import (
    GmshGeometryKind,
    GmshGeometrySpec,
    GmshMeshDimension,
    GmshMeshRequest,
    GmshMeshResult,
    GmshMeshSizeField,
    GmshMeshStatus,
    GmshPhysicalGroup,
)


def test_gmsh_geometry_spec_serializes_and_deserializes() -> None:
    spec = GmshGeometrySpec(
        GmshGeometryKind.BOX,
        {"length": 1.0, "width": 0.2, "height": 0.1},
        geometry_id="box",
        units="m",
        physical_groups=(GmshPhysicalGroup("domain", 3, (1,), tag=4),),
    )

    round_tripped = GmshGeometrySpec.from_dict(spec.to_dict())

    assert round_tripped.kind is GmshGeometryKind.BOX
    assert round_tripped.parameters["width"] == 0.2
    assert round_tripped.physical_groups[0].name == "domain"


def test_gmsh_mesh_size_field_serializes_and_validates() -> None:
    field = GmshMeshSizeField(global_size=0.05, min_size=0.01, max_size=0.1)

    round_tripped = GmshMeshSizeField.from_dict(field.to_dict())

    assert round_tripped.global_size == 0.05
    assert round_tripped.effective_min == 0.01
    assert round_tripped.effective_max == 0.1


def test_gmsh_mesh_request_serializes_paths_as_strings(tmp_path: Path) -> None:
    request = GmshMeshRequest(
        geometry=GmshGeometrySpec(GmshGeometryKind.RECTANGLE, {"width": 1.0, "height": 0.5}),
        mesh_dimension=GmshMeshDimension.DIM2,
        mesh_size=GmshMeshSizeField(global_size=0.1),
        output_dir=tmp_path,
        output_name="rect",
    )

    payload = request.to_dict()
    round_tripped = GmshMeshRequest.from_dict(payload)

    assert payload["output_dir"] == str(tmp_path)
    assert round_tripped.output_dir == tmp_path
    assert round_tripped.mesh_dimension is GmshMeshDimension.DIM2


def test_gmsh_mesh_result_is_json_serializable(tmp_path: Path) -> None:
    request = GmshMeshRequest(output_dir=tmp_path, output_name="box")
    result = GmshMeshResult(
        GmshMeshStatus.OK,
        request,
        geo_path=tmp_path / "box.geo",
        msh_path=tmp_path / "box.msh",
    )

    payload = result.to_dict()

    assert payload["status"] == "ok"
    assert payload["geo_path"].endswith("box.geo")
    json.dumps(payload)
