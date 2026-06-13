from __future__ import annotations

from osw.experimental.feaspec import (
    CalculiXExportDiagnosticCode,
    CalculiXExportSeverity,
    FEASpecCalculiXExportDiagnostic,
)

REQUIRED_FX_CODES = {
    "FX_RENDER_BLOCKED",
    "FX_OUTPUT_DIR_MISSING",
    "FX_OUTPUT_DIR_NOT_DIRECTORY",
    "FX_OUTPUT_DIR_NOT_EMPTY",
    "FX_UNSAFE_BASENAME",
    "FX_OUTPUT_EXISTS",
    "FX_WRITE_FAILED",
    "FX_MANIFEST_WRITE_FAILED",
    "FX_DIAGNOSTICS_WRITE_FAILED",
    "FX_README_WRITE_FAILED",
    "FX_CHECKSUM_FAILED",
    "FX_SOLVER_RUN_FORBIDDEN",
}


def test_required_export_diagnostic_codes_are_defined() -> None:
    assert {code.value for code in CalculiXExportDiagnosticCode} == REQUIRED_FX_CODES


def test_export_severity_values_are_stable() -> None:
    assert {severity.value for severity in CalculiXExportSeverity} == {
        "info",
        "warning",
        "error",
        "blocker",
    }


def test_export_diagnostic_defaults_block_error_and_blocker_severity() -> None:
    info = FEASpecCalculiXExportDiagnostic.make(
        CalculiXExportDiagnosticCode.FX_SOLVER_RUN_FORBIDDEN,
        CalculiXExportSeverity.INFO,
        "No solver run is allowed from the exporter.",
    )
    blocker = FEASpecCalculiXExportDiagnostic.make(
        CalculiXExportDiagnosticCode.FX_OUTPUT_EXISTS,
        CalculiXExportSeverity.BLOCKER,
        "Output exists.",
    )

    assert info.blocks_export is False
    assert blocker.blocks_export is True


def test_export_diagnostic_serializes_to_stable_dict() -> None:
    diagnostic = FEASpecCalculiXExportDiagnostic.make(
        CalculiXExportDiagnosticCode.FX_UNSAFE_BASENAME,
        CalculiXExportSeverity.BLOCKER,
        "Unsafe basename.",
        path="../bad",
        suggested_fix="Use a plain filename stem.",
    )

    assert diagnostic.to_dict() == {
        "code": "FX_UNSAFE_BASENAME",
        "severity": "blocker",
        "message": "Unsafe basename.",
        "path": "../bad",
        "suggested_fix": "Use a plain filename stem.",
        "blocks_export": True,
    }
