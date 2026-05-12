from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest

from osw.mesh.conversion import convert_mesh
from osw.mesh.meshio_bridge import load_mesh_info

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("meshio") is None,
    reason="meshio optional mesh extra is not installed.",
)


def test_generated_vtu_mesh_import_and_export(tmp_path: Path) -> None:
    meshio = importlib.import_module("meshio")
    source_path = tmp_path / "small.vtu"
    export_path = tmp_path / "exported.vtu"
    mesh = meshio.Mesh(
        points=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
        cells=[("triangle", [(0, 1, 2)])],
    )
    meshio.write(source_path, mesh, file_format="vtu")

    info = load_mesh_info(source_path)
    converted = convert_mesh(source_path, export_path, output_format="vtu")

    assert info.nodes == 3
    assert info.elements == 1
    assert info.cell_types == ("triangle",)
    assert info.bounding_box.minimum == (0.0, 0.0, 0.0)
    assert info.bounding_box.maximum == (1.0, 1.0, 0.0)
    assert converted == export_path
    assert export_path.exists()
