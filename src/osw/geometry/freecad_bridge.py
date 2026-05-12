"""Optional FreeCAD bridge placeholder for BREP preview."""

from __future__ import annotations

from pathlib import Path

from .geometry_model import GeometryBody, GeometryModel, build_geometry_model


def is_freecad_available() -> bool:
    return False


def preview_with_freecad_stub(path: str | Path, *, geometry_format: str) -> GeometryModel:
    geometry_path = Path(path)
    body = GeometryBody(
        name=geometry_path.stem or f"{geometry_format}-body",
        kind="cad-placeholder",
        metadata={
            "bridge": "freecad",
            "status": "metadata-only",
            "faces": None,
            "edges": None,
            "vertices": None,
        },
    )
    return build_geometry_model(
        source=str(geometry_path),
        geometry_format=geometry_format,
        vertices=(),
        bodies=(body,),
        metadata={"optional_bridge": "freecad"},
        warnings=(
            "BREP preview uses a metadata-only optional CAD bridge stub; install a reviewed "
            "FreeCAD-backed importer in a later phase for topology details.",
        ),
    )
