"""Diagnostics for the FEASpec installed-only CalculiX run gate."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "CalculiXRunSeverity",
    "CalculiXRunDiagnosticCode",
    "FEASpecCalculiXRunDiagnostic",
]


class CalculiXRunSeverity(str, Enum):
    """Severity for FEASpec installed-only run diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class CalculiXRunDiagnosticCode(str, Enum):
    """Stable diagnostic code catalog for the installed-only run gate."""

    FR_RUN_NOT_AUTHORIZED = "FR_RUN_NOT_AUTHORIZED"
    FR_EXECUTE_FLAG_REQUIRED = "FR_EXECUTE_FLAG_REQUIRED"
    FR_CONFIRMATION_REQUIRED = "FR_CONFIRMATION_REQUIRED"
    FR_README_NOT_ACKNOWLEDGED = "FR_README_NOT_ACKNOWLEDGED"
    FR_CCX_MISSING = "FR_CCX_MISSING"
    FR_CCX_NOT_EXECUTABLE = "FR_CCX_NOT_EXECUTABLE"
    FR_EXPORT_BUNDLE_INVALID = "FR_EXPORT_BUNDLE_INVALID"
    FR_MANIFEST_MISSING = "FR_MANIFEST_MISSING"
    FR_INP_MISSING = "FR_INP_MISSING"
    FR_README_MISSING = "FR_README_MISSING"
    FR_RUN_DIR_UNSAFE = "FR_RUN_DIR_UNSAFE"
    FR_RUN_DIR_NOT_EMPTY = "FR_RUN_DIR_NOT_EMPTY"
    FR_TIMEOUT = "FR_TIMEOUT"
    FR_NONZERO_EXIT = "FR_NONZERO_EXIT"
    FR_OUTPUT_MISSING = "FR_OUTPUT_MISSING"
    FR_FORBIDDEN_PATH = "FR_FORBIDDEN_PATH"
    FR_METADATA_WRITE_FAILED = "FR_METADATA_WRITE_FAILED"
    FR_PROCESS_START_FAILED = "FR_PROCESS_START_FAILED"


@dataclass(frozen=True)
class FEASpecCalculiXRunDiagnostic:
    """A single FEASpec run-gate diagnostic."""

    code: CalculiXRunDiagnosticCode
    severity: CalculiXRunSeverity
    message: str
    path: str = ""
    suggested_fix: str = ""
    blocks_execution: bool = False

    @classmethod
    def make(
        cls,
        code: CalculiXRunDiagnosticCode,
        severity: CalculiXRunSeverity,
        message: str,
        *,
        path: str = "",
        suggested_fix: str = "",
        blocks_execution: bool | None = None,
    ) -> FEASpecCalculiXRunDiagnostic:
        resolved_blocks = (
            severity in {CalculiXRunSeverity.ERROR, CalculiXRunSeverity.BLOCKER}
            if blocks_execution is None
            else blocks_execution
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            path=path,
            suggested_fix=suggested_fix,
            blocks_execution=resolved_blocks,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "suggested_fix": self.suggested_fix,
            "blocks_execution": self.blocks_execution,
        }
