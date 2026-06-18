from __future__ import annotations

from osw.experimental.feaspec import (
    CalculiXResultParserDiagnosticCode,
    CalculiXResultParserSeverity,
    FEASpecCalculiXResultParserDiagnostic,
)


def test_all_parser_diagnostic_codes_are_defined() -> None:
    assert {item.value for item in CalculiXResultParserDiagnosticCode} == {
        "FP_FILE_MISSING",
        "FP_PATH_NOT_FILE",
        "FP_UNSUPPORTED_FORMAT",
        "FP_SIZE_LIMIT_EXCEEDED",
        "FP_LINE_LIMIT_EXCEEDED",
        "FP_ENCODING_UNSUPPORTED",
        "FP_PARSE_NOT_IMPLEMENTED",
        "FP_PARTIAL_PARSE",
        "FP_UNSUPPORTED_SECTION",
        "FP_UNSUPPORTED_RESULT_BLOCK",
        "FP_NUMERIC_CONVERSION_FAILED",
        "FP_NO_PRIMARY_FIELD",
        "FP_UNITS_MISSING",
        "FP_PROVENANCE_MISSING",
        "FP_SOLVER_RUN_FAILED",
        "FP_FORBIDDEN_PATH",
        "FP_EXTERNAL_COMMAND_FORBIDDEN",
        "FP_RESULT_DATASET_WRITE_FORBIDDEN",
        "FP_SNIPPET_TRUNCATED",
        "FP_HASH_FAILED",
        "FP_METADATA_ONLY",
        "FP_STATUS_SCAN_ONLY",
        "FP_STATUS_PATTERN_UNSUPPORTED",
        "FP_STATUS_NO_RECOGNIZED_LINES",
        "FP_STATUS_PARTIAL_SUMMARY",
        "FP_STATUS_NUMERIC_VALUES_NOT_PARSED",
    }


def test_all_parser_severity_values_are_defined() -> None:
    assert {item.value for item in CalculiXResultParserSeverity} == {
        "info",
        "warning",
        "error",
        "blocker",
    }


def test_parser_diagnostic_defaults_are_blocking_for_errors() -> None:
    blocked = FEASpecCalculiXResultParserDiagnostic.make(
        CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
        CalculiXResultParserSeverity.BLOCKER,
        "missing",
        path="/missing.dat",
    )
    warning = FEASpecCalculiXResultParserDiagnostic.make(
        CalculiXResultParserDiagnosticCode.FP_PARSE_NOT_IMPLEMENTED,
        CalculiXResultParserSeverity.WARNING,
        "future",
        path="/future.dat",
        blocks_parse=False,
        blocks_import=False,
    )

    assert blocked.blocks_parse is True
    assert blocked.blocks_import is True
    assert warning.blocks_parse is False
    assert warning.blocks_import is False


def test_parser_diagnostic_serializes_as_expected() -> None:
    payload = FEASpecCalculiXResultParserDiagnostic.make(
        CalculiXResultParserDiagnosticCode.FP_METADATA_ONLY,
        CalculiXResultParserSeverity.WARNING,
        "metadata-only",
        path="/path/to/file.dat",
        artifact_kind="dat",
        suggested_fix="use later parser phase",
        blocks_parse=False,
        blocks_import=False,
    ).to_dict()

    assert payload == {
        "code": "FP_METADATA_ONLY",
        "severity": "warning",
        "message": "metadata-only",
        "path": "/path/to/file.dat",
        "artifact_kind": "dat",
        "suggested_fix": "use later parser phase",
        "blocks_parse": False,
        "blocks_import": False,
    }
