from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from osw.mesh.gmsh_adapter import GmshPrimitive, MeshSizeControl, generate_primitive_mesh

pytestmark = pytest.mark.optional_dependency


def _optional_gmsh_meshio() -> tuple[object, object]:
    try:
        return importlib.import_module("gmsh"), importlib.import_module("meshio")
    except Exception as exc:  # pragma: no cover - depends on optional local extras.
        pytest.skip(f"gmsh and meshio optional mesh extras are not available: {exc}")


def test_optional_gmsh_plate_mesh_generation(tmp_path: Path) -> None:
    gmsh, meshio = _optional_gmsh_meshio()
    msh_path = tmp_path / "plate.msh"
    vtu_path = tmp_path / "plate.vtu"

    result = generate_primitive_mesh(
        GmshPrimitive.plate(width=1.0, height=0.5, name="plate"),
        msh_path,
        mesh_size=MeshSizeControl(target_size=0.2),
        gmsh_module=gmsh,
        meshio_module=meshio,
        vtu_path=vtu_path,
    )

    assert result.msh_path.exists()
    assert result.vtu_path == vtu_path
    assert vtu_path.exists()
    assert result.mesh_info is not None
    assert result.mesh_info.nodes > 0
    assert result.mesh_info.elements > 0
