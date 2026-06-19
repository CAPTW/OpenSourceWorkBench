from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXDatMinimalDirectoryParseResult,
    CalculiXDatMinimalParseLimits,
    CalculiXDatMinimalParseResult,
    CalculiXDatMinimalParseStatus,
    CalculiXDatScalarCandidate,
    CalculiXDatTableCandidate,
    CalculiXDatUnitContext,
    CalculiXDatUnsupportedContent,
    CalculiXDatValueCell,
    CalculiXResultParserDiagnosticCode,
    explain_calculix_dat_minimal_parse,
    parse_calculix_dat_directory_minimal,
    parse_calculix_dat_minimal,
)


def _codes(result: CalculiXDatMinimalParseResult) -> set[CalculiXResultParserDiagnosticCode]:
    return {diagnostic.code for diagnostic in result.diagnostics}


def _write_scalar_dat(path: Path, body: str = "total energy = 1.25 J\n") -> Path:
    path.write_text("TOTAL ENERGY SUMMARY\n" + body, encoding="utf-8")
    return path


def _write_table_dat(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "DISPLACEMENTS",
                "node | ux | uy",
                "units | - | mm | mm",
                "1 | 0.10 | 0.20",
                "2 | 0.30 | 0.40",
            ]
        ),
        encoding="utf-8",
    )
    return path


def test_dat_parser_module_imports_and_exports_required_api() -> None:
    assert parse_calculix_dat_minimal
    assert parse_calculix_dat_directory_minimal
    assert explain_calculix_dat_minimal_parse
    assert CalculiXDatMinimalParseStatus
    assert CalculiXDatMinimalParseLimits
    assert CalculiXDatScalarCandidate
    assert CalculiXDatTableCandidate
    assert CalculiXDatUnsupportedContent
    assert CalculiXDatMinimalParseResult
    assert CalculiXDatMinimalDirectoryParseResult
    assert CalculiXDatValueCell
    assert CalculiXDatUnitContext


def test_unsupported_suffix_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_text("not dat\n", encoding="utf-8")

    result = parse_calculix_dat_minimal(path)

    assert result.status is CalculiXDatMinimalParseStatus.UNSUPPORTED
    assert CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT in _codes(result)


def test_dat_file_is_accepted(tmp_path: Path) -> None:
    result = parse_calculix_dat_minimal(_write_scalar_dat(tmp_path / "case.dat"))

    assert result.suffix == ".dat"
    assert result.name == "case.dat"
    assert result.minimal_parser is True
    assert result.freeform_parser is False
    assert result.frd_parser is False


def test_scalar_candidate_equals_style_parses_with_raw_value_unit_and_provenance(
    tmp_path: Path,
) -> None:
    result = parse_calculix_dat_minimal(_write_scalar_dat(tmp_path / "case.dat"))

    assert result.scalar_count == 1
    scalar = result.scalar_candidates[0]
    assert scalar.label == "total energy"
    assert scalar.raw_value == "1.25"
    assert scalar.value == 1.25
    assert scalar.unit == "J"
    assert scalar.raw_line == "total energy = 1.25 J"
    assert scalar.line_number == 2
    assert scalar.section_heading == "total energy = 1.25 J"
    assert scalar.source_path.endswith("case.dat")
    assert CalculiXResultParserDiagnosticCode.FP_DAT_SCALAR_CANDIDATE_PARSED in _codes(
        result
    )


def test_scalar_candidate_colon_style_parses(tmp_path: Path) -> None:
    result = parse_calculix_dat_minimal(
        _write_scalar_dat(tmp_path / "case.dat", body="max displacement: 2.5 mm\n")
    )

    assert result.scalar_candidates[0].label == "max displacement"
    assert result.scalar_candidates[0].value == 2.5
    assert result.scalar_candidates[0].unit == "mm"


def test_scalar_missing_unit_is_skipped_with_diagnostic(tmp_path: Path) -> None:
    result = parse_calculix_dat_minimal(
        _write_scalar_dat(tmp_path / "case.dat", body="max displacement = 2.5\n")
    )

    assert result.scalar_candidates == ()
    assert CalculiXResultParserDiagnosticCode.FP_DAT_UNITS_MISSING in _codes(result)


def test_scalar_can_use_explicit_unit_context(tmp_path: Path) -> None:
    result = parse_calculix_dat_minimal(
        _write_scalar_dat(tmp_path / "case.dat", body="max displacement = 2.5\n"),
        unit_context=CalculiXDatUnitContext(
            scalar_units={"max displacement": "mm"},
        ),
    )

    assert result.scalar_candidates[0].value == 2.5
    assert result.scalar_candidates[0].unit == "mm"


def test_scalar_malformed_number_emits_diagnostic(tmp_path: Path) -> None:
    result = parse_calculix_dat_minimal(
        _write_scalar_dat(tmp_path / "case.dat", body="max displacement = nope mm\n")
    )

    assert result.scalar_candidates == ()
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_NUMERIC_CONVERSION_FAILED
        in _codes(result)
    )


