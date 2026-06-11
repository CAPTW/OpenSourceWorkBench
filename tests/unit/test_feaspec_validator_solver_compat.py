from __future__ import annotations

from pathlib import Path

from osw.experimental.feaspec import DiagnosticCode, ValidationState, validate_for_solver

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "examples" / "feaspec"


def test_validate_for_solver_calculix_passes_field_checks_for_approved_examples() -> None:
    for filename in ("cantilever_beam_approved.json", "truss_2d_approved.json"):
        report = validate_for_solver(EXAMPLES / filename, "calculix")
        assert report.validation_state is ValidationState.APPROVED
        assert not report.has_blockers
        assert not report.has_errors
        assert report.can_handoff_to_solver


def test_validate_for_solver_candidate_is_not_solver_ready() -> None:
    report = validate_for_solver(EXAMPLES / "truss_2d_candidate.json", "calculix")

    assert not report.can_handoff_to_solver
    assert DiagnosticCode.FS_REVIEW_MISSING in report.diagnostic_codes


def test_validate_for_solver_abaqus_reports_optional_non_default() -> None:
    report = validate_for_solver(EXAMPLES / "cantilever_beam_approved.json", "abaqus")

    assert DiagnosticCode.FS_SOLVER_ABAQUS_NON_DEFAULT in report.diagnostic_codes
    assert not report.can_handoff_to_solver


def test_validate_for_solver_unknown_solver_reports_unsupported() -> None:
    report = validate_for_solver(EXAMPLES / "cantilever_beam_approved.json", "nastran")

    assert DiagnosticCode.FS_SOLVER_UNSUPPORTED_ELEMENT in report.diagnostic_codes
    assert report.has_errors
    assert not report.can_handoff_to_solver
