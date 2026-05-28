"""Validation helpers for bounded OpenFOAM template requests."""

from __future__ import annotations

from osw.core.diagnostics import DiagnosticReport
from osw.solvers.openfoam.case_generator import validate_case_request
from osw.solvers.openfoam.model import OpenFOAMCaseRequest


def validate_openfoam_case_request(request: OpenFOAMCaseRequest) -> DiagnosticReport:
    """Validate cavity/duct template readiness without running OpenFOAM."""

    return validate_case_request(request)
