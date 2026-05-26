from __future__ import annotations

from pathlib import Path

import pytest

from osw.mesh.meshio_bridge import MeshImportStatus, read_mesh, write_mesh


def test_optional_meshio_can_import_and_export_tiny_mesh(tmp_path: Path) -> None:
    meshio = pytest.importorskip("meshio", reason="meshio optional mesh extra is not installed.")

    source = tmp_path / "tiny.msh"
    meshio.write(
        source,
        meshio.Mesh(
            points=[[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            cells=[("triangle", [[0, 1, 2]])],
        ),
        file_format="gmsh22",
    )

    result = read_mesh(source)
    assert result.status in {MeshImportStatus.OK, MeshImportStatus.WARNING}
    assert result.mesh is not None
    assert result.mesh.info.node_count == 3
    assert result.mesh.info.element_count == 1
    assert result.mesh.info.cell_types == ("triangle",)

    output = tmp_path / "tiny.vtu"
    export = write_mesh(result.mesh, output)

    assert export.status is MeshImportStatus.OK
    assert output.exists()
