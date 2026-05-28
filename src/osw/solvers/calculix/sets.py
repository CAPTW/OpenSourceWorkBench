"""Small helpers for deterministic CalculiX set formatting."""

from __future__ import annotations

from collections.abc import Iterable


def normalize_set_name(name: str) -> str:
    """Return a stable CalculiX-safe uppercase set name."""

    normalized = "".join(
        char.upper() if char.isalnum() else "_"
        for char in str(name).strip()
    ).strip("_")
    return normalized or "SET"


def chunk_ids(ids: Iterable[int], *, width: int = 16) -> tuple[tuple[int, ...], ...]:
    """Chunk one-based ids for readable CalculiX set sections."""

    normalized = tuple(int(item) for item in ids)
    return tuple(
        normalized[index : index + width]
        for index in range(0, len(normalized), width)
    )
