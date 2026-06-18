from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXResultMetadataLimits,
    CalculiXResultMetadataStatus,
    CalculiXResultParserDiagnosticCode,
    scan_calculix_result_file_metadata,
)


def test_default_limits_are_explicit_and_reusable() -> None:
    limits = CalculiXResultMetadataLimits()

    assert limits.max_file_bytes > 0
    assert limits.max_lines > 0
    assert limits.max_snippet_chars > 0
    assert limits.max_snippet_lines > 0
    assert ".dat" in limits.allowed_suffixes
    assert ".frd" in limits.allowed_suffixes
    assert ".sta" in limits.allowed_suffixes
    assert ".cvg" in limits.allowed_suffixes


def test_limits_can_be_tightened_to_force_limit_behavior(tmp_path: Path) -> None:
    target = tmp_path / "result.txt"
    target.write_text("one\ntwo\nthree\n", encoding="utf-8")

    scan = scan_calculix_result_file_metadata(
        target,
        limits=CalculiXResultMetadataLimits(
            max_file_bytes=4,
            max_lines=1,
            max_snippet_lines=1,
            max_snippet_chars=2,
        ),
    )

    assert scan.status is CalculiXResultMetadataStatus.LIMIT_EXCEEDED
    assert CalculiXResultParserDiagnosticCode.FP_SIZE_LIMIT_EXCEEDED in {
        item.code for item in scan.diagnostics
    }


def test_snippet_limits_only_affect_snippets(tmp_path: Path) -> None:
    target = tmp_path / "result.txt"
    target.write_text("abcdefghijkl\n", encoding="utf-8")

    scan = scan_calculix_result_file_metadata(
        target,
        limits=CalculiXResultMetadataLimits(max_snippet_chars=3, max_snippet_lines=1),
    )

    assert scan.snippet_truncated is True
    assert scan.first_line_snippets[0] == "abc"
    assert CalculiXResultParserDiagnosticCode.FP_SNIPPET_TRUNCATED in {
        item.code for item in scan.diagnostics
    }
