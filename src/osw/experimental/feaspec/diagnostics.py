"""Structured diagnostics for the experimental FEASpec validator."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

from .models import ValidationState


class DiagnosticSeverity(str, Enum):
    """Validator diagnostic severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class DiagnosticCategory(str, Enum):
    """Validator diagnostic category."""

    SCHEMA = "schema"
    UNITS = "units"
    GEOMETRY = "geometry"
    MATERIAL = "material"
    SECTION = "section"
    BOUNDARY_CONDITION = "boundary_condition"
    LOAD = "load"
    DIMENSION = "dimension"
    EVIDENCE = "evidence"
    HUMAN_REVIEW = "human_review"
    SOLVER_COMPATIBILITY = "solver_compatibility"
    BENCHMARK = "benchmark"


class DiagnosticCode(str, Enum):
    """Stable diagnostic code catalog reserved by the validator design."""

    FS_SCHEMA_MISSING_FIELD = "FS_SCHEMA_MISSING_FIELD"
    FS_UNITS_MISSING_SYSTEM = "FS_UNITS_MISSING_SYSTEM"
    FS_UNITS_AMBIGUOUS = "FS_UNITS_AMBIGUOUS"
    FS_GEOM_DUPLICATE_ID = "FS_GEOM_DUPLICATE_ID"
    FS_GEOM_MISSING_NODE = "FS_GEOM_MISSING_NODE"
    FS_GEOM_DISCONNECTED_GRAPH = "FS_GEOM_DISCONNECTED_GRAPH"
    FS_MATERIAL_MISSING = "FS_MATERIAL_MISSING"
    FS_SECTION_MISSING = "FS_SECTION_MISSING"
    FS_BC_INVALID_TARGET = "FS_BC_INVALID_TARGET"
    FS_BC_INSUFFICIENT_CONSTRAINTS = "FS_BC_INSUFFICIENT_CONSTRAINTS"
    FS_LOAD_INVALID_TARGET = "FS_LOAD_INVALID_TARGET"
    FS_LOAD_MISSING_UNITS = "FS_LOAD_MISSING_UNITS"
    FS_DIMENSION_CONFLICT = "FS_DIMENSION_CONFLICT"
    FS_EVIDENCE_MISSING = "FS_EVIDENCE_MISSING"
    FS_CONFIDENCE_LOW = "FS_CONFIDENCE_LOW"
    FS_REVIEW_MISSING = "FS_REVIEW_MISSING"
    FS_REVIEW_NOT_APPROVED = "FS_REVIEW_NOT_APPROVED"
    FS_SOLVER_UNSUPPORTED_ELEMENT = "FS_SOLVER_UNSUPPORTED_ELEMENT"
    FS_SOLVER_ABAQUS_NON_DEFAULT = "FS_SOLVER_ABAQUS_NON_DEFAULT"
    FS_BENCHMARK_METADATA_MISSING = "FS_BENCHMARK_METADATA_MISSING"


@dataclass(frozen=True)
class FEASpecValidationDiagnostic:
    """A single semantic validation diagnostic."""

    code: DiagnosticCode
    severity: DiagnosticSeverity
    category: DiagnosticCategory
    message: str
    target_ref: str = ""
    evidence_ref: str = ""
    suggested_fix: str = ""
    blocks_approval: bool = False
    blocks_solver_handoff: bool = False

    @classmethod
    def make(
        cls,
        code: DiagnosticCode,
        severity: DiagnosticSeverity,
        category: DiagnosticCategory,
        message: str,
        *,
        target_ref: str = "",
        evidence_ref: str = "",
        suggested_fix: str = "",
        blocks_approval: bool | None = None,
        blocks_solver_handoff: bool | None = None,
    ) -> FEASpecValidationDiagnostic:
        blocks_approval = _blocks_approval(severity) if blocks_approval is None else blocks_approval
        if blocks_solver_handoff is None:
            blocks_solver_handoff = blocks_approval or severity is DiagnosticSeverity.BLOCKER
        return cls(
            code=code,
            severity=severity,
            category=category,
            message=message,
            target_ref=target_ref,
            evidence_ref=evidence_ref,
            suggested_fix=suggested_fix,
            blocks_approval=blocks_approval,
            blocks_solver_handoff=blocks_solver_handoff,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "target_ref": self.target_ref,
            "evidence_ref": self.evidence_ref,
            "suggested_fix": self.suggested_fix,
            "blocks_approval": self.blocks_approval,
            "blocks_solver_handoff": self.blocks_solver_handoff,
        }


