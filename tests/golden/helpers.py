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


def normalize_text(
    text: str,
    *,
    replacements: tuple[tuple[str | Path, str], ...] = (),
) -> str:
    """Normalize line endings, trailing whitespace, timestamps, and known paths."""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    for value, token in replacements:
        raw = str(value)
        normalized = normalized.replace(raw, token)
        normalized = normalized.replace(raw.replace("\\", "/"), token)
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
