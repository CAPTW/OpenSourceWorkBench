from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXFrdBlockKind,
    CalculiXFrdBlockScanLimits,
    CalculiXFrdBlockScanStatus,
    CalculiXResultParserDiagnosticCode,
    scan_calculix_frd_blocks,
)


def _codes(scan: object) -> set[CalculiXResultParserDiagnosticCode]:
    return {diagnostic.code for diagnostic in getattr(scan, "diagnostics", ())}


def test_line_limit_produces_block_scanner_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_text(
        "\n".join(["1C FRD HEADER", "detail", "100C DISPLACEMENT FIELD", "value"]),
        encoding="utf-8",
    )

    scan = scan_calculix_frd_blocks(
        path,
        limits=CalculiXFrdBlockScanLimits(max_lines=2),
    )

    assert scan.status is CalculiXFrdBlockScanStatus.SCANNED_WITH_WARNINGS
    assert scan.processed_line_count == 2
    assert scan.line_count_truncated is True
    assert CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_LIMIT_EXCEEDED in _codes(
        scan
    )


def test_block_span_limit_produces_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_text(
        "\n".join(["1C FRD HEADER", "detail 1", "detail 2", "detail 3"]),
        encoding="utf-8",
    )

    scan = scan_calculix_frd_blocks(
        path,
        limits=CalculiXFrdBlockScanLimits(max_block_lines=2),
    )

    assert scan.blocks[0].line_end == 2
    assert CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_TOO_LARGE in _codes(scan)


def test_snippets_are_bounded(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_text("100C DISPLACEMENT FIELD\n" + ("x" * 80), encoding="utf-8")

    scan = scan_calculix_frd_blocks(
        path,
        limits=CalculiXFrdBlockScanLimits(max_snippet_chars=12),
    )

    assert all(len(snippet) <= 12 for snippet in scan.blocks[0].snippets)


def test_unknown_block_retention_is_bounded(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_text(
        "\n".join(f"777C REVIEW RECORD {index}" for index in range(5)),
        encoding="utf-8",
    )

    scan = scan_calculix_frd_blocks(
        path,
        limits=CalculiXFrdBlockScanLimits(max_unknown_blocks=2),
    )

    assert scan.summary.unknown_block_count == 2
    assert [block.kind for block in scan.blocks] == [
        CalculiXFrdBlockKind.UNKNOWN,
        CalculiXFrdBlockKind.UNKNOWN,
    ]
    assert CalculiXResultParserDiagnosticCode.FP_FRD_UNKNOWN_RECORD in _codes(scan)


def test_size_limit_falls_back_to_metadata_only(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_text("1C FRD HEADER\n", encoding="utf-8")

    scan = scan_calculix_frd_blocks(
        path,
        limits=CalculiXFrdBlockScanLimits(max_file_bytes=3),
    )

    assert scan.status is CalculiXFrdBlockScanStatus.METADATA_ONLY
    assert scan.blocks == ()
    assert CalculiXResultParserDiagnosticCode.FP_SIZE_LIMIT_EXCEEDED in _codes(scan)
    assert CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_TOO_LARGE in _codes(scan)


def test_binary_like_content_is_unsupported(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_bytes(b"1C FRD HEADER\x00\x00\x00")

    scan = scan_calculix_frd_blocks(path)

    assert scan.status is CalculiXFrdBlockScanStatus.UNSUPPORTED
    assert CalculiXResultParserDiagnosticCode.FP_FRD_BINARY_UNSUPPORTED in _codes(scan)
    assert scan.blocks == ()