@dataclass(frozen=True)
class ValidationPhaseResult:
    """Diagnostics emitted by one validator phase."""

    phase: str
    diagnostics: tuple[FEASpecValidationDiagnostic, ...] = ()

    @property
    def passed(self) -> bool:
        return not any(
            diagnostic.severity
            in {DiagnosticSeverity.ERROR, DiagnosticSeverity.BLOCKER}
            for diagnostic in self.diagnostics
        )


@dataclass(frozen=True)
class FEASpecValidationReport:
    """Structured result returned by the experimental FEASpec validator."""

    validation_state: ValidationState
    diagnostics: tuple[FEASpecValidationDiagnostic, ...] = ()
    phase_results: tuple[ValidationPhaseResult, ...] = ()
    accepted_warnings_required: bool = False
    solver_id: str = ""
    benchmark_seed: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def has_blockers(self) -> bool:
        return any(
            diagnostic.severity is DiagnosticSeverity.BLOCKER
            for diagnostic in self.diagnostics
        )

    @property
    def has_errors(self) -> bool:
        return any(
            diagnostic.severity is DiagnosticSeverity.ERROR
            for diagnostic in self.diagnostics
        )

    @property
    def is_valid(self) -> bool:
        return not self.has_blockers and not self.has_errors

    @property
    def can_be_approved(self) -> bool:
        return self.is_valid and not any(
            diagnostic.blocks_approval for diagnostic in self.diagnostics
        )

    @property
    def can_handoff_to_solver(self) -> bool:
        return (
            bool(self.solver_id)
            and self.validation_state is ValidationState.APPROVED
            and self.is_valid
            and not any(diagnostic.blocks_solver_handoff for diagnostic in self.diagnostics)
        )

    @property
    def diagnostic_codes(self) -> set[DiagnosticCode]:
        return {diagnostic.code for diagnostic in self.diagnostics}

    def to_dict(self) -> dict[str, object]:
        return {
            "validation_state": self.validation_state.value,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
            "phase_results": [
                {
                    "phase": phase.phase,
                    "passed": phase.passed,
                    "diagnostics": [diagnostic.to_dict() for diagnostic in phase.diagnostics],
                }
                for phase in self.phase_results
            ],
            "is_valid": self.is_valid,
            "has_blockers": self.has_blockers,
            "has_errors": self.has_errors,
            "can_be_approved": self.can_be_approved,
            "can_handoff_to_solver": self.can_handoff_to_solver,
            "accepted_warnings_required": self.accepted_warnings_required,
            "solver_id": self.solver_id,
            "benchmark_seed": self.benchmark_seed,
            "metadata": dict(self.metadata),
        }


def infer_validation_state(
    diagnostics: Iterable[FEASpecValidationDiagnostic],
    *,
    approved: bool = False,
    rejected: bool = False,
) -> ValidationState:
    """Infer the validator report state from diagnostics and review state."""

    diagnostics = tuple(diagnostics)
    if rejected:
        return ValidationState.REJECTED
    if any(
        diagnostic.severity
        in {DiagnosticSeverity.ERROR, DiagnosticSeverity.BLOCKER}
        for diagnostic in diagnostics
    ):
        return ValidationState.INVALID
    if any(diagnostic.severity is DiagnosticSeverity.WARNING for diagnostic in diagnostics):
        return ValidationState.VALID_WITH_WARNINGS
    if approved:
        return ValidationState.APPROVED
    return ValidationState.VALID_WITH_WARNINGS


def _blocks_approval(severity: DiagnosticSeverity) -> bool:
    return severity in {DiagnosticSeverity.ERROR, DiagnosticSeverity.BLOCKER}
