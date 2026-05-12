"""Mesh import and generation package."""

from __future__ import annotations

from .conversion import convert_mesh, convert_mesh_to_vtu
from .gmsh_adapter import (
    GmshAdapterError,
    GmshMeshResult,
    GmshPrimitive,
    MeshSizeControl,
    PhysicalGroupMetadata,
    convert_gmsh_msh_to_vtu,
    generate_primitive_mesh,
    is_gmsh_available,
    load_gmsh_mesh,
    load_gmsh_mesh_info,
)
from .mesh_model import (
    MeshBoundingBox,
    MeshCellBlock,
    MeshData,
    MeshInfo,
    build_mesh_info,
)
from .meshio_bridge import (
    MeshImportError,
    detect_mesh_format,
    export_vtu,
    load_mesh,
    load_mesh_info,
)

__all__ = [
    "GmshAdapterError",
    "GmshMeshResult",
    "GmshPrimitive",
    "MeshBoundingBox",
    "MeshCellBlock",
    "MeshData",
    "MeshImportError",
    "MeshInfo",
    "MeshSizeControl",
    "PhysicalGroupMetadata",
    "build_mesh_info",
    "convert_gmsh_msh_to_vtu",
    "convert_mesh",
    "convert_mesh_to_vtu",
    "detect_mesh_format",
    "export_vtu",
    "generate_primitive_mesh",
    "is_gmsh_available",
    "load_gmsh_mesh",
    "load_gmsh_mesh_info",
    "load_mesh",
    "load_mesh_info",
]
