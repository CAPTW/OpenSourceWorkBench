from __future__ import annotations

from osw.experimental.feaspec import (
    DiagnosticCategory,
    DiagnosticCode,
    DiagnosticSeverity,
    FEASpecValidationDiagnostic,
    FEASpecValidationReport,
    ValidationState,
)


def test_diagnostic_severity_enum_includes_required_values() -> None:
    assert {item.value for item in DiagnosticSeverity} == {
        "info",
        "warning",
        "error",
        "blocker",
    }


def test_diagnostic_categories_include_required_values() -> None:
    assert {item.value for item in DiagnosticCategory} >= {
        "schema",
        "units",
        "geometry",
        "material",
        "section",
        "boundary_condition",
        "load",
        "dimension",
        "evidence",
        "human_review",
        "solver_compatibility",
        "benchmark",
    }


def test_required_diagnostic_codes_are_available() -> None:
    assert {item.value for item in DiagnosticCode} >= {
        "FS_SCHEMA_MISSING_FIELD",
        "FS_UNITS_MISSING_SYSTEM",
        "FS_UNITS_AMBIGUOUS",
        "FS_GEOM_DUPLICATE_ID",
        "FS_GEOM_MISSING_NODE",
        "FS_GEOM_DISCONNECTED_GRAPH",
        "FS_MATERIAL_MISSING",
        "FS_SECTION_MISSING",
        "FS_BC_INVALID_TARGET",
        "FS_BC_INSUFFICIENT_CONSTRAINTS",
        "FS_LOAD_INVALID_TARGET",
        "FS_LOAD_MISSING_UNITS",
        "FS_DIMENSION_CONFLICT",
        "FS_EVIDENCE_MISSING",
        "FS_CONFIDENCE_LOW",
        "FS_REVIEW_MISSING",
        "FS_REVIEW_NOT_APPROVED",
        "FS_SOLVER_UNSUPPORTED_ELEMENT",
        "FS_SOLVER_ABAQUS_NON_DEFAULT",
        "FS_BENCHMARK_METADATA_MISSING",
    }


def test_report_properties_reflect_blocking_diagnostics() -> None:
    diagnostic = FEASpecValidationDiagnostic.make(
        DiagnosticCode.FS_LOAD_MISSING_UNITS,
        DiagnosticSeverity.BLOCKER,
        DiagnosticCategory.LOAD,
        "Load units are missing.",
    )

    report = FEASpecValidationReport(
        validation_state=ValidationState.INVALID,
        diagnostics=(diagnostic,),
    )

    assert report.diagnostics == (diagnostic,)
    assert report.has_blockers
    assert report.has_errors is False
    assert not report.is_valid
    assert not report.can_be_approved
    assert not report.can_handoff_to_solver


def test_nonblocking_warning_requires_acceptance_but_not_approval_block() -> None:
    diagnostic = FEASpecValidationDiagnostic.make(
        DiagnosticCode.FS_CONFIDENCE_LOW,
        DiagnosticSeverity.WARNING,
        DiagnosticCategory.EVIDENCE,
        "Confidence is low.",
        blocks_approval=False,
        blocks_solver_handoff=True,
    )

    assert diagnostic.blocks_approval is False
    assert diagnostic.blocks_solver_handoff is True
    assert diagnostic.to_dict()["code"] == "FS_CONFIDENCE_LOW"
