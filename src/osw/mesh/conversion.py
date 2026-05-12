"""Mesh conversion helpers built on the meshio bridge."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .meshio_bridge import MeshImportError, export_vtu, load_mesh


def convert_mesh(
    source_path: str | Path,
    target_path: str | Path,
    *,
    output_format: str = "vtu",
    meshio_module: Any | None = None,
) -> Path:
    """Convert a supported mesh file to a supported output format."""

    if output_format.lower() != "vtu":
        msg = "Only VTU export is available in the v0.1 mesh import MVP."
        raise MeshImportError(msg)

    mesh_data = load_mesh(source_path, meshio_module=meshio_module)
    return export_vtu(mesh_data, target_path, meshio_module=meshio_module)


def convert_mesh_to_vtu(
    source_path: str | Path,
    target_path: str | Path,
    *,
    meshio_module: Any | None = None,
) -> Path:
    return convert_mesh(source_path, target_path, output_format="vtu", meshio_module=meshio_module)