def test_simple_table_with_explicit_units_parses_and_preserves_raw_cells(
    tmp_path: Path,
) -> None:
    result = parse_calculix_dat_minimal(_write_table_dat(tmp_path / "case.dat"))

    assert result.table_count == 1
    table = result.table_candidates[0]
    assert table.section_heading == "DISPLACEMENTS"
    assert table.column_headers == ("node", "ux", "uy")
    assert table.units["ux"] == "mm"
    assert table.units["uy"] == "mm"
    assert table.row_count == 2
    assert table.rows[0][0].raw == "1"
    assert table.rows[0][0].parsed is False
    assert table.rows[0][1].raw == "0.10"
    assert table.rows[0][1].value == 0.10
    assert table.rows[0][1].unit == "mm"
    assert table.parsed_numeric_value_count == 4
    assert CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_CANDIDATE_PARSED in _codes(
        result
    )


def test_table_can_use_unit_context_for_value_columns(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "DISPLACEMENTS\nnode | ux\n1 | 0.10\n",
        encoding="utf-8",
    )

    result = parse_calculix_dat_minimal(
        path,
        unit_context={"table_column_units": {"ux": "mm"}},
    )

    assert result.table_candidates[0].rows[0][1].value == 0.10
    assert result.table_candidates[0].rows[0][1].unit == "mm"


def test_table_missing_unit_skips_numeric_value_for_column(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "DISPLACEMENTS\nnode | ux\n1 | 0.10\n",
        encoding="utf-8",
    )

    result = parse_calculix_dat_minimal(path)

    assert result.table_candidates[0].rows[0][1].value is None
    assert result.table_candidates[0].rows[0][1].parsed is False
    assert CalculiXResultParserDiagnosticCode.FP_DAT_UNITS_MISSING in _codes(result)


def test_unknown_table_is_skipped(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text("TABLE OF REACTION OUTPUT\nnode force 1.0 N\n", encoding="utf-8")

    result = parse_calculix_dat_minimal(path)

    assert result.table_candidates == ()
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_UNKNOWN_TABLE_SKIPPED
        in _codes(result)
    )


def test_unsupported_section_is_preserved_with_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text("CONTACT PAIR RESULTS\nunsupported text\n", encoding="utf-8")

    result = parse_calculix_dat_minimal(path)

    assert result.unsupported_content
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_UNSUPPORTED_SECTION_SKIPPED
        in _codes(result)
    )


def test_node_and_element_output_candidates_preserve_provenance(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "NODE OUTPUT\nnode | ux\nunits | - | mm\n1 | 0.1\n"
        "ELEMENT OUTPUT\nelement | sxx\nunits | - | MPa\n1 | 5.0\n",
        encoding="utf-8",
    )

    result = parse_calculix_dat_minimal(path)

    assert result.table_count == 2
    assert result.table_candidates[0].section_heading == "NODE OUTPUT"
    assert result.table_candidates[0].header_line_number == 2
    assert result.table_candidates[1].section_heading == "ELEMENT OUTPUT"
    assert result.table_candidates[1].header_line_number == 6


def test_explain_dat_minimal_parse_is_reviewer_readable(tmp_path: Path) -> None:
    result = parse_calculix_dat_minimal(_write_scalar_dat(tmp_path / "case.dat"))

    lines = explain_calculix_dat_minimal_parse(result)

    assert any("minimal parse" in line.lower() for line in lines)
    assert any("free-form parser: false" in line.lower() for line in lines)
    assert any("units inferred: false" in line.lower() for line in lines)


def test_directory_parser_picks_dat_only_sorted_and_non_recursive(tmp_path: Path) -> None:
    root = tmp_path / "results"
    root.mkdir()
    _write_scalar_dat(root / "b.dat")
    _write_scalar_dat(root / "a.dat")
    (root / "ignored.frd").write_text("not parsed\n", encoding="utf-8")
    (root / "ignored.sta").write_text("not parsed\n", encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    _write_scalar_dat(nested / "z.dat")

    result = parse_calculix_dat_directory_minimal(root)

    assert [item.name for item in result.files] == ["a.dat", "b.dat"]
    assert result.recursive is False
    assert result.writes_files is False
    assert result.scalar_count == 2


def test_parser_writes_no_files(tmp_path: Path) -> None:
    root = tmp_path / "results"
    root.mkdir()
    path = _write_scalar_dat(root / "case.dat")
    before = sorted(item.name for item in root.iterdir())

    result = parse_calculix_dat_minimal(path)

    assert result.writes_files is False
    assert before == sorted(item.name for item in root.iterdir())


def test_result_to_dict_includes_summary_flags(tmp_path: Path) -> None:
    result = parse_calculix_dat_minimal(_write_scalar_dat(tmp_path / "case.dat"))
    payload = result.to_dict()

    assert payload["summary"]["scalar_candidate_count"] == 1
    assert payload["summary"]["freeform_parser"] is False
    assert payload["summary"]["frd_parser"] is False
    assert payload["summary"]["units_inferred"] is False
    assert payload["summary"]["writes_files"] is False
