from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXDatSection,
    CalculiXDatSectionDirectoryScan,
    CalculiXDatSectionKind,
    CalculiXDatSectionScan,
    CalculiXDatSectionScanLimits,
    CalculiXDatSectionScanStatus,
    CalculiXDatSectionSummary,
    CalculiXResultArtifactKind,
    CalculiXResultParserDiagnosticCode,
    explain_calculix_dat_section_scan,
    inspect_calculix_result_directory,
    scan_calculix_dat_sections,
    scan_calculix_dat_sections_directory,
)


def _write_dat(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "CalculiX 2.21 result file",
                "job beam_case",
                "SOLVER MESSAGE:",
                "iteration text only",
                "TOTAL ENERGY SUMMARY",
                "total strain energy 1.23E-04",
                "TABLE OF REACTION OUTPUT",
                "node force text 10.0",
                "DISPLACEMENTS",
                "U1 text 2.0",
                "STRESSES",
                "SXX text 3.0",
                "NODE OUTPUT",
                "node result text",
                "ELEMENT OUTPUT",
                "element result text",
                "CONTACT PAIR RESULTS",
                "unsupported text",
                "ODD REVIEW SECTION:",
                "opaque text",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _codes(scan: CalculiXDatSectionScan) -> set[CalculiXResultParserDiagnosticCode]:
    return {diagnostic.code for diagnostic in scan.diagnostics}


def _kinds(scan: CalculiXDatSectionScan) -> set[CalculiXDatSectionKind]:
    return {section.kind for section in scan.sections}


def test_dat_section_scanner_module_imports_and_exports_required_api() -> None:
    assert scan_calculix_dat_sections
    assert scan_calculix_dat_sections_directory
    assert explain_calculix_dat_section_scan
    assert CalculiXDatSectionKind
    assert CalculiXDatSection
    assert CalculiXDatSectionSummary
    assert CalculiXDatSectionScan
    assert CalculiXDatSectionDirectoryScan
    assert CalculiXDatSectionScanStatus
    assert CalculiXDatSectionScanLimits


def test_unsupported_suffix_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "result.frd"
    path.write_text("CalculiX result\n", encoding="utf-8")

    scan = scan_calculix_dat_sections(path)

    assert scan.status is CalculiXDatSectionScanStatus.UNSUPPORTED
    assert CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT in _codes(scan)


def test_dat_file_is_accepted_and_classifies_required_section_kinds(
    tmp_path: Path,
) -> None:
    scan = scan_calculix_dat_sections(_write_dat(tmp_path / "case.dat"))
    kinds = _kinds(scan)

    assert scan.suffix == ".dat"
    assert scan.artifact_kind == "dat"
    assert CalculiXDatSectionKind.HEADER in kinds
    assert CalculiXDatSectionKind.SOLVER_MESSAGE in kinds
    assert CalculiXDatSectionKind.SCALAR_CANDIDATE in kinds
    assert CalculiXDatSectionKind.TABLE_CANDIDATE in kinds
    assert CalculiXDatSectionKind.DISPLACEMENT_CANDIDATE in kinds
    assert CalculiXDatSectionKind.STRESS_CANDIDATE in kinds
    assert CalculiXDatSectionKind.NODE_OUTPUT_CANDIDATE in kinds
    assert CalculiXDatSectionKind.ELEMENT_OUTPUT_CANDIDATE in kinds
    assert CalculiXDatSectionKind.UNSUPPORTED in kinds
    assert CalculiXDatSectionKind.UNKNOWN in kinds
    assert scan.summary.numeric_tokens_not_parsed is True
    assert scan.numerical_values_parsed is False
    assert scan.numeric_values_extracted is False
    assert scan.tables_extracted is False


def test_unknown_and_unsupported_sections_are_preserved_with_diagnostics(
    tmp_path: Path,
) -> None:
    scan = scan_calculix_dat_sections(_write_dat(tmp_path / "case.dat"))

    assert any(section.kind is CalculiXDatSectionKind.UNKNOWN for section in scan.sections)
    assert any(section.unsupported for section in scan.sections)
    assert CalculiXResultParserDiagnosticCode.FP_DAT_UNKNOWN_SECTION in _codes(scan)
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_HEADING_UNSUPPORTED
        in _codes(scan)
    )


