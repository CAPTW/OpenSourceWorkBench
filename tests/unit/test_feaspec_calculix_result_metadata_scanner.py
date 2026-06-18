from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import (
    CalculiXResultMetadataLimits,
    CalculiXResultMetadataStatus,
    CalculiXResultParserDiagnosticCode,
    scan_calculix_result_directory_metadata,
    scan_calculix_result_file_metadata,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNER_SOURCE = (
    REPO_ROOT
    / "src"
    / "osw"
    / "experimental"
    / "feaspec"
    / "calculix_result_metadata_scanner.py"
)


def _write_text(path: Path, payload: str) -> None:
    path.write_bytes(payload.encode("utf-8"))


def test_scanner_module_exports_and_basic_api() -> None:
    assert scan_calculix_result_file_metadata
    assert scan_calculix_result_directory_metadata
    assert CalculiXResultMetadataLimits
    assert CalculiXResultMetadataStatus


def test_missing_file_scans_as_blocked_with_fp_file_missing(tmp_path: Path) -> None:
    scan = scan_calculix_result_file_metadata(tmp_path / "missing.dat")

    assert scan.status is CalculiXResultMetadataStatus.BLOCKED
    assert scan.exists is False
    assert CalculiXResultParserDiagnosticCode.FP_FILE_MISSING in {
        item.code for item in scan.diagnostics
    }


def test_directory_path_passed_to_file_scanner_flags_path_not_file(tmp_path: Path) -> None:
    directory = tmp_path / "dir"
    directory.mkdir()
    scan = scan_calculix_result_file_metadata(directory)

    assert scan.status is CalculiXResultMetadataStatus.BLOCKED
    assert scan.is_file is False
    assert CalculiXResultParserDiagnosticCode.FP_PATH_NOT_FILE in {
        item.code for item in scan.diagnostics
    }


def test_unsupported_suffix_is_flagged(tmp_path: Path) -> None:
    path = tmp_path / "notes.tmp"
    _write_text(path, "unsupported")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.artifact_kind == "other"
    assert scan.status is CalculiXResultMetadataStatus.UNSUPPORTED
    assert CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT in {
        item.code for item in scan.diagnostics
    }


def test_dat_file_is_classified_as_dat(tmp_path: Path) -> None:
    path = tmp_path / "result.dat"
    _write_text(path, "dat text")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.suffix == ".dat"
    assert scan.artifact_kind == "dat"


def test_frd_file_is_classified_as_frd(tmp_path: Path) -> None:
    path = tmp_path / "result.frd"
    _write_text(path, "frd text")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.suffix == ".frd"
    assert scan.artifact_kind == "frd"


def test_sta_file_is_classified_as_sta(tmp_path: Path) -> None:
    path = tmp_path / "result.sta"
    _write_text(path, "sta text")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.suffix == ".sta"
    assert scan.artifact_kind == "sta"


def test_cvg_file_is_classified_as_cvg(tmp_path: Path) -> None:
    path = tmp_path / "result.cvg"
    _write_text(path, "cvg text")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.suffix == ".cvg"
    assert scan.artifact_kind == "cvg"


def test_inp_file_is_classified_as_inp(tmp_path: Path) -> None:
    path = tmp_path / "mesh.inp"
    _write_text(path, "*NODE")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.suffix == ".inp"
    assert scan.artifact_kind == "inp"


def test_sha256_hash_is_deterministic_for_repeated_scan(tmp_path: Path) -> None:
    path = tmp_path / "mesh.inp"
    _write_text(path, "*NODE")

    first = scan_calculix_result_file_metadata(path)
    second = scan_calculix_result_file_metadata(path)

    assert first.sha256 == second.sha256
    assert first.sha256


def test_byte_size_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    payload = "line-one\nline-two\n"
    _write_text(path, payload)

    scan = scan_calculix_result_file_metadata(path)

    assert scan.byte_size == len(payload.encode("utf-8"))


def test_line_count_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    _write_text(path, "a\nb\nc\n")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.line_count == 3
    assert scan.line_count_truncated is False


def test_line_limit_reports_truncation(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    _write_text(path, "a\nb\nc\nd\n")

    scan = scan_calculix_result_file_metadata(
        path,
        limits=CalculiXResultMetadataLimits(max_lines=2),
    )

    assert scan.line_count == 2
    assert scan.line_count_truncated is True
    assert CalculiXResultParserDiagnosticCode.FP_LINE_LIMIT_EXCEEDED in {
        item.code for item in scan.diagnostics
    }


def test_size_limit_reports_truncation(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    payload = "This file is definitely larger than eight bytes."
    _write_text(path, payload)

    scan = scan_calculix_result_file_metadata(
        path,
        limits=CalculiXResultMetadataLimits(max_file_bytes=8),
    )

    assert scan.byte_size > 8
    assert scan.status is CalculiXResultMetadataStatus.LIMIT_EXCEEDED
    assert CalculiXResultParserDiagnosticCode.FP_SIZE_LIMIT_EXCEEDED in {
        item.code for item in scan.diagnostics
    }


def test_first_line_snippets_are_captured(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    _write_text(path, "first\nsecond\nthird\n")

    scan = scan_calculix_result_file_metadata(
        path,
        limits=CalculiXResultMetadataLimits(max_snippet_lines=2),
    )

    assert scan.first_line_snippets == ("first", "second")
    assert scan.snippet_truncated


def test_last_line_snippets_are_captured(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    _write_text(path, "first\nsecond\nthird\n")

    scan = scan_calculix_result_file_metadata(
        path,
        limits=CalculiXResultMetadataLimits(max_snippet_lines=2),
    )

    assert scan.last_line_snippets == ("second", "third")
    assert scan.snippet_truncated


def test_utf8_sig_is_reported_for_bom_text(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    path.write_bytes(b"\xef\xbb\xbffirst\nsecond\n")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.encoding == "utf-8-sig"
    assert scan.encoding_supported is True
    assert scan.first_line_snippets == ("first", "second")


def test_snippet_truncation_is_recorded(tmp_path: Path) -> None:
    path = tmp_path / "result.txt"
    _write_text(path, "abcdefghijkl\n")

    scan = scan_calculix_result_file_metadata(
        path,
        limits=CalculiXResultMetadataLimits(max_snippet_chars=4, max_snippet_lines=1),
    )

    assert scan.snippet_truncated is True
    assert CalculiXResultParserDiagnosticCode.FP_SNIPPET_TRUNCATED in {
        item.code for item in scan.diagnostics
    }


def test_binaryish_bytes_do_not_crash_scanner(tmp_path: Path) -> None:
    path = tmp_path / "binary.bin"
    path.write_bytes(b"\x00\xff\x00\xff")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.exists is True
    assert scan.byte_size == 4
    assert scan.line_count == 1
    assert CalculiXResultParserDiagnosticCode.FP_ENCODING_UNSUPPORTED in {
        item.code for item in scan.diagnostics
    }


def test_encoding_fallback_is_deterministic_when_utf8_fails(tmp_path: Path) -> None:
    path = tmp_path / "unicode.bin"
    path.write_bytes(b"\xff\xfe\x61\x00\x62\x00")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.encoding == "utf-8-replaced"
    assert scan.encoding_supported is False


def test_dat_scan_marks_parse_not_implemented(tmp_path: Path) -> None:
    path = tmp_path / "result.dat"
    _write_text(path, "placeholder")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.parse_not_implemented is True
    assert CalculiXResultParserDiagnosticCode.FP_PARSE_NOT_IMPLEMENTED in {
        item.code for item in scan.diagnostics
    }
    assert CalculiXResultParserDiagnosticCode.FP_METADATA_ONLY in {
        item.code for item in scan.diagnostics
    }


def test_frd_scan_marks_parse_not_implemented(tmp_path: Path) -> None:
    path = tmp_path / "result.frd"
    _write_text(path, "placeholder")

    scan = scan_calculix_result_file_metadata(path)

    assert scan.parse_not_implemented is True


def test_sta_and_cvg_scans_are_marked_metadata_only(tmp_path: Path) -> None:
    sta_path = tmp_path / "result.sta"
    cvg_path = tmp_path / "result.cvg"
    _write_text(sta_path, "status")
    _write_text(cvg_path, "status")

    sta_scan = scan_calculix_result_file_metadata(sta_path)
    cvg_scan = scan_calculix_result_file_metadata(cvg_path)

    assert sta_scan.parse_not_implemented is True
    assert cvg_scan.parse_not_implemented is True


def test_directory_scan_orders_artifacts_deterministically(tmp_path: Path) -> None:
    _write_text(tmp_path / "z.dat", "z")
    _write_text(tmp_path / "a.dat", "a")
    _write_text(tmp_path / "m.txt", "m")

    scan = scan_calculix_result_directory_metadata(tmp_path)

    names = [item.name for item in scan.artifacts]
    assert names == sorted(names)


def test_directory_scan_does_not_recurse_by_default(tmp_path: Path) -> None:
    _write_text(tmp_path / "root.txt", "root")
    nested = tmp_path / "nested"
    nested.mkdir()
    _write_text(nested / "nested.dat", "nested")

    scan = scan_calculix_result_directory_metadata(tmp_path)
    assert "nested.dat" not in {item.name for item in scan.artifacts}
    assert len(scan.artifacts) == 1


def test_directory_scan_does_not_write_files(tmp_path: Path) -> None:
    _write_text(tmp_path / "result.dat", "no write")
    before = sorted(path.name for path in tmp_path.iterdir() if path.is_file())

    scan = scan_calculix_result_directory_metadata(tmp_path)

    after = sorted(path.name for path in tmp_path.iterdir() if path.is_file())
    assert before == after
    assert scan.status is not CalculiXResultMetadataStatus.BLOCKED


def test_scanner_has_no_numeric_parsing_or_unit_inference() -> None:
    content = SCANNER_SOURCE.read_text(encoding="utf-8").lower()

    assert "float(" not in content
    assert "int(" not in content
    assert "units" not in content


def test_scanner_does_not_execute_external_commands_or_solver_calls() -> None:
    content = SCANNER_SOURCE.read_text(encoding="utf-8").lower()

    forbidden_tokens = (
        "subprocess",
        "popen",
        "os.system",
        "run(",
        "ccx.exe",
        "calculix_runner",
        "solveradapter",
        "write_text(",
        "write_bytes(",
        "mkdir(",
    )
    for token in forbidden_tokens:
        assert token not in content
