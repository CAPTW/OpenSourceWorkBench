from __future__ import annotations

from osw.experimental.feaspec import (
    CalculiXResultImportDiagnosticCode,
    CalculiXResultImportSeverity,
    FEASpecCalculiXResultImportDiagnostic,
)

REQUIRED_FI_CODES = {
    "FI_RESULT_DIR_MISSING",
    "FI_RESULT_DIR_NOT_DIRECTORY",
    "FI_MANIFEST_MISSING",
    "FI_RUN_METADATA_MISSING",
    "FI_EXPORT_MANIFEST_MISSING",
    "FI_UNSUPPORTED_FILE",
    "FI_PARSE_NOT_IMPLEMENTED",
    "FI_PARTIAL_IMPORT",
    "FI_NO_PRIMARY_RESULT",
    "FI_RUN_FAILED",
    "FI_RUN_TIMED_OUT",
    "FI_SOLVER_NOT_EXECUTED",
    "FI_PROVENANCE_INCOMPLETE",
    "FI_FORBIDDEN_PATH",
    "FI_RESULT_DATASET_WRITE_FORBIDDEN",
}


def test_all_result_import_diagnostic_codes_exist() -> None:
    assert REQUIRED_FI_CODES.issubset(
        {item.value for item in CalculiXResultImportDiagnosticCode}
    )


def test_result_import_severity_values_exist() -> None:
    assert {item.value for item in CalculiXResultImportSeverity} == {
        "info",
        "warning",
        "error",
        "blocker",
    }


def test_result_import_diagnostic_serializes_and_blocks_by_severity() -> None:
    diagnostic = FEASpecCalculiXResultImportDiagnostic.make(
        CalculiXResultImportDiagnosticCode.FI_RESULT_DIR_MISSING,
        CalculiXResultImportSeverity.BLOCKER,
        "missing",
        path="results",
        suggested_fix="choose a directory",
    )

    assert diagnostic.blocks_import is True
    assert diagnostic.to_dict() == {
        "code": "FI_RESULT_DIR_MISSING",
        "severity": "blocker",
        "message": "missing",
        "path": "results",
        "suggested_fix": "choose a directory",
        "blocks_import": True,
    }


def test_warning_can_be_nonblocking() -> None:
    diagnostic = FEASpecCalculiXResultImportDiagnostic.make(
        CalculiXResultImportDiagnosticCode.FI_PARSE_NOT_IMPLEMENTED,
        CalculiXResultImportSeverity.WARNING,
        "future parser",
        blocks_import=False,
    )

    assert diagnostic.blocks_import is False
