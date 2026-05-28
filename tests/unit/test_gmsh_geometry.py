from __future__ import annotations

from pathlib import Path

import pytest

from osw.mesh.gmsh_geometry import GmshGeometryError, default_physical_groups, generate_geo_script
from osw.mesh.gmsh_model import (
    GmshGeometryKind,
    GmshGeometrySpec,
    GmshMeshDimension,
    GmshMeshRequest,
    GmshMeshSizeField,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "gmsh"


def _request(
    kind: GmshGeometryKind,
    parameters: dict[str, object],
    *,
    dimension: GmshMeshDimension,
    name: str,
) -> GmshMeshRequest:
    return GmshMeshRequest(
        geometry=GmshGeometrySpec(kind, parameters, geometry_id=name, units="m"),
        mesh_dimension=dimension,
        mesh_size=GmshMeshSizeField(global_size=0.05),
        output_name=name,
    )


def test_rectangle_geo_generation_is_deterministic() -> None:
    script = generate_geo_script(
        _request(
            GmshGeometryKind.RECTANGLE,
            {"width": 1.0, "height": 0.5},
            dimension=GmshMeshDimension.DIM2,
            name="rectangle",
        )
    )

    assert script == (FIXTURES / "expected_rectangle.geo").read_text(encoding="utf-8")


def test_box_geo_generation_is_deterministic() -> None:
    script = generate_geo_script(
        _request(
            GmshGeometryKind.BOX,
            {"length": 1.0, "width": 0.2, "height": 0.1},
            dimension=GmshMeshDimension.DIM3,
            name="box",
        )
    )

    assert script == (FIXTURES / "expected_box.geo").read_text(encoding="utf-8")


def test_cylinder_geo_generation_is_deterministic() -> None:
    script = generate_geo_script(
        _request(
            GmshGeometryKind.CYLINDER,
            {"radius": 0.25, "height": 1.0},
            dimension=GmshMeshDimension.DIM3,
            name="cylinder",
        )
    )

    assert "Cylinder(1)" in script
    assert "Physical Volume(\"domain\")" in script


def test_plate_with_hole_geo_generation_is_deterministic() -> None:
    script = generate_geo_script(
        _request(
            GmshGeometryKind.PLATE_WITH_HOLE,
            {"width": 1.0, "height": 0.5, "hole_radius": 0.1, "center": (0.5, 0.25)},
            dimension=GmshMeshDimension.DIM2,
            name="plate",
        )
    )

    assert "Circle(5)" in script
    assert "Physical Curve(\"hole_wall\")" in script


def test_unsupported_geometry_kind_is_friendly() -> None:
    request = GmshMeshRequest(
        geometry=GmshGeometrySpec(GmshGeometryKind.UNKNOWN, {}),
        output_name="unknown",
    )

    with pytest.raises(GmshGeometryError, match="Unsupported Gmsh geometry kind"):
        generate_geo_script(request)


def test_physical_group_labels_are_stable() -> None:
    groups = default_physical_groups(GmshGeometryKind.BOX, GmshMeshDimension.DIM3)

    assert [group.name for group in groups] == ["inlet", "outlet", "wall", "domain"]