def test_no_recognized_sections_produces_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text("opaque lowercase line\nanother opaque line\n", encoding="utf-8")

    scan = scan_calculix_dat_sections(path)

    assert scan.sections == ()
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_NO_RECOGNIZED_SECTIONS
        in _codes(scan)
    )


def test_section_spans_heading_lines_and_snippets_are_deterministic(
    tmp_path: Path,
) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "CalculiX header\nheader detail\nTOTAL ENERGY SUMMARY\nvalue 4.0\n",
        encoding="utf-8",
    )

    first = scan_calculix_dat_sections(path)
    second = scan_calculix_dat_sections(path)

    assert [section.to_dict() for section in first.sections] == [
        section.to_dict() for section in second.sections
    ]
    assert first.sections[0].heading_line_number == 1
    assert first.sections[0].line_start == 1
    assert first.sections[0].line_end == 2
    assert first.sections[1].heading_line_number == 3
    assert "value 4.0" in first.sections[1].snippets


def test_numeric_tokens_remain_text_snippets_only(tmp_path: Path) -> None:
    path = tmp_path / "case.dat"
    path.write_text(
        "TOTAL ENERGY SUMMARY\nstrain energy 1.234E-05\n",
        encoding="utf-8",
    )

    scan = scan_calculix_dat_sections(path)
    payload = scan.to_dict()

    assert scan.summary.numeric_tokens_not_parsed is True
    assert scan.sections[0].numeric_tokens_present is True
    assert "1.234E-05" in scan.sections[0].snippets[1]
    assert (
        CalculiXResultParserDiagnosticCode.FP_DAT_NUMERIC_VALUES_NOT_PARSED
        in _codes(scan)
    )
    assert payload["numerical_values_parsed"] is False
    assert payload["numeric_values_extracted"] is False
    assert payload["tables_extracted"] is False
    assert "parsed_values" not in payload


def test_directory_scanner_picks_dat_files_sorted_and_non_recursive(
    tmp_path: Path,
) -> None:
    root = tmp_path / "results"
    root.mkdir()
    (root / "b.dat").write_text("TOTAL ENERGY SUMMARY\n", encoding="utf-8")
    (root / "a.dat").write_text("CalculiX header\n", encoding="utf-8")
    (root / "ignored.frd").write_text("frd not scanned\n", encoding="utf-8")
    (root / "ignored.sta").write_text("sta not scanned\n", encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    (nested / "z.dat").write_text("CalculiX nested\n", encoding="utf-8")

    scan = scan_calculix_dat_sections_directory(root)

    assert [item.name for item in scan.files] == ["a.dat", "b.dat"]
    assert scan.recursive is False
    assert scan.writes_files is False
    assert scan.summary.kind_counts[CalculiXDatSectionKind.HEADER] == 1
    assert scan.summary.kind_counts[CalculiXDatSectionKind.SCALAR_CANDIDATE] == 1


def test_dat_section_scanner_writes_no_files(tmp_path: Path) -> None:
    root = tmp_path / "results"
    root.mkdir()
    _write_dat(root / "case.dat")
    before = sorted(path.name for path in root.iterdir())

    scan = scan_calculix_dat_sections_directory(root)
    after = sorted(path.name for path in root.iterdir())

    assert scan.writes_files is False
    assert before == after


def test_result_import_model_includes_dat_section_summary(tmp_path: Path) -> None:
    root = tmp_path / "results"
    root.mkdir()
    _write_dat(root / "case.dat")

    inspection = inspect_calculix_result_directory(root)
    dat_artifact = next(
        artifact
        for artifact in inspection.artifacts
        if artifact.kind is CalculiXResultArtifactKind.DAT
    )

    assert "dat_section_summary" in dat_artifact.metadata
    assert "dat_section_scan" in dat_artifact.metadata
    assert dat_artifact.metadata["dat_section_summary"]["section_count"] >= 1
    assert dat_artifact.metadata["dat_section_summary"]["numeric_tokens_not_parsed"]


def test_explain_dat_section_scan_is_reviewer_readable(tmp_path: Path) -> None:
    scan = scan_calculix_dat_sections(_write_dat(tmp_path / "case.dat"))
    lines = explain_calculix_dat_section_scan(scan)

    assert any(".dat section file scan" in line.lower() for line in lines)
    assert any("numerical values parsed: false" in line.lower() for line in lines)
    assert any("tables extracted: false" in line.lower() for line in lines)
