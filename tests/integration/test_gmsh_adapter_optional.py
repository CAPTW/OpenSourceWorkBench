from __future__ import annotations

from pathlib import Path

import pytest

from osw.mesh.gmsh_adapter import GmshAdapter, find_gmsh_executable
from osw.mesh.gmsh_model import (
    GmshGeometryKind,
    GmshGeometrySpec,
    GmshMeshDimension,
    GmshMeshRequest,
    GmshMeshSizeField,
    GmshMeshStatus,
)
from osw.mesh.meshio_bridge import meshio_available

pytestmark = pytest.mark.optional_dependency


def test_optional_real_gmsh_rectangle_generation(tmp_path: Path) -> None:
    resolution = find_gmsh_executable()
    if not resolution.found:
        pytest.skip(resolution.diagnostics.summary())

    request = GmshMeshRequest(
        geometry=GmshGeometrySpec(
            GmshGeometryKind.RECTANGLE,
            {"width": 0.2, "height": 0.1},
            geometry_id="tiny_rectangle",
        ),
        mesh_dimension=GmshMeshDimension.DIM2,
        mesh_size=GmshMeshSizeField(global_size=0.05),
        output_dir=tmp_path,
        output_name="tiny_rectangle",
        convert_to_vtu=meshio_available(),
        timeout_seconds=10.0,
    )

    result = GmshAdapter().generate_mesh(request)

    assert result.status in {GmshMeshStatus.OK, GmshMeshStatus.WARNING}
    assert result.msh_path is not None
    assert result.msh_path.exists()
    if meshio_available():
        assert result.mesh_info is not None
        assert result.mesh_info.node_count > 0
        assert result.mesh_info.element_count > 0
