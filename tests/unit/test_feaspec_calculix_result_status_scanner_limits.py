from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXResultParserDiagnosticCode,
    CalculiXStatusLineCategory,
    CalculiXStatusScanLimits,
    CalculiXStatusScanStatus,
    scan_calculix_status_file,
)


def _codes(scan: object) -> set[CalculiXResultParserDiagnosticCode]:
    return {diagnostic.code for diagnostic in getattr(scan, "diagnostics", ())}


def test_line_limit_produces_warning_and_partial_summary(tmp_path: Path) -> None:
    path = tmp_path / "case.sta"
    path.write_text(
        "\n".join(f"step {index} increment {index}" for index in range(10)),
        encoding="utf-8",
    )

    scan = scan_calculix_status_file(
        path,
        limits=CalculiXStatusScanLimits(max_lines=3),
    )

    assert scan.status is CalculiXStatusScanStatus.SCANNED_WITH_WARNINGS
    assert scan.processed_line_count == 3
    assert scan.line_count_truncated is True
    assert CalculiXResultParserDiagnosticCode.FP_LINE_LIMIT_EXCEEDED in _codes(scan)
    assert CalculiXResultParserDiagnosticCode.FP_STATUS_PARTIAL_SUMMARY in _codes(scan)


def test_unknown_line_retention_is_bounded(tmp_path: Path) -> None:
    path = tmp_path / "case.sta"
    path.write_text(
        "\n".join(f"opaque line {index}" for index in range(5)),
        encoding="utf-8",
    )

    scan = scan_calculix_status_file(
        path,
        limits=CalculiXStatusScanLimits(max_unknown_lines=2),
    )

    assert scan.summary.unknown_line_count == 5
    assert len(scan.lines) == 2
    assert all(line.category is CalculiXStatusLineCategory.UNKNOWN for line in scan.lines)
    assert (
        CalculiXResultParserDiagnosticCode.FP_STATUS_NO_RECOGNIZED_LINES
        in _codes(scan)
    )
    assert CalculiXResultParserDiagnosticCode.FP_STATUS_PARTIAL_SUMMARY in _codes(scan)


def test_no_recognized_lines_produces_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "case.cvg"
    path.write_text("opaque\nblank\n", encoding="utf-8")

    scan = scan_calculix_status_file(path)

    assert scan.summary.recognized_line_count == 0
    assert (
        CalculiXResultParserDiagnosticCode.FP_STATUS_NO_RECOGNIZED_LINES
        in _codes(scan)
    )


def test_numeric_convergence_tokens_are_not_parsed_as_values(tmp_path: Path) -> None:
    path = tmp_path / "case.cvg"
    path.write_text(
        "convergence residual 1.23E-04 after iteration 8\n",
        encoding="utf-8",
    )

    scan = scan_calculix_status_file(path)
    payload = scan.to_dict()

    assert scan.summary.numeric_tokens_not_parsed is True
    assert scan.numerical_values_parsed is False
    assert scan.lines[0].numeric_tokens_present is True
    assert "1.23E-04" in scan.lines[0].snippet
    assert (
        CalculiXResultParserDiagnosticCode.FP_STATUS_NUMERIC_VALUES_NOT_PARSED
        in _codes(scan)
    )
    assert payload["numerical_values_parsed"] is False
    assert "parsed_values" not in payload
    assert "numeric_values" not in payload


def test_size_limit_falls_back_to_metadata_only(tmp_path: Path) -> None:
    path = tmp_path / "case.sta"
    path.write_text("step 1\n" * 5, encoding="utf-8")

    scan = scan_calculix_status_file(
        path,
        limits=CalculiXStatusScanLimits(max_file_bytes=3),
    )

    assert scan.status is CalculiXStatusScanStatus.METADATA_ONLY
    assert scan.lines == ()
    assert CalculiXResultParserDiagnosticCode.FP_SIZE_LIMIT_EXCEEDED in _codes(scan)
    assert CalculiXResultParserDiagnosticCode.FP_STATUS_PARTIAL_SUMMARY in _codes(scan)
