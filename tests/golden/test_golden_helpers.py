from __future__ import annotations

from pathlib import Path

import pytest

from helpers import assert_text_matches_golden, normalize_text


def test_normalize_text_replaces_paths_and_timestamps() -> None:
    text = "created=2026-05-14T10:20:30Z\npath=C:\\tmp\\case\\out.dat\n"

    assert (
        normalize_text(
            text,
            replacements=((Path("C:/tmp/case"), "<CASE_ROOT>"),),
        )
        == "created=<TIMESTAMP>\npath=<CASE_ROOT>\\out.dat\n"
    )


def test_normalize_text_replaces_foreign_windows_path_from_lexical_posix_root() -> None:
    """A POSIX-form known root must match a Windows lexical path on any host."""

    text = "created=2026-05-14T10:20:30Z\npath=C:\\tmp\\case\\out.dat\n"

    assert (
        normalize_text(
            text,
            replacements=(("C:/tmp/case", "<CASE_ROOT>"),),
        )
        == "created=<TIMESTAMP>\npath=<CASE_ROOT>\\out.dat\n"
    )


def test_normalize_text_replaces_both_separator_forms_of_known_root() -> None:
    text = "slash=C:/tmp/case/out.dat\nbackslash=C:\\tmp\\case\\out.dat\n"

    assert (
        normalize_text(text, replacements=(("C:/tmp/case", "<CASE_ROOT>"),))
        == "slash=<CASE_ROOT>/out.dat\nbackslash=<CASE_ROOT>\\out.dat\n"
    )


def test_normalize_text_preserves_posix_paths_and_unrelated_windows_roots() -> None:
    text = (
        "posix=/tmp/case/out.dat\n"
        "other=C:\\tmp\\other\\out.dat\n"
        "url=https://example.com:443/docs\n"
        "label=created:ok\n"
    )

    assert normalize_text(
        text,
        replacements=(("/tmp/case", "<CASE_ROOT>"), ("C:/tmp/case", "<WIN_ROOT>")),
    ) == (
        "posix=<CASE_ROOT>/out.dat\n"
        "other=C:\\tmp\\other\\out.dat\n"
        "url=https://example.com:443/docs\n"
        "label=created:ok\n"
    )


def test_normalize_text_replaces_longer_roots_before_shorter_roots() -> None:
    text = "path=C:\\tmp\\case\\out.dat\n"

    assert (
        normalize_text(
            text,
            replacements=(("C:/tmp", "<TMP>"), ("C:/tmp/case", "<CASE_ROOT>")),
        )
        == "path=<CASE_ROOT>\\out.dat\n"
    )


def test_normalize_text_path_normalization_is_idempotent() -> None:
    text = "created=2026-05-14T10:20:30Z\npath=C:\\tmp\\case\\out.dat\n"
    replacements = (("C:/tmp/case", "<CASE_ROOT>"),)
    once = normalize_text(text, replacements=replacements)
    assert once == "created=<TIMESTAMP>\npath=<CASE_ROOT>\\out.dat\n"
    assert normalize_text(once, replacements=replacements) == once


def test_assert_text_matches_golden_reports_unified_diff() -> None:
    with pytest.raises(AssertionError, match="expected/demo.txt"):
        assert_text_matches_golden("alpha\nbeta\n", "alpha\ngamma\n", label="demo.txt")
