"""Diagnostics for FEASpec CalculiX result import planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "CalculiXResultImportDiagnosticCode",
    "CalculiXResultImportSeverity",
    "FEASpecCalculiXResultImportDiagnostic",
]


class CalculiXResultImportSeverity(str, Enum):
    """Severity for FEASpec CalculiX result import diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class CalculiXResultImportDiagnosticCode(str, Enum):
    """Stable diagnostic code catalog for result import planning."""

    FI_RESULT_DIR_MISSING = "FI_RESULT_DIR_MISSING"
    FI_RESULT_DIR_NOT_DIRECTORY = "FI_RESULT_DIR_NOT_DIRECTORY"
    FI_MANIFEST_MISSING = "FI_MANIFEST_MISSING"
    FI_RUN_METADATA_MISSING = "FI_RUN_METADATA_MISSING"
    FI_EXPORT_MANIFEST_MISSING = "FI_EXPORT_MANIFEST_MISSING"
    FI_UNSUPPORTED_FILE = "FI_UNSUPPORTED_FILE"
    FI_PARSE_NOT_IMPLEMENTED = "FI_PARSE_NOT_IMPLEMENTED"
    FI_PARTIAL_IMPORT = "FI_PARTIAL_IMPORT"
    FI_NO_PRIMARY_RESULT = "FI_NO_PRIMARY_RESULT"
    FI_RUN_FAILED = "FI_RUN_FAILED"
    FI_RUN_TIMED_OUT = "FI_RUN_TIMED_OUT"
    FI_SOLVER_NOT_EXECUTED = "FI_SOLVER_NOT_EXECUTED"
    FI_PROVENANCE_INCOMPLETE = "FI_PROVENANCE_INCOMPLETE"
    FI_FORBIDDEN_PATH = "FI_FORBIDDEN_PATH"
    FI_RESULT_DATASET_WRITE_FORBIDDEN = "FI_RESULT_DATASET_WRITE_FORBIDDEN"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultImportDiagnostic:
    """A single FEASpec CalculiX result-import diagnostic."""

    code: CalculiXResultImportDiagnosticCode
    severity: CalculiXResultImportSeverity
    message: str
    path: str = ""
    suggested_fix: str = ""
    blocks_import: bool = False

    @classmethod
    def make(
        cls,
        code: CalculiXResultImportDiagnosticCode,
        severity: CalculiXResultImportSeverity,
        message: str,
        *,
        path: str = "",
        suggested_fix: str = "",
        blocks_import: bool | None = None,
    ) -> FEASpecCalculiXResultImportDiagnostic:
        resolved_blocks = (
            severity in {
                CalculiXResultImportSeverity.ERROR,
                CalculiXResultImportSeverity.BLOCKER,
            }
            if blocks_import is None
            else blocks_import
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            path=path,
            suggested_fix=suggested_fix,
            blocks_import=resolved_blocks,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "suggested_fix": self.suggested_fix,
            "blocks_import": self.blocks_import,
        }
