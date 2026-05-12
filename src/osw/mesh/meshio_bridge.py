"""Dependency-guarded meshio bridge for standard mesh import previews."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

from .mesh_model import MeshCellBlock, MeshData, MeshInfo, normalize_cell_block, normalize_point

SUPPORTED_MESH_FORMATS: dict[str, str] = {
    ".msh": "gmsh",
    ".inp": "abaqus",
    ".bdf": "nastran",
    ".nas": "nastran",
    ".fem": "nastran",
    ".su2": "su2",
    ".vtk": "vtk",
    ".vtu": "vtu",
    ".xdmf": "xdmf",
    ".xmf": "xdmf",
    ".cgns": "cgns",
}


class MeshImportError(RuntimeError):
    """Raised when a mesh cannot be imported with a user-actionable message."""


def detect_mesh_format(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    mesh_format = SUPPORTED_MESH_FORMATS.get(suffix)
    if mesh_format is None:
        supported = ", ".join(sorted(SUPPORTED_MESH_FORMATS))
        msg = f"Unsupported mesh format '{suffix or '<none>'}'. Supported extensions: {supported}."
        raise MeshImportError(msg)
    return mesh_format


def is_meshio_available() -> bool:
    try:
        _load_meshio()
    except MeshImportError:
        return False
    return True


def load_mesh(path: str | Path, *, meshio_module: Any | None = None) -> MeshData:
    mesh_path = Path(path)
    if not mesh_path.exists():
        msg = f"Mesh file does not exist: {mesh_path}"
        raise MeshImportError(msg)

    detect_mesh_format(mesh_path)
    module = meshio_module if meshio_module is not None else _load_meshio()
    try:
        raw_mesh = module.read(str(mesh_path))
    except Exception as exc:  # pragma: no cover - exact meshio errors vary by plugin.
        msg = f"Could not read mesh '{mesh_path}': {exc}"
        raise MeshImportError(msg) from exc
    try:
        return mesh_data_from_meshio(raw_mesh)
    except Exception as exc:
        msg = f"Could not normalize mesh '{mesh_path}': {exc}"
        raise MeshImportError(msg) from exc


def load_mesh_info(path: str | Path, *, meshio_module: Any | None = None) -> MeshInfo:
    mesh_path = Path(path)
    mesh_format = detect_mesh_format(mesh_path)
    return load_mesh(mesh_path, meshio_module=meshio_module).info(str(mesh_path), mesh_format)


def mesh_data_from_meshio(mesh: Any) -> MeshData:
    points = tuple(normalize_point(point) for point in getattr(mesh, "points", ()))
    cells = tuple(_normalize_meshio_cell_block(block) for block in getattr(mesh, "cells", ()))
    return MeshData(
        points=points,
        cells=cells,
        point_data=dict(getattr(mesh, "point_data", {}) or {}),
        cell_data=dict(getattr(mesh, "cell_data", {}) or {}),
    )


def export_vtu(
    mesh_data: MeshData,
    target_path: str | Path,
    *,
    meshio_module: Any | None = None,
) -> Path:
    target = Path(target_path)
    if target.suffix.lower() != ".vtu":
        msg = "VTU export target must use the .vtu extension."
        raise MeshImportError(msg)

    module = meshio_module if meshio_module is not None else _load_meshio()
    target.parent.mkdir(parents=True, exist_ok=True)
    mesh = module.Mesh(
        points=[list(point) for point in mesh_data.points],
        cells=[(block.cell_type, [list(row) for row in block.data]) for block in mesh_data.cells],
    )
    try:
        module.write(str(target), mesh, file_format="vtu")
    except Exception as exc:  # pragma: no cover - exact meshio errors vary by plugin.
        msg = f"Could not export VTU mesh '{target}': {exc}"
        raise MeshImportError(msg) from exc
    return target


def _load_meshio() -> ModuleType:
    try:
        return import_module("meshio")
    except ImportError as exc:
        msg = (
            "meshio is not installed. Install the optional mesh extra, for example "
            "`pip install open-solver-workbench[mesh]`, before importing mesh files."
        )
        raise MeshImportError(msg) from exc


def _normalize_meshio_cell_block(block: Any) -> MeshCellBlock:
    if isinstance(block, MeshCellBlock):
        return block
    if hasattr(block, "type") and hasattr(block, "data"):
        return normalize_cell_block(str(block.type), block.data)
    if isinstance(block, tuple) and len(block) == 2:
        cell_type, data = block
        return normalize_cell_block(str(cell_type), data)

    msg = f"Unsupported mesh cell block shape: {type(block).__name__}"
    raise TypeError(msg)
