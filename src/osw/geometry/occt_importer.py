"""Optional OCCT bridge placeholder for STEP and IGES preview."""

from __future__ import annotations

from pathlib import Path

from .geometry_model import GeometryBody, GeometryModel, build_geometry_model


def is_occt_available() -> bool:
    return False


def preview_with_occt_stub(path: str | Path, *, geometry_format: str) -> GeometryModel:
    geometry_path = Path(path)
    body = GeometryBody(
        name=geometry_path.stem or f"{geometry_format}-body",
        kind="cad-placeholder",
        metadata={
            "bridge": "occt",
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
        metadata={"optional_bridge": "occt"},
        warnings=(
            f"{geometry_format.upper()} preview uses a metadata-only optional CAD bridge stub; "
            "install a reviewed OCCT-backed importer in a later phase for topology details.",
        ),
    )
