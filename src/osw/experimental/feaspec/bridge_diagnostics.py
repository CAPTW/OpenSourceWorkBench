"""Diagnostics for the experimental FEASpec project bridge."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class BridgeSeverity(str, Enum):
    """Bridge diagnostic severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class BridgeDiagnosticCode(str, Enum):
    """Stable diagnostic code catalog for FEASpec project bridge planning."""

    FB_APPROVAL_REQUIRED = "FB_APPROVAL_REQUIRED"
    FB_VALIDATION_BLOCKED = "FB_VALIDATION_BLOCKED"
    FB_UNSUPPORTED_GEOMETRY = "FB_UNSUPPORTED_GEOMETRY"
    FB_UNMAPPED_REGION = "FB_UNMAPPED_REGION"
    FB_MISSING_MATERIAL = "FB_MISSING_MATERIAL"
    FB_UNSUPPORTED_SECTION = "FB_UNSUPPORTED_SECTION"
    FB_INVALID_BC_TARGET = "FB_INVALID_BC_TARGET"
    FB_INVALID_LOAD_TARGET = "FB_INVALID_LOAD_TARGET"
    FB_UNSUPPORTED_LOAD_TYPE = "FB_UNSUPPORTED_LOAD_TYPE"
    FB_UNITS_UNSUPPORTED = "FB_UNITS_UNSUPPORTED"
    FB_SOLVER_TARGET_UNSUPPORTED = "FB_SOLVER_TARGET_UNSUPPORTED"
    FB_PROVENANCE_INCOMPLETE = "FB_PROVENANCE_INCOMPLETE"


@dataclass(frozen=True)
class FEASpecBridgeDiagnostic:
    """A single FEASpec-to-ProjectSchema bridge diagnostic."""

    code: BridgeDiagnosticCode
    severity: BridgeSeverity
    message: str
    target_ref: str = ""
    source_field: str = ""
    suggested_fix: str = ""
    blocks_bridge: bool = False
    blocks_solver_handoff: bool = True

    @classmethod
    def make(
        cls,
        code: BridgeDiagnosticCode,
        severity: BridgeSeverity,
        message: str,
        *,
        target_ref: str = "",
        source_field: str = "",
        suggested_fix: str = "",
        blocks_bridge: bool | None = None,
        blocks_solver_handoff: bool = True,
    ) -> FEASpecBridgeDiagnostic:
        resolved_blocks_bridge = (
            severity in {BridgeSeverity.ERROR, BridgeSeverity.BLOCKER}
            if blocks_bridge is None
            else blocks_bridge
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            target_ref=target_ref,
            source_field=source_field,
            suggested_fix=suggested_fix,
            blocks_bridge=resolved_blocks_bridge,
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
            "blocks_bridge": self.blocks_bridge,
            "blocks_solver_handoff": self.blocks_solver_handoff,
        }
