"""Dependency-guarded meshio bridge for standard mesh import previews."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from enum import StrEnum
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any

from osw.core.diagnostics import DiagnosticCode, DiagnosticReport
from osw.core.project_schema import MeshRef

from .mesh_model import (
    MeshCellBlock,
    MeshData,
    MeshFormat,
    MeshInfo,
    MeshModel,
    mesh_data_to_model,
    normalize_cell_block,
    normalize_point,
)

SUPPORTED_MESH_FORMATS: dict[str, MeshFormat] = {
    ".msh": MeshFormat.GMSH_MSH,
    ".inp": MeshFormat.ABAQUS_INP,
    ".bdf": MeshFormat.NASTRAN_BDF,
    ".nas": MeshFormat.NASTRAN_BDF,
    ".fem": MeshFormat.NASTRAN_BDF,
    ".su2": MeshFormat.SU2,
    ".vtk": MeshFormat.VTK,
    ".vtu": MeshFormat.VTU,
    ".xdmf": MeshFormat.XDMF,
    ".xmf": MeshFormat.XDMF,
    ".cgns": MeshFormat.CGNS,
    ".med": MeshFormat.MED,
}
MESHIO_WRITE_FORMATS: dict[str, str] = {
    ".inp": "abaqus",
    ".msh": "gmsh22",
    ".vtu": "vtu",
    ".vtk": "vtk",
    ".xdmf": "xdmf",
    ".xmf": "xdmf",
}
NATIVE_COMMERCIAL_CAD_EXTENSIONS = frozenset(
    {".sldprt", ".sldasm", ".catpart", ".catproduct", ".prt", ".asm"}
)


class MeshImportStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    DEPENDENCY_MISSING = "dependency_missing"


class MeshImportError(RuntimeError):
    """Raised by compatibility APIs when a mesh operation cannot continue."""


@dataclass(frozen=True)
class MeshImportResult:
    status: MeshImportStatus
    mesh: MeshModel | None = None
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    source_path: str = ""
    format: str = MeshFormat.UNKNOWN.value

    @property
    def ok(self) -> bool:
        return self.status in {MeshImportStatus.OK, MeshImportStatus.WARNING}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "source_path": self.source_path,
            "format": self.format,
            "mesh": self.mesh.to_dict(include_arrays=False) if self.mesh else None,
            "diagnostics": self.diagnostics.to_dict(),
        }


@dataclass(frozen=True)
class MeshExportResult:
    status: MeshImportStatus
    output_path: str = ""
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    artifact_ref: MeshRef | None = None

    @property
    def ok(self) -> bool:
        return self.status in {MeshImportStatus.OK, MeshImportStatus.WARNING}


def meshio_available() -> bool:
    return importlib.util.find_spec("meshio") is not None


def is_meshio_available() -> bool:
    return meshio_available()


def supported_mesh_formats() -> list[str]:
    return sorted({mesh_format.value for mesh_format in SUPPORTED_MESH_FORMATS.values()})


def supported_mesh_extensions() -> list[str]:
    return sorted(SUPPORTED_MESH_FORMATS)


def detect_mesh_format(path: str | Path) -> MeshFormat:
    suffix = Path(path).suffix.lower()
    if suffix in NATIVE_COMMERCIAL_CAD_EXTENSIONS:
        msg = (
            f"Unsupported mesh format '{suffix}'. v0.1 supports standard/exported "
            "CAD and mesh formats. Please export STEP/STL/OBJ or a supported mesh format."
        )
        raise MeshImportError(msg)
    mesh_format = SUPPORTED_MESH_FORMATS.get(suffix)
    if mesh_format is None:
        supported = ", ".join(sorted(SUPPORTED_MESH_FORMATS))
        msg = f"Unsupported mesh format '{suffix or '<none>'}'. Supported extensions: {supported}."
        raise MeshImportError(msg)
    return mesh_format


def read_mesh(path: str | Path, *, meshio_module: Any | None = None) -> MeshImportResult:
    mesh_path = Path(path)
    try:
        mesh_format = detect_mesh_format(mesh_path)
    except MeshImportError as exc:
        report = DiagnosticReport()
        code = (
            "native-commercial-cad-unsupported"
            if mesh_path.suffix.lower() in NATIVE_COMMERCIAL_CAD_EXTENSIONS
            else "unsupported-mesh-format"
        )
        report.add_error(
            code,
            str(exc),
            hint="Use a standard/exported mesh format supported by meshio.",
            path=mesh_path,
        )
        return MeshImportResult(
            MeshImportStatus.ERROR,
            diagnostics=report,
            source_path=str(mesh_path),
            format=MeshFormat.UNKNOWN.value,
        )

    if not mesh_path.exists():
        report = DiagnosticReport()
        report.add_error(
            "mesh-file-missing",
            f"Mesh file does not exist: {mesh_path}",
            hint="Choose an existing mesh file before importing.",
            path=mesh_path,
        )
        return MeshImportResult(
            MeshImportStatus.ERROR,
            diagnostics=report,
            source_path=str(mesh_path),
            format=mesh_format.value,
        )

    try:
        module = meshio_module if meshio_module is not None else _load_meshio()
    except MeshImportError as exc:
        report = DiagnosticReport()
        report.add_error(
            DiagnosticCode.DEPENDENCY_UNAVAILABLE,
            str(exc),
            hint='Install the mesh extra, for example: python -m pip install -e ".[mesh]"',
            path=mesh_path,
        )
        return MeshImportResult(
            MeshImportStatus.DEPENDENCY_MISSING,
            diagnostics=report,
            source_path=str(mesh_path),
            format=mesh_format.value,
        )

    try:
        raw_mesh = module.read(str(mesh_path))
        mesh_data = mesh_data_from_meshio(raw_mesh)
        mesh = mesh_data_to_model(
            mesh_data,
            source=str(mesh_path),
            mesh_format=mesh_format,
            name=mesh_path.name,
        )
    except Exception as exc:  # pragma: no cover - exact meshio errors vary by plugin.
        report = DiagnosticReport()
        report.add_error(
            "mesh-read-failed",
            f"Could not read mesh '{mesh_path}': {exc}",
            hint="Verify the file is a valid exported mesh in a supported format.",
            path=mesh_path,
        )
        return MeshImportResult(
            MeshImportStatus.ERROR,
            diagnostics=report,
            source_path=str(mesh_path),
            format=mesh_format.value,
        )

    report = DiagnosticReport()
    if mesh.info.warnings:
        for warning in mesh.info.warnings:
            report.add_warning("mesh-info-warning", warning, path=mesh_path)
        status = MeshImportStatus.WARNING
    else:
        status = MeshImportStatus.OK
    return MeshImportResult(
        status,
        mesh=mesh,
        diagnostics=report,
        source_path=str(mesh_path),
        format=mesh_format.value,
    )


def read_mesh_info(path: str | Path, *, meshio_module: Any | None = None) -> MeshInfo:
    result = read_mesh(path, meshio_module=meshio_module)
    if result.mesh is None:
        raise MeshImportError(result.diagnostics.summary())
    return result.mesh.info


def load_mesh(path: str | Path, *, meshio_module: Any | None = None) -> MeshData:
    result = read_mesh(path, meshio_module=meshio_module)
    if result.mesh is None:
        raise MeshImportError(_compat_error_message(result))
    return result.mesh.to_mesh_data()


def load_mesh_info(path: str | Path, *, meshio_module: Any | None = None) -> MeshInfo:
    return read_mesh_info(path, meshio_module=meshio_module)


def mesh_data_from_meshio(mesh: Any) -> MeshData:
    points = tuple(normalize_point(point) for point in getattr(mesh, "points", ()))
    cells = tuple(_normalize_meshio_cell_block(block) for block in getattr(mesh, "cells", ()))
    return MeshData(
        points=points,
        cells=cells,
        point_data=dict(getattr(mesh, "point_data", {}) or {}),
        cell_data=dict(getattr(mesh, "cell_data", {}) or {}),
        field_data=dict(getattr(mesh, "field_data", {}) or {}),
    )


def mesh_to_project_ref(
    mesh: MeshModel,
    project_relative_path: str | None = None,
    *,
    ref_id: str | None = None,
) -> MeshRef:
    path = project_relative_path or mesh.source_path or mesh.info.source_path
    return MeshRef(
        id=ref_id or mesh.id,
        path=path,
        format=mesh.info.format,
        name=mesh.name or Path(path).name,
        status="imported",
        cell_count=mesh.info.element_count,
        node_count=mesh.info.node_count,
        quality_summary=_quality_summary(mesh.info),
        mesh_info=mesh.info.to_dict(),
        metadata={
            "mesh_info": mesh.info.to_dict(),
            "cell_types": list(mesh.info.cell_types),
            "point_data_names": list(mesh.info.point_data_names),
            "cell_data_names": list(mesh.info.cell_data_names),
        },
    )


def write_mesh(
    mesh: MeshModel | MeshData,
    path: str | Path,
    *,
    file_format: str | None = None,
    meshio_module: Any | None = None,
) -> MeshExportResult:
    target = Path(path)
    try:
        extension = _resolve_write_extension(target, file_format)
    except MeshImportError as exc:
        report = DiagnosticReport()
        report.add_error(
            "unsupported-mesh-export-format",
            str(exc),
            hint="Choose a standard mesh output extension such as .vtu, .vtk, .msh, or .xdmf.",
            path=target,
        )
        return MeshExportResult(MeshImportStatus.ERROR, str(target), report)
    meshio_format = MESHIO_WRITE_FORMATS[extension]
    mesh_data = mesh.to_mesh_data() if isinstance(mesh, MeshModel) else mesh

    try:
        module = meshio_module if meshio_module is not None else _load_meshio()
    except MeshImportError as exc:
        report = DiagnosticReport()
        report.add_error(
            DiagnosticCode.DEPENDENCY_UNAVAILABLE,
            str(exc),
            hint='Install the mesh extra, for example: python -m pip install -e ".[mesh]"',
            path=target,
        )
        return MeshExportResult(MeshImportStatus.DEPENDENCY_MISSING, str(target), report)

    target.parent.mkdir(parents=True, exist_ok=True)
    raw_mesh = module.Mesh(
        points=[list(point) for point in mesh_data.points],
        cells=[(block.cell_type, [list(row) for row in block.data]) for block in mesh_data.cells],
    )
    try:
        module.write(str(target), raw_mesh, file_format=meshio_format)
    except Exception as exc:  # pragma: no cover - exact meshio errors vary by plugin.
        report = DiagnosticReport()
        report.add_error(
            "mesh-write-failed",
            f"Could not export mesh '{target}' as {meshio_format}: {exc}",
            hint="Verify the requested output format is supported by meshio.",
            path=target,
        )
        return MeshExportResult(MeshImportStatus.ERROR, str(target), report)

    info = (
        mesh.info
        if isinstance(mesh, MeshModel)
        else mesh.info(str(target), extension.lstrip("."))
    )
    artifact_ref = MeshRef(
        id=Path(target).stem,
        path=str(target),
        format=extension.lstrip("."),
        name=target.name,
        status="exported",
        cell_count=info.element_count,
        node_count=info.node_count,
        mesh_info=info.to_dict(),
    )
    return MeshExportResult(MeshImportStatus.OK, str(target), DiagnosticReport(), artifact_ref)


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
    result = write_mesh(mesh_data, target, file_format="vtu", meshio_module=meshio_module)
    if not result.ok:
        raise MeshImportError(result.diagnostics.summary())
    return target


def _load_meshio() -> ModuleType:
    try:
        return import_module("meshio")
    except ImportError as exc:
        msg = (
            "meshio is not installed. Install the optional mesh extra before "
            "importing or converting mesh files."
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


def _resolve_write_extension(target: Path, file_format: str | None) -> str:
    if file_format:
        normalized = file_format.lower().lstrip(".")
        aliases = {
            "abaqus": ".inp",
            "calculix": ".inp",
            "gmsh": ".msh",
            "gmsh22": ".msh",
            "inp": ".inp",
            "msh": ".msh",
            "vtk": ".vtk",
            "vtu": ".vtu",
            "xdmf": ".xdmf",
            "xmf": ".xmf",
        }
        extension = aliases.get(normalized, f".{normalized}")
    else:
        extension = target.suffix.lower()
    if extension not in MESHIO_WRITE_FORMATS:
        supported = ", ".join(sorted(MESHIO_WRITE_FORMATS))
        msg = (
            f"Unsupported mesh export format '{extension or '<none>'}'. "
            f"Supported extensions: {supported}."
        )
        raise MeshImportError(msg)
    return extension


def _quality_summary(info: MeshInfo) -> str:
    return (
        f"{info.node_count} nodes, {info.element_count} elements, "
        f"cell types: {', '.join(info.cell_types) or 'none'}"
    )


def _compat_error_message(result: MeshImportResult) -> str:
    summary = result.diagnostics.summary()
    if "Mesh file does not exist" in summary:
        return f"Mesh file does not exist: {result.source_path}"
    if "Could not read mesh" in summary:
        return summary
    return summary
