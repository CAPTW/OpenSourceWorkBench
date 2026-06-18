from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXResultArtifactKind,
    CalculiXResultParserDiagnosticCode,
    CalculiXStatusDirectoryScan,
    CalculiXStatusFileScan,
    CalculiXStatusLine,
    CalculiXStatusLineCategory,
    CalculiXStatusScanLimits,
    CalculiXStatusScanStatus,
    CalculiXStatusSummary,
    explain_calculix_status_scan,
    inspect_calculix_result_directory,
    scan_calculix_status_directory,
    scan_calculix_status_file,
)


def _write_status_file(path: Path) -> Path:
    path.write_text(
        "\n".join(
            [
                "CalculiX job started",
                "STEP 1 INCREMENT 2 TIME 3.0",
                "convergence residual 1.0E-03 is reported",
                "WARNING contact pair was adjusted",
                "ERROR element set is missing",
                "analysis completed",
                "solution failed after cutback",
                "opaque tail line",
            ]
        ),
        encoding="utf-8",
    )
    return path


def _codes(scan: CalculiXStatusFileScan) -> set[CalculiXResultParserDiagnosticCode]:
    return {diagnostic.code for diagnostic in scan.diagnostics}


def test_status_scanner_module_imports_and_public_api_exports_required_types() -> None:
    assert scan_calculix_status_file
    assert scan_calculix_status_directory
    assert explain_calculix_status_scan
    assert CalculiXStatusLineCategory
    assert CalculiXStatusLine
    assert CalculiXStatusSummary
    assert CalculiXStatusFileScan
    assert CalculiXStatusDirectoryScan
    assert CalculiXStatusScanStatus
    assert CalculiXStatusScanLimits


def test_unsupported_suffix_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "result.dat"
    path.write_text("convergence residual 1.0\n", encoding="utf-8")

    scan = scan_calculix_status_file(path)

    assert scan.status is CalculiXStatusScanStatus.UNSUPPORTED
    assert CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT in _codes(scan)


def test_sta_file_is_accepted_and_classifies_required_categories(tmp_path: Path) -> None:
    scan = scan_calculix_status_file(_write_status_file(tmp_path / "case.sta"))
    counts = scan.summary.category_counts

    assert scan.suffix == ".sta"
    assert scan.artifact_kind == "sta"
    assert counts[CalculiXStatusLineCategory.INFORMATIONAL] == 1
    assert counts[CalculiXStatusLineCategory.PROGRESS] == 1
    assert counts[CalculiXStatusLineCategory.CONVERGENCE] == 1
    assert counts[CalculiXStatusLineCategory.WARNING] == 1
    assert counts[CalculiXStatusLineCategory.ERROR] == 1
    assert counts[CalculiXStatusLineCategory.COMPLETION] == 1
    assert counts[CalculiXStatusLineCategory.FAILURE] == 1
    assert counts[CalculiXStatusLineCategory.UNKNOWN] == 1
    assert scan.summary.completion_indicated is True
    assert scan.summary.failure_indicated is True
    assert scan.summary.numeric_tokens_not_parsed is True


def test_cvg_file_is_accepted(tmp_path: Path) -> None:
    path = tmp_path / "case.cvg"
    path.write_text("convergence iteration 1 residual 0.1\n", encoding="utf-8")

    scan = scan_calculix_status_file(path)

    assert scan.suffix == ".cvg"
    assert scan.artifact_kind == "cvg"
    assert scan.summary.category_counts[CalculiXStatusLineCategory.CONVERGENCE] == 1
    assert scan.summary.numeric_tokens_not_parsed is True


def test_line_numbers_and_bounded_snippets_are_preserved(tmp_path: Path) -> None:
    path = tmp_path / "case.sta"
    path.write_text("first unknown\nWARNING " + ("x" * 80), encoding="utf-8")

    scan = scan_calculix_status_file(
        path,
        limits=CalculiXStatusScanLimits(max_snippet_chars=20),
    )

    assert [line.line_number for line in scan.lines] == [1, 2]
    assert scan.lines[1].category is CalculiXStatusLineCategory.WARNING
    assert len(scan.lines[1].snippet) == 20
    assert len(scan.lines[1].raw_text_snippet) == 20


def test_category_counts_are_deterministic(tmp_path: Path) -> None:
    path = _write_status_file(tmp_path / "case.sta")

    first = scan_calculix_status_file(path).summary.to_dict()
    second = scan_calculix_status_file(path).summary.to_dict()

    assert first["category_counts"] == second["category_counts"]


def test_directory_scanner_picks_status_files_sorted_and_non_recursive(
    tmp_path: Path,
) -> None:
    root = tmp_path / "results"
    root.mkdir()
    (root / "b.cvg").write_text("convergence residual 1.0\n", encoding="utf-8")
    (root / "a.sta").write_text("step 1 increment 1\n", encoding="utf-8")
    (root / "ignored.dat").write_text("dat is not scanned here\n", encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    (nested / "z.sta").write_text("completion\n", encoding="utf-8")

    scan = scan_calculix_status_directory(root)

    assert [item.name for item in scan.files] == ["a.sta", "b.cvg"]
    assert scan.recursive is False
    assert scan.writes_files is False
    assert scan.summary.category_counts[CalculiXStatusLineCategory.PROGRESS] == 1
    assert scan.summary.category_counts[CalculiXStatusLineCategory.CONVERGENCE] == 1


def test_status_scanner_writes_no_files(tmp_path: Path) -> None:
    root = tmp_path / "results"
    root.mkdir()
    _write_status_file(root / "case.sta")
    before = sorted(path.name for path in root.iterdir())

    scan = scan_calculix_status_directory(root)
    after = sorted(path.name for path in root.iterdir())

    assert scan.writes_files is False
    assert before == after


def test_result_import_model_includes_status_summary_for_sta_cvg(
    tmp_path: Path,
) -> None:
    root = tmp_path / "results"
    root.mkdir()
    _write_status_file(root / "case.sta")
    (root / "case.cvg").write_text("convergence residual 0.5\n", encoding="utf-8")

    inspection = inspect_calculix_result_directory(root)
    artifacts = {
        artifact.kind: artifact
        for artifact in inspection.artifacts
        if artifact.kind in {CalculiXResultArtifactKind.STA, CalculiXResultArtifactKind.CVG}
    }

    assert "status_summary" in artifacts[CalculiXResultArtifactKind.STA].metadata
    assert "status_scan" in artifacts[CalculiXResultArtifactKind.CVG].metadata
    assert artifacts[CalculiXResultArtifactKind.STA].metadata["status_summary"][
        "numeric_tokens_not_parsed"
    ] is True


def test_explain_status_scan_is_reviewer_readable(tmp_path: Path) -> None:
    scan = scan_calculix_status_file(_write_status_file(tmp_path / "case.sta"))
    lines = explain_calculix_status_scan(scan)

    assert any("status file scan" in line.lower() for line in lines)
    assert any("numerical convergence values parsed: false" in line.lower() for line in lines)
