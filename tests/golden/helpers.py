"""Shared helpers for deterministic golden-file comparisons."""

from __future__ import annotations

import difflib
import json
import re
from pathlib import Path
from typing import Any

TIMESTAMP_RE = re.compile(
    r"\b20\d\d-\d\d-\d\d(?:[ T][0-2]\d:[0-5]\d:[0-5]\d(?:\.\d+)?)?(?:Z|[+-]\d\d:?\d\d)?\b"
)


def lexical_path_variants(value: str | Path) -> tuple[str, ...]:
    """Return known-root spellings without host-native filesystem resolution.

    A Windows absolute root must produce both separator forms on every host.
    Foreign paths are not passed through ``Path.resolve()``.
    """

    raw = str(value)
    variants: list[str] = []
    seen: set[str] = set()

    def add(item: str) -> None:
        if item and item not in seen:
            seen.add(item)
            variants.append(item)

    add(raw)
    add(raw.replace("\\", "/"))
    add(raw.replace("/", "\\"))
    if isinstance(value, Path):
        add(value.as_posix())
    variants.sort(key=len, reverse=True)
    return tuple(variants)


def normalize_text(
    text: str,
    *,
    replacements: tuple[tuple[str | Path, str], ...] = (),
) -> str:
    """Normalize line endings, trailing whitespace, timestamps, and known paths."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    replacement_pairs: list[tuple[str, str]] = []
    for value, token in replacements:
        for candidate in lexical_path_variants(value):
            replacement_pairs.append((candidate, token))
    replacement_pairs.sort(key=lambda item: len(item[0]), reverse=True)
    for candidate, token in replacement_pairs:
        normalized = normalized.replace(candidate, token)
    normalized = TIMESTAMP_RE.sub("<TIMESTAMP>", normalized)
    return "\n".join(line.rstrip() for line in normalized.strip().splitlines()) + "\n"


def assert_text_matches_golden(
    actual: str,
    expected: str,
    *,
    label: str,
    replacements: tuple[tuple[str | Path, str], ...] = (),
) -> None:
    """Assert text equality with a readable unified diff on mismatch."""

    normalized_actual = normalize_text(actual, replacements=replacements)
    normalized_expected = normalize_text(expected, replacements=replacements)
    if normalized_actual == normalized_expected:
        return

    diff = "\n".join(
        difflib.unified_diff(
            normalized_expected.splitlines(),
            normalized_actual.splitlines(),
            fromfile=f"expected/{label}",
            tofile=f"actual/{label}",
            lineterm="",
        )
    )
    raise AssertionError(f"Golden text mismatch for {label}:\n{diff}")


def canonical_json(value: Any) -> str:
    """Render JSON-like data in a stable, diff-friendly form."""

    data = json.loads(value) if isinstance(value, str) else value
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def assert_json_matches_golden(actual: Any, expected: Any, *, label: str) -> None:
    """Assert JSON equality with stable formatting and a readable diff."""

    actual_text = canonical_json(actual)
    expected_text = canonical_json(expected)
    assert_text_matches_golden(actual_text, expected_text, label=label)
