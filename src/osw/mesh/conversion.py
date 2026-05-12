"""Mesh conversion and export helpers built on the meshio bridge."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

from osw.core.project_schema import ResultRef

from .mesh_model import MeshData
from .meshio_bridge import MeshImportError, load_mesh

SUPPORTED_EXPORT_FORMATS: dict[str, str] = {
    ".inp": "abaqus",
    ".msh": "gmsh",
    ".vtu": "vtu",
    ".xdmf": "xdmf",
    ".xmf": "xdmf",
}

MESHIO_WRITE_FORMATS: dict[str, str] = {
    ".inp": "abaqus",
    ".msh": "gmsh22",
    ".vtu": "vtu",
    ".xdmf": "xdmf",
    ".xmf": "xdmf",
}

FORMAT_ALIASES: dict[str, str] = {
    "abaqus": ".inp",
    "calculix": ".inp",
    "gmsh": ".msh",
    "gmsh22": ".msh",
    "inp": ".inp",
    "msh": ".msh",
    "vtu": ".vtu",
    "xdmf": ".xdmf",
    "xmf": ".xmf",
}

COMMON_MESHIO_CELL_TYPES = frozenset(
    {
        "vertex",
        "line",
        "line3",
        "triangle",
        "triangle6",
        "quad",
        "quad8",
        "quad9",
        "tetra",
        "tetra10",
        "hexahedron",
        "hexahedron20",
        "wedge",
        "pyramid",
    }
)

CALCULIX_INP_CELL_TYPES = frozenset(
    {
        "line",
        "line3",
        "triangle",
        "triangle6",
        "quad",
        "quad8",
        "tetra",
        "tetra10",
        "hexahedron",
        "hexahedron20",
        "wedge",
        "pyramid",
    }
)


class MeshExportError(RuntimeError):
    """Raised when a mesh export cannot be completed with a friendly message."""


@dataclass(frozen=True)
class MeshExportArtifact:
    """Track a generated mesh artifact for reports and project references."""

    path: str | Path
    format: str
    meshio_format: str
    node_count: int
    element_count: int
    cell_types: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "cell_types", tuple(self.cell_types))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "format": self.format,
            "meshio_format": self.meshio_format,
            "node_count": self.node_count,
            "element_count": self.element_count,
            "cell_types": list(self.cell_types),
            "metadata": dict(self.metadata),
        }

    def to_result_ref(self, ref_id: str) -> ResultRef:
        metadata = {
            "format": self.format,
            "meshio_format": self.meshio_format,
            "node_count": self.node_count,
            "element_count": self.element_count,
            "cell_types": list(self.cell_types),
            **self.metadata,
        }
        return ResultRef(
            ref_id=ref_id,
            path=str(self.path),
            kind="mesh_export",
            metadata=metadata,
        )


def export_mesh(
    mesh_data: MeshData,
    target_path: str | Path,
    *,
    output_format: str | None = None,
    meshio_module: Any | None = None,
    metadata: dict[str, Any] | None = None,
) -> MeshExportArtifact:
    """Export normalized mesh data to a supported standard mesh format."""

    target = Path(target_path)
    extension = _resolve_export_extension(target, output_format)
    logical_format = SUPPORTED_EXPORT_FORMATS[extension]
    meshio_format = MESHIO_WRITE_FORMATS[extension]
    _validate_export_cell_types(mesh_data, extension)

    module = meshio_module if meshio_module is not None else _load_meshio()
    target.parent.mkdir(parents=True, exist_ok=True)
    mesh = module.Mesh(
        points=[list(point) for point in mesh_data.points],
        cells=[
            (block.cell_type, [list(row) for row in block.data])
            for block in mesh_data.cells
        ],
    )
    try:
        module.write(str(target), mesh, file_format=meshio_format)
    except Exception as exc:  # pragma: no cover - exact meshio errors vary by plugin.
        msg = f"Could not export mesh '{target}' as {logical_format}: {exc}"
        raise MeshExportError(msg) from exc

    return MeshExportArtifact(
        path=target,
        format=logical_format,
        meshio_format=meshio_format,
        node_count=len(mesh_data.points),
        element_count=sum(block.count for block in mesh_data.cells),
        cell_types=_cell_types(mesh_data),
        metadata=metadata or {},
    )


def convert_mesh(
    source_path: str | Path,
    target_path: str | Path,
    *,
    output_format: str | None = None,
    meshio_module: Any | None = None,
) -> Path:
    """Convert a supported mesh file to a supported output format."""

    mesh_data = load_mesh(source_path, meshio_module=meshio_module)
    artifact = export_mesh(
        mesh_data,
        target_path,
        output_format=output_format,
        meshio_module=meshio_module,
    )
    return Path(artifact.path)


def convert_mesh_to_vtu(
    source_path: str | Path,
    target_path: str | Path,
    *,
    meshio_module: Any | None = None,
) -> Path:
    return convert_mesh(
        source_path,
        target_path,
        output_format="vtu",
        meshio_module=meshio_module,
    )


def _load_meshio() -> ModuleType:
    try:
        return import_module("meshio")
    except ImportError as exc:
        msg = (
            "meshio is not installed. Install the optional mesh extra, for example "
            "`pip install open-solver-workbench[mesh]`, before exporting mesh files."
        )
        raise MeshImportError(msg) from exc


def _resolve_export_extension(target: Path, output_format: str | None) -> str:
    if output_format is not None:
        normalized = output_format.lower().lstrip(".")
        extension = FORMAT_ALIASES.get(normalized, f".{normalized}")
    else:
        extension = target.suffix.lower()

    if extension not in SUPPORTED_EXPORT_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_EXPORT_FORMATS))
        msg = (
            f"Unsupported mesh export format '{extension or '<none>'}'. "
            f"Supported extensions: {supported}."
        )
        raise MeshExportError(msg)
    return extension


def _validate_export_cell_types(mesh_data: MeshData, extension: str) -> None:
    allowed = CALCULIX_INP_CELL_TYPES if extension == ".inp" else COMMON_MESHIO_CELL_TYPES
    label = ".inp" if extension == ".inp" else extension
    for block in mesh_data.cells:
        if block.cell_type not in allowed:
            msg = (
                f"Unsupported cell type '{block.cell_type}' for {label} export. "
                f"Supported cell types: {', '.join(sorted(allowed))}."
            )
            raise MeshExportError(msg)


def _cell_types(mesh_data: MeshData) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for block in mesh_data.cells:
        if block.cell_type not in seen:
            ordered.append(block.cell_type)
            seen.add(block.cell_type)
    return tuple(ordered)
