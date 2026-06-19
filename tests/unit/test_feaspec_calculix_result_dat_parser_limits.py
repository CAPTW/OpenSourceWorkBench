from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXDatMinimalParseLimits,
    CalculiXDatMinimalParseStatus,
    CalculiXResultParserDiagnosticCode,
    parse_calculix_dat_minimal,
)


def _codes(result) -> set[CalculiXResultParserDiagnosticCode]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def test_scalar_limit_is_enforced(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "TOTAL ENERGY SUMMARY\nfirst = 1.0 J\nsecond = 2.0 J\n",
        encoding="utf-8",
    )

    result = parse_calculix_dat_minimal(
        path,
        limits=CalculiXDatMinimalParseLimits(max_scalar_candidates=1),
    )

    assert result.scalar_count == 1
    assert result.status is CalculiXDatMinimalParseStatus.PARTIAL
    assert CalculiXResultParserDiagnosticCode.FP_DAT_SCALAR_LIMIT_EXCEEDED in _codes(
        result
    )


def test_table_row_limit_is_enforced(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "DISPLACEMENTS\nnode | ux\nunits | - | mm\n1 | 0.1\n2 | 0.2\n",
        encoding="utf-8",
    )

    result = parse_calculix_dat_minimal(
        path,
        limits=CalculiXDatMinimalParseLimits(max_table_rows=1),
    )

    assert result.table_candidates[0].row_count == 1
    assert result.status is CalculiXDatMinimalParseStatus.PARTIAL
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_ROW_LIMIT_EXCEEDED
        in _codes(result)
    )


def test_table_column_limit_is_enforced(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "DISPLACEMENTS\nnode | ux | uy | uz\nunits | - | mm | mm | mm\n1 | 0.1 | 0.2 | 0.3\n",
        encoding="utf-8",
    )

    result = parse_calculix_dat_minimal(
        path,
        limits=CalculiXDatMinimalParseLimits(max_table_columns=2),
    )

    assert result.table_candidates[0].column_headers == ("node", "ux")
    assert result.status is CalculiXDatMinimalParseStatus.PARTIAL
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_COLUMN_LIMIT_EXCEEDED
        in _codes(result)
    )


def test_section_size_limit_preserves_bounded_input(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "TOTAL ENERGY SUMMARY\nfirst = 1.0 J\nsecond = 2.0 J\n",
        encoding="utf-8",
    )

    result = parse_calculix_dat_minimal(
        path,
        limits=CalculiXDatMinimalParseLimits(max_section_lines=2),
    )

    assert result.scalar_count == 1
    assert result.scalar_candidates[0].label == "first"


def test_missing_file_is_blocked(tmp_path: Path) -> None:
    result = parse_calculix_dat_minimal(tmp_path / "missing.dat")

    assert result.status is CalculiXDatMinimalParseStatus.BLOCKED
    assert CalculiXResultParserDiagnosticCode.FP_FILE_MISSING in _codes(result)
