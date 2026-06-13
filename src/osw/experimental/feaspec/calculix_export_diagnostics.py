"""Diagnostics for experimental FEASpec CalculiX no-run export bundles."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "CalculiXExportDiagnosticCode",
    "CalculiXExportSeverity",
    "FEASpecCalculiXExportDiagnostic",
]


class CalculiXExportSeverity(str, Enum):
    """FEASpec CalculiX exporter diagnostic severity."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class CalculiXExportDiagnosticCode(str, Enum):
    """Stable diagnostic code catalog for FEASpec CalculiX export bundles."""

    FX_RENDER_BLOCKED = "FX_RENDER_BLOCKED"
    FX_OUTPUT_DIR_MISSING = "FX_OUTPUT_DIR_MISSING"
    FX_OUTPUT_DIR_NOT_DIRECTORY = "FX_OUTPUT_DIR_NOT_DIRECTORY"
    FX_OUTPUT_DIR_NOT_EMPTY = "FX_OUTPUT_DIR_NOT_EMPTY"
    FX_UNSAFE_BASENAME = "FX_UNSAFE_BASENAME"
    FX_OUTPUT_EXISTS = "FX_OUTPUT_EXISTS"
    FX_WRITE_FAILED = "FX_WRITE_FAILED"
    FX_MANIFEST_WRITE_FAILED = "FX_MANIFEST_WRITE_FAILED"
    FX_DIAGNOSTICS_WRITE_FAILED = "FX_DIAGNOSTICS_WRITE_FAILED"
    FX_README_WRITE_FAILED = "FX_README_WRITE_FAILED"
    FX_CHECKSUM_FAILED = "FX_CHECKSUM_FAILED"
    FX_SOLVER_RUN_FORBIDDEN = "FX_SOLVER_RUN_FORBIDDEN"


@dataclass(frozen=True)
class FEASpecCalculiXExportDiagnostic:
    """A single FEASpec CalculiX exporter diagnostic."""

    code: CalculiXExportDiagnosticCode
    severity: CalculiXExportSeverity
    message: str
    path: str = ""
    suggested_fix: str = ""
    blocks_export: bool = False

    @classmethod
    def make(
        cls,
        code: CalculiXExportDiagnosticCode,
        severity: CalculiXExportSeverity,
        message: str,
        *,
        path: str = "",
        suggested_fix: str = "",
        blocks_export: bool | None = None,
    ) -> FEASpecCalculiXExportDiagnostic:
        blocks_export_resolved = (
            severity in {CalculiXExportSeverity.ERROR, CalculiXExportSeverity.BLOCKER}
            if blocks_export is None
            else blocks_export
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            path=path,
            suggested_fix=suggested_fix,
            blocks_export=blocks_export_resolved,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "suggested_fix": self.suggested_fix,
            "blocks_export": self.blocks_export,
        }
