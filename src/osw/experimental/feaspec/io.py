"""JSON I/O helpers for the experimental FEASpec model layer."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .models import FEASpec, FEASpecCandidate, FEASpecDocument, parse_feaspec_dict


def load_feaspec(
    path: str | Path,
    *,
    allow_diagnostics: bool = False,
) -> FEASpecCandidate | FEASpec:
    """Load a FEASpec JSON file and parse it through the model layer."""

    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return parse_feaspec_dict(payload, allow_diagnostics=allow_diagnostics)


def dump_feaspec(
    spec: FEASpecDocument | Mapping[str, Any],
    path: str | Path,
    *,
    indent: int = 2,
) -> None:
    """Write a FEASpec model or mapping to JSON."""

    payload = spec.to_dict() if isinstance(spec, FEASpecDocument) else dict(spec)
    Path(path).write_text(
        json.dumps(payload, indent=indent, sort_keys=False) + "\n",
        encoding="utf-8",
    )
