"""Diagnostics for experimental FEASpec CalculiX INP rendering."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "CalculiXInpDiagnosticCode",
    "CalculiXInpSeverity",
    "FEASpecCalculiXInpDiagnostic",
]


class CalculiXInpSeverity(str, Enum):
    """FEASpec CalculiX INP renderer diagnostic severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class CalculiXInpDiagnosticCode(str, Enum):
    """Stable diagnostic code catalog for FEASpec CalculiX INP rendering."""

    FW_PLAN_NOT_READY = "FW_PLAN_NOT_READY"
    FW_MESH_REQUIRED = "FW_MESH_REQUIRED"
    FW_UNSUPPORTED_ELEMENT_TYPE = "FW_UNSUPPORTED_ELEMENT_TYPE"
    FW_NODE_MISSING = "FW_NODE_MISSING"
    FW_ELEMENT_MISSING = "FW_ELEMENT_MISSING"
    FW_MATERIAL_MISSING = "FW_MATERIAL_MISSING"
    FW_SECTION_MISSING = "FW_SECTION_MISSING"
    FW_BC_INVALID_TARGET = "FW_BC_INVALID_TARGET"
    FW_LOAD_INVALID_TARGET = "FW_LOAD_INVALID_TARGET"
    FW_LOAD_UNSUPPORTED_TYPE = "FW_LOAD_UNSUPPORTED_TYPE"
    FW_STEP_UNSUPPORTED = "FW_STEP_UNSUPPORTED"
    FW_OUTPUT_UNSUPPORTED = "FW_OUTPUT_UNSUPPORTED"
    FW_WRITE_PATH_EXISTS = "FW_WRITE_PATH_EXISTS"
    FW_PROVENANCE_INCOMPLETE = "FW_PROVENANCE_INCOMPLETE"


@dataclass(frozen=True)
class FEASpecCalculiXInpDiagnostic:
    """A single FEASpec CalculiX INP renderer diagnostic."""

    code: CalculiXInpDiagnosticCode
    severity: CalculiXInpSeverity
    message: str
    target_ref: str = ""
    source_field: str = ""
    suggested_fix: str = ""
    blocks_render: bool = False
    blocks_write: bool = False

    @classmethod
    def make(
        cls,
        code: CalculiXInpDiagnosticCode,
        severity: CalculiXInpSeverity,
        message: str,
        *,
        target_ref: str = "",
        source_field: str = "",
        suggested_fix: str = "",
        blocks_render: bool | None = None,
        blocks_write: bool | None = None,
    ) -> FEASpecCalculiXInpDiagnostic:
        blocks_render_resolved = (
            severity in {CalculiXInpSeverity.ERROR, CalculiXInpSeverity.BLOCKER}
            if blocks_render is None
            else blocks_render
        )
        blocks_write_resolved = (
            blocks_render_resolved if blocks_write is None else blocks_write
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            target_ref=target_ref,
            source_field=source_field,
            suggested_fix=suggested_fix,
            blocks_render=blocks_render_resolved,
            blocks_write=blocks_write_resolved,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "target_ref": self.target_ref,
            "source_field": self.source_field,
            "suggested_fix": self.suggested_fix,
            "blocks_render": self.blocks_render,
            "blocks_write": self.blocks_write,
        }
