"""JSON helpers for optional solver manifests."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

from .manifest_models import OptionalSolverManifest, parse_optional_solver_manifest_dict


def load_optional_solver_manifest_json(path: str | Path) -> OptionalSolverManifest:
    """Load a declarative optional solver manifest from JSON."""

    manifest_path = Path(path)
    _require_json_path(manifest_path)
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"Invalid optional solver manifest JSON: {manifest_path}"
        raise ValueError(msg) from exc
    if not isinstance(payload, Mapping):
        msg = "Optional solver manifest JSON must contain an object."
        raise ValueError(msg)
    return parse_optional_solver_manifest_dict(payload)


def dump_optional_solver_manifest_json(
    manifest: OptionalSolverManifest,
    path: str | Path,
    *,
    overwrite: bool = False,
) -> None:
    """Write a declarative optional solver manifest to JSON."""

    manifest_path = Path(path)
    _require_json_path(manifest_path)
    if not manifest_path.parent.exists():
        msg = f"Parent directory does not exist: {manifest_path.parent}"
        raise ValueError(msg)
    if manifest_path.exists() and not overwrite:
        msg = f"Optional solver manifest already exists: {manifest_path}"
        raise ValueError(msg)
    manifest_path.write_text(
        json.dumps(manifest.to_dict(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _require_json_path(path: Path) -> None:
    if path.suffix.lower() != ".json":
        msg = f"Optional solver manifests use JSON files only: {path}"
        raise ValueError(msg)
