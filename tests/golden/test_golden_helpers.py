from __future__ import annotations

from pathlib import Path

import pytest
from helpers import assert_text_matches_golden, normalize_text


def test_normalize_text_replaces_paths_and_timestamps() -> None:
    text = "created=2026-05-14T10:20:30Z\npath=C:\\tmp\\case\\out.dat\n"

    assert normalize_text(
        text,
        replacements=((Path("C:/tmp/case"), "<CASE_ROOT>"),),
    ) == "created=<TIMESTAMP>\npath=<CASE_ROOT>\\out.dat\n"


def test_assert_text_matches_golden_reports_unified_diff() -> None:
    with pytest.raises(AssertionError, match="expected/demo.txt"):
        assert_text_matches_golden("alpha\nbeta\n", "alpha\ngamma\n", label="demo.txt")
