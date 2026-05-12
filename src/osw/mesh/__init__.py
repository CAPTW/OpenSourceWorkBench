"""Mesh import and generation package."""

from __future__ import annotations

from .conversion import (
    SUPPORTED_EXPORT_FORMATS,
    MeshExportArtifact,
    MeshExportError,
    convert_mesh,
    convert_mesh_to_vtu,
    export_mesh,
)
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
from .quality import (
    MeshQualityMetrics,
    MeshQualityWarning,
    analyze_mesh_quality,
)

__all__ = [
    "GmshAdapterError",
    "GmshMeshResult",
    "GmshPrimitive",
    "MeshBoundingBox",
    "MeshCellBlock",
    "MeshData",
    "MeshExportArtifact",
    "MeshExportError",
    "MeshImportError",
    "MeshInfo",
    "MeshQualityMetrics",
    "MeshQualityWarning",
    "MeshSizeControl",
    "PhysicalGroupMetadata",
    "SUPPORTED_EXPORT_FORMATS",
    "analyze_mesh_quality",
    "build_mesh_info",
    "convert_gmsh_msh_to_vtu",
    "convert_mesh",
    "convert_mesh_to_vtu",
    "detect_mesh_format",
    "export_mesh",
    "export_vtu",
    "generate_primitive_mesh",
    "is_gmsh_available",
    "load_gmsh_mesh",
    "load_gmsh_mesh_info",
    "load_mesh",
    "load_mesh_info",
]
