"""Minimal standard/exported CAD import preview layer."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from .freecad_bridge import preview_with_freecad_stub
from .geometry_model import GeometryBody, GeometryModel, build_geometry_model
from .occt_importer import preview_with_occt_stub

STANDARD_FORMATS: dict[str, str] = {
    ".stl": "stl",
    ".obj": "obj",
    ".step": "step",
    ".stp": "step",
    ".iges": "iges",
    ".igs": "iges",
    ".brep": "brep",
}

NATIVE_COMMERCIAL_CAD_EXTENSIONS = frozenset(
    {
        ".sldprt",
        ".sldasm",
        ".catpart",
        ".catproduct",
        ".prt",
        ".asm",
    }
)


class GeometryImportError(RuntimeError):
    """Raised when geometry preview cannot proceed with a clear user message."""


def detect_geometry_format(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in NATIVE_COMMERCIAL_CAD_EXTENSIONS:
        msg = (
            "OSW v0.1 does not support native commercial CAD direct import. "
            "Please export STEP or STL from the source CAD tool and import that standard file."
        )
        raise GeometryImportError(msg)

    geometry_format = STANDARD_FORMATS.get(suffix)
    if geometry_format is None:
        supported = ", ".join(sorted(STANDARD_FORMATS))
        msg = (
            f"Unsupported geometry format '{suffix or '<none>'}'. "
            f"Supported standard/exported extensions: {supported}."
        )
        raise GeometryImportError(msg)
    return geometry_format


def preview_geometry(path: str | Path) -> GeometryModel:
    geometry_path = Path(path)
    if not geometry_path.exists():
        msg = f"Geometry file does not exist: {geometry_path}"
        raise GeometryImportError(msg)

    geometry_format = detect_geometry_format(geometry_path)
    try:
        if geometry_format == "stl":
            return _preview_ascii_stl(geometry_path)
        if geometry_format == "obj":
            return _preview_obj(geometry_path)
        if geometry_format in {"step", "iges"}:
            return preview_with_occt_stub(geometry_path, geometry_format=geometry_format)
        if geometry_format == "brep":
            return preview_with_freecad_stub(geometry_path, geometry_format=geometry_format)
    except GeometryImportError:
        raise
    except Exception as exc:
        msg = f"Could not preview geometry '{geometry_path}': {exc}"
        raise GeometryImportError(msg) from exc

    msg = f"No preview handler is available for geometry format '{geometry_format}'."
    raise GeometryImportError(msg)


def _preview_ascii_stl(path: Path) -> GeometryModel:
    vertices = _read_ascii_stl_vertices(path)
    triangle_count = len(vertices) // 3
    body = GeometryBody(
        name=path.stem or "stl-body",
        kind="surface-mesh",
        metadata={"vertices": len(vertices), "triangles": triangle_count},
    )
    return build_geometry_model(
        source=str(path),
        geometry_format="stl",
        vertices=vertices,
        bodies=(body,),
        metadata={"parser": "ascii-stl"},
    )


def _preview_obj(path: Path) -> GeometryModel:
    vertices, faces = _read_obj_vertices_and_faces(path)
    body = GeometryBody(
        name=path.stem or "obj-body",
        kind="surface-mesh",
        metadata={"vertices": len(vertices), "faces": len(faces)},
    )
    return build_geometry_model(
        source=str(path),
        geometry_format="obj",
        vertices=vertices,
        bodies=(body,),
        metadata={"parser": "obj-preview"},
    )


def _read_ascii_stl_vertices(path: Path) -> tuple[tuple[float, float, float], ...]:
    vertices: list[tuple[float, float, float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.strip().split()
        if len(parts) == 4 and parts[0].lower() == "vertex":
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))

    if not vertices:
        msg = "STL preview currently supports ASCII STL files with vertex records."
        raise GeometryImportError(msg)
    return tuple(vertices)


def _read_obj_vertices_and_faces(
    path: Path,
) -> tuple[tuple[tuple[float, float, float], ...], tuple[tuple[str, ...], ...]]:
    vertices: list[tuple[float, float, float]] = []
    faces: list[tuple[str, ...]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if parts[0] == "v" and len(parts) >= 4:
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "f" and len(parts) >= 4:
            faces.append(tuple(parts[1:]))

    if not vertices:
        msg = "OBJ preview requires at least one vertex record."
        raise GeometryImportError(msg)
    return tuple(vertices), tuple(faces)


def supported_geometry_extensions() -> tuple[str, ...]:
    return tuple(sorted(STANDARD_FORMATS))


def native_commercial_cad_extensions() -> tuple[str, ...]:
    return tuple(sorted(NATIVE_COMMERCIAL_CAD_EXTENSIONS))


def import_preview(path: str | Path) -> GeometryModel:
    """Alias used by importer-style callers."""

    return preview_geometry(path)


def preview_many(paths: Iterable[str | Path]) -> tuple[GeometryModel, ...]:
    return tuple(preview_geometry(path) for path in paths)
