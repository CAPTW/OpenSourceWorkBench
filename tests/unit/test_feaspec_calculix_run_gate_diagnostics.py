from __future__ import annotations

from osw.experimental.feaspec.calculix_run_diagnostics import (
    CalculiXRunDiagnosticCode,
    CalculiXRunSeverity,
    FEASpecCalculiXRunDiagnostic,
)

REQUIRED_CODES = {
    "FR_RUN_NOT_AUTHORIZED",
    "FR_EXECUTE_FLAG_REQUIRED",
    "FR_CONFIRMATION_REQUIRED",
    "FR_README_NOT_ACKNOWLEDGED",
    "FR_CCX_MISSING",
    "FR_CCX_NOT_EXECUTABLE",
    "FR_EXPORT_BUNDLE_INVALID",
    "FR_MANIFEST_MISSING",
    "FR_INP_MISSING",
    "FR_README_MISSING",
    "FR_RUN_DIR_UNSAFE",
    "FR_RUN_DIR_NOT_EMPTY",
    "FR_TIMEOUT",
    "FR_NONZERO_EXIT",
    "FR_OUTPUT_MISSING",
    "FR_FORBIDDEN_PATH",
    "FR_METADATA_WRITE_FAILED",
    "FR_PROCESS_START_FAILED",
}


def test_all_required_fr_diagnostic_codes_exist() -> None:
    assert REQUIRED_CODES.issubset({item.name for item in CalculiXRunDiagnosticCode})
    assert REQUIRED_CODES.issubset({item.value for item in CalculiXRunDiagnosticCode})


def test_required_severity_values_exist() -> None:
    assert {item.value for item in CalculiXRunSeverity} == {
        "info",
        "warning",
        "error",
        "blocker",
    }


def test_diagnostic_make_marks_errors_and_blockers_as_execution_blocking() -> None:
    warning = FEASpecCalculiXRunDiagnostic.make(
        CalculiXRunDiagnosticCode.FR_CCX_MISSING,
        CalculiXRunSeverity.WARNING,
        "ccx missing",
    )
    blocker = FEASpecCalculiXRunDiagnostic.make(
        CalculiXRunDiagnosticCode.FR_CONFIRMATION_REQUIRED,
        CalculiXRunSeverity.BLOCKER,
        "confirmation required",
    )

    assert warning.blocks_execution is False
    assert blocker.blocks_execution is True
    assert blocker.to_dict() == {
        "code": "FR_CONFIRMATION_REQUIRED",
        "severity": "blocker",
        "message": "confirmation required",
        "path": "",
        "suggested_fix": "",
        "blocks_execution": True,
    }


def test_diagnostic_make_can_force_execution_blocking_for_missing_ccx() -> None:
    diagnostic = FEASpecCalculiXRunDiagnostic.make(
        CalculiXRunDiagnosticCode.FR_CCX_MISSING,
        CalculiXRunSeverity.WARNING,
        "ccx missing",
        blocks_execution=True,
    )

    assert diagnostic.blocks_execution is True
