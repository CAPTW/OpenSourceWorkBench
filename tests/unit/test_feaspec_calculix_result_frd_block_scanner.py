from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXFrdBlock,
    CalculiXFrdBlockDirectoryScan,
    CalculiXFrdBlockKind,
    CalculiXFrdBlockScan,
    CalculiXFrdBlockScanLimits,
    CalculiXFrdBlockScanStatus,
    CalculiXFrdBlockSummary,
    CalculiXFrdReferenceCandidate,
    CalculiXResultArtifactKind,
    CalculiXResultParserDiagnosticCode,
    explain_calculix_frd_block_scan,
    inspect_calculix_result_directory,
    scan_calculix_frd_blocks,
    scan_calculix_frd_blocks_directory,
)


def _write_frd(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "1C FRD HEADER",
                "job beam_case",
                "2C NODE COORDINATES",
                "1 0.0 0.0 0.0",
                "3C ELEMENT CONNECTIVITY",
                "1 1 2",
                "100C DISPLACEMENT FIELD",
                "U1 text 1.0",
                "200C RESULT BLOCK",
                "result set text",
                "400C BINARY OPAQUE BLOCK",
                "opaque text",
                "777C REVIEW RECORD",
                "unknown text",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _codes(scan: CalculiXFrdBlockScan) -> set[CalculiXResultParserDiagnosticCode]:
    return {diagnostic.code for diagnostic in scan.diagnostics}


def _kinds(scan: CalculiXFrdBlockScan) -> set[CalculiXFrdBlockKind]:
    return {block.kind for block in scan.blocks}


def test_frd_block_scanner_module_imports_and_exports_required_api() -> None:
    assert scan_calculix_frd_blocks
    assert scan_calculix_frd_blocks_directory
    assert explain_calculix_frd_block_scan
    assert CalculiXFrdBlockKind
    assert CalculiXFrdBlock
    assert CalculiXFrdReferenceCandidate
    assert CalculiXFrdBlockSummary
    assert CalculiXFrdBlockScan
    assert CalculiXFrdBlockDirectoryScan
    assert CalculiXFrdBlockScanStatus
    assert CalculiXFrdBlockScanLimits


def test_unsupported_suffix_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "result.dat"
    path.write_text("CalculiX result\n", encoding="utf-8")

    scan = scan_calculix_frd_blocks(path)

    assert scan.status is CalculiXFrdBlockScanStatus.UNSUPPORTED
    assert CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT in _codes(scan)


def test_frd_file_is_accepted_and_classifies_required_block_kinds(
    tmp_path: Path,
) -> None:
    scan = scan_calculix_frd_blocks(_write_frd(tmp_path / "case.frd"))
    kinds = _kinds(scan)

    assert scan.suffix == ".frd"
    assert scan.artifact_kind == "frd"
    assert CalculiXFrdBlockKind.HEADER in kinds
    assert CalculiXFrdBlockKind.NODE_REFERENCE_CANDIDATE in kinds
    assert CalculiXFrdBlockKind.ELEMENT_REFERENCE_CANDIDATE in kinds
    assert CalculiXFrdBlockKind.FIELD_REFERENCE_CANDIDATE in kinds
    assert CalculiXFrdBlockKind.RESULT_BLOCK_CANDIDATE in kinds
    assert CalculiXFrdBlockKind.UNSUPPORTED in kinds
    assert CalculiXFrdBlockKind.UNKNOWN in kinds
    assert scan.summary.numeric_tokens_not_parsed is True
    assert scan.numerical_values_parsed is False
    assert scan.field_values_parsed is False
    assert scan.mesh_reconstructed is False
    assert scan.visualization_arrays_built is False


def test_reference_candidates_are_deferred_and_categorized(tmp_path: Path) -> None:
    scan = scan_calculix_frd_blocks(_write_frd(tmp_path / "case.frd"))

    reference_kinds = {candidate.reference_kind for candidate in scan.reference_candidates}
    assert {"node", "element", "field", "result", "unknown"} <= reference_kinds
    assert all(candidate.values_parsed is False for candidate in scan.reference_candidates)
    assert all(candidate.mesh_reconstructed is False for candidate in scan.reference_candidates)
    assert all(candidate.units_inferred is False for candidate in scan.reference_candidates)
    assert scan.summary.field_reference_candidate_count == 1
    assert scan.summary.mesh_reference_candidate_count == 2
    assert (
        CalculiXResultParserDiagnosticCode.FP_FRD_REFERENCE_CANDIDATE_ONLY
        in _codes(scan)
    )


def test_unknown_and_unsupported_blocks_are_preserved_with_diagnostics(
    tmp_path: Path,
) -> None:
    scan = scan_calculix_frd_blocks(_write_frd(tmp_path / "case.frd"))

    assert any(block.kind is CalculiXFrdBlockKind.UNKNOWN for block in scan.blocks)
    assert any(block.unsupported for block in scan.blocks)
    assert CalculiXResultParserDiagnosticCode.FP_FRD_UNKNOWN_RECORD in _codes(scan)
    assert CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_UNSUPPORTED in _codes(scan)


def test_no_recognized_blocks_produces_diagnostic(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_text("opaque lowercase line\nanother opaque line\n", encoding="utf-8")

    scan = scan_calculix_frd_blocks(path)

    assert scan.blocks == ()
    assert (
        CalculiXResultParserDiagnosticCode.FP_FRD_NO_RECOGNIZED_BLOCKS
        in _codes(scan)
    )


def test_block_spans_heading_lines_and_snippets_are_deterministic(
    tmp_path: Path,
) -> None:
    path = tmp_path / "case.frd"
    path.write_text(
        "1C FRD HEADER\nheader detail\n2C NODE COORDINATES\nnode 1 0 0 0\n",
        encoding="utf-8",
    )

    first = scan_calculix_frd_blocks(path)
    second = scan_calculix_frd_blocks(path)

    assert [block.to_dict() for block in first.blocks] == [
        block.to_dict() for block in second.blocks
    ]
    assert first.blocks[0].heading_line_number == 1
    assert first.blocks[0].line_start == 1
    assert first.blocks[0].line_end == 2
    assert first.blocks[1].heading_line_number == 3
    assert "node 1 0 0 0" in first.blocks[1].snippets


def test_numeric_tokens_remain_text_snippets_only(tmp_path: Path) -> None:
    path = tmp_path / "case.frd"
    path.write_text(
        "100C DISPLACEMENT FIELD\n1 1.234E-05 2.0\n",
        encoding="utf-8",
    )

    scan = scan_calculix_frd_blocks(path)
    payload = scan.to_dict()

    assert scan.summary.numeric_tokens_not_parsed is True
    assert scan.blocks[0].numeric_tokens_present is True
    assert "1.234E-05" in scan.blocks[0].snippets[1]
    assert CalculiXResultParserDiagnosticCode.FP_FRD_FIELD_VALUES_NOT_PARSED in _codes(
        scan
    )
    assert payload["numerical_values_parsed"] is False
    assert payload["field_values_parsed"] is False
    assert payload["numeric_values_extracted"] is False
    assert payload["mesh_reconstructed"] is False
    assert "parsed_values" not in payload


def test_directory_scanner_picks_frd_files_sorted_and_non_recursive(
    tmp_path: Path,
) -> None:
    root = tmp_path / "results"
    root.mkdir()
    (root / "b.frd").write_text("100C DISPLACEMENT FIELD\n", encoding="utf-8")
    (root / "a.frd").write_text("1C FRD HEADER\n", encoding="utf-8")
    (root / "ignored.dat").write_text("dat not scanned\n", encoding="utf-8")
    (root / "ignored.sta").write_text("sta not scanned\n", encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    (nested / "z.frd").write_text("1C FRD HEADER\n", encoding="utf-8")

    scan = scan_calculix_frd_blocks_directory(root)

    assert [item.name for item in scan.files] == ["a.frd", "b.frd"]
    assert scan.recursive is False
    assert scan.writes_files is False
    assert scan.summary.kind_counts[CalculiXFrdBlockKind.HEADER] == 1
    assert scan.summary.kind_counts[CalculiXFrdBlockKind.FIELD_REFERENCE_CANDIDATE] == 1


def test_frd_block_scanner_writes_no_files(tmp_path: Path) -> None:
    root = tmp_path / "results"
    root.mkdir()
    _write_frd(root / "case.frd")
    before = sorted(path.name for path in root.iterdir())

    scan = scan_calculix_frd_blocks_directory(root)
    after = sorted(path.name for path in root.iterdir())

    assert scan.writes_files is False
    assert before == after


def test_result_import_model_includes_frd_block_summary(tmp_path: Path) -> None:
    root = tmp_path / "results"
    root.mkdir()
    _write_frd(root / "case.frd")

    inspection = inspect_calculix_result_directory(root)
    frd_artifact = next(
        artifact
        for artifact in inspection.artifacts
        if artifact.kind is CalculiXResultArtifactKind.FRD
    )

    assert "frd_block_summary" in frd_artifact.metadata
    assert "frd_block_scan" in frd_artifact.metadata
    assert frd_artifact.metadata["frd_block_summary"]["block_count"] >= 1
    assert frd_artifact.metadata["frd_block_summary"]["numeric_tokens_not_parsed"]


def test_explain_frd_block_scan_is_reviewer_readable(tmp_path: Path) -> None:
    scan = scan_calculix_frd_blocks(_write_frd(tmp_path / "case.frd"))
    lines = explain_calculix_frd_block_scan(scan)

    assert any(".frd block file scan" in line.lower() for line in lines)
    assert any("numerical field values parsed: false" in line.lower() for line in lines)
    assert any("mesh reconstructed: false" in line.lower() for line in lines)
