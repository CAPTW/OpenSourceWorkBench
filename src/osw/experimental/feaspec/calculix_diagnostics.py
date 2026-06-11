"""Diagnostics for experimental FEASpec to CalculiX case planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CalculiXPlanSeverity(str, Enum):
    """CalculiX case-plan diagnostic severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class CalculiXPlanDiagnosticCode(str, Enum):
    """Stable diagnostic code catalog for FEASpec CalculiX case planning."""

    FC_APPROVAL_REQUIRED = "FC_APPROVAL_REQUIRED"
    FC_VALIDATION_BLOCKED = "FC_VALIDATION_BLOCKED"
    FC_BRIDGE_BLOCKED = "FC_BRIDGE_BLOCKED"
    FC_MESH_REQUIRED = "FC_MESH_REQUIRED"
    FC_UNSUPPORTED_GEOMETRY = "FC_UNSUPPORTED_GEOMETRY"
    FC_UNSUPPORTED_ELEMENT_TYPE = "FC_UNSUPPORTED_ELEMENT_TYPE"
    FC_MATERIAL_MISSING = "FC_MATERIAL_MISSING"
    FC_SECTION_MISSING = "FC_SECTION_MISSING"
    FC_BC_INVALID_TARGET = "FC_BC_INVALID_TARGET"
    FC_BC_INSUFFICIENT_CONSTRAINTS = "FC_BC_INSUFFICIENT_CONSTRAINTS"
    FC_LOAD_INVALID_TARGET = "FC_LOAD_INVALID_TARGET"
    FC_LOAD_UNSUPPORTED_TYPE = "FC_LOAD_UNSUPPORTED_TYPE"
    FC_UNITS_UNSUPPORTED = "FC_UNITS_UNSUPPORTED"
    FC_STEP_UNSUPPORTED = "FC_STEP_UNSUPPORTED"
    FC_OUTPUT_UNSUPPORTED = "FC_OUTPUT_UNSUPPORTED"
    FC_PROVENANCE_INCOMPLETE = "FC_PROVENANCE_INCOMPLETE"


@dataclass(frozen=True)
class FEASpecCalculiXPlanDiagnostic:
    """A single FEASpec-to-CalculiX case-plan diagnostic."""

    code: CalculiXPlanDiagnosticCode
    severity: CalculiXPlanSeverity
    message: str
    target_ref: str = ""
    source_field: str = ""
    suggested_fix: str = ""
    blocks_case_plan: bool = False
    blocks_solver_handoff: bool = True

    @classmethod
    def make(
        cls,
        code: CalculiXPlanDiagnosticCode,
        severity: CalculiXPlanSeverity,
        message: str,
        *,
        target_ref: str = "",
        source_field: str = "",
        suggested_fix: str = "",
        blocks_case_plan: bool | None = None,
        blocks_solver_handoff: bool = True,
    ) -> FEASpecCalculiXPlanDiagnostic:
        resolved_blocks_case_plan = (
            severity in {CalculiXPlanSeverity.ERROR, CalculiXPlanSeverity.BLOCKER}
            if blocks_case_plan is None
            else blocks_case_plan
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            target_ref=target_ref,
            source_field=source_field,
            suggested_fix=suggested_fix,
            blocks_case_plan=resolved_blocks_case_plan,
            blocks_solver_handoff=blocks_solver_handoff,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "target_ref": self.target_ref,
            "source_field": self.source_field,
            "suggested_fix": self.suggested_fix,
            "blocks_case_plan": self.blocks_case_plan,
            "blocks_solver_handoff": self.blocks_solver_handoff,
        }
