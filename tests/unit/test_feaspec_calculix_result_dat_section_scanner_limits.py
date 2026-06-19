from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXDatSectionKind,
    CalculiXDatSectionScanLimits,
    CalculiXDatSectionScanStatus,
    CalculiXResultParserDiagnosticCode,
    scan_calculix_dat_sections,
)


def _codes(scan: object) -> set[CalculiXResultParserDiagnosticCode]:
    return {diagnostic.code for diagnostic in getattr(scan, "diagnostics", ())}


def test_line_limit_produces_section_scanner_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "\n".join(["CalculiX header", "detail", "TOTAL ENERGY SUMMARY", "value"]),
        encoding="utf-8",
    )

    scan = scan_calculix_dat_sections(
        path,
        limits=CalculiXDatSectionScanLimits(max_lines=2),
    )

    assert scan.status is CalculiXDatSectionScanStatus.SCANNED_WITH_WARNINGS
    assert scan.processed_line_count == 2
    assert scan.line_count_truncated is True
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_LINE_LIMIT_EXCEEDED
        in _codes(scan)
    )


def test_section_size_limit_produces_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "\n".join(["CalculiX header", "detail 1", "detail 2", "detail 3"]),
        encoding="utf-8",
    )

    scan = scan_calculix_dat_sections(
        path,
        limits=CalculiXDatSectionScanLimits(max_section_lines=2),
    )

    assert scan.sections[0].line_end == 2
    assert CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_TOO_LARGE in _codes(scan)


def test_snippets_are_bounded(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text("TOTAL ENERGY SUMMARY\n" + ("x" * 80), encoding="utf-8")

    scan = scan_calculix_dat_sections(
        path,
        limits=CalculiXDatSectionScanLimits(max_snippet_chars=12),
    )

    assert all(len(snippet) <= 12 for snippet in scan.sections[0].snippets)


def test_unknown_section_retention_is_bounded(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "\n".join(f"UNKNOWN SECTION {index}:" for index in range(5)),
        encoding="utf-8",
    )

    scan = scan_calculix_dat_sections(
        path,
        limits=CalculiXDatSectionScanLimits(max_unknown_sections=2),
    )

    assert scan.summary.unknown_section_count == 2
    assert [section.kind for section in scan.sections] == [
        CalculiXDatSectionKind.UNKNOWN,
        CalculiXDatSectionKind.UNKNOWN,
    ]
    assert CalculiXResultParserDiagnosticCode.FP_DAT_UNKNOWN_SECTION in _codes(scan)


def test_size_limit_falls_back_to_metadata_only(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text("CalculiX header\n", encoding="utf-8")

    scan = scan_calculix_dat_sections(
        path,
        limits=CalculiXDatSectionScanLimits(max_file_bytes=3),
    )

    assert scan.status is CalculiXDatSectionScanStatus.METADATA_ONLY
    assert scan.sections == ()
    assert CalculiXResultParserDiagnosticCode.FP_SIZE_LIMIT_EXCEEDED in _codes(scan)
    assert CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_TOO_LARGE in _codes(scan)
