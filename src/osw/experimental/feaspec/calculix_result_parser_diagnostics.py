"""Parser diagnostics for FEASpec CalculiX result metadata scanning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "CalculiXResultParserSeverity",
    "CalculiXResultParserDiagnosticCode",
    "FEASpecCalculiXResultParserDiagnostic",
]


class CalculiXResultParserSeverity(str, Enum):
    """Severity for FEASpec CalculiX result parser diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class CalculiXResultParserDiagnosticCode(str, Enum):
    """Stable parser diagnostic catalog."""

    FP_FILE_MISSING = "FP_FILE_MISSING"
    FP_PATH_NOT_FILE = "FP_PATH_NOT_FILE"
    FP_UNSUPPORTED_FORMAT = "FP_UNSUPPORTED_FORMAT"
    FP_SIZE_LIMIT_EXCEEDED = "FP_SIZE_LIMIT_EXCEEDED"
    FP_LINE_LIMIT_EXCEEDED = "FP_LINE_LIMIT_EXCEEDED"
    FP_ENCODING_UNSUPPORTED = "FP_ENCODING_UNSUPPORTED"
    FP_PARSE_NOT_IMPLEMENTED = "FP_PARSE_NOT_IMPLEMENTED"
    FP_PARTIAL_PARSE = "FP_PARTIAL_PARSE"
    FP_UNSUPPORTED_SECTION = "FP_UNSUPPORTED_SECTION"
    FP_UNSUPPORTED_RESULT_BLOCK = "FP_UNSUPPORTED_RESULT_BLOCK"
    FP_NUMERIC_CONVERSION_FAILED = "FP_NUMERIC_CONVERSION_FAILED"
    FP_NO_PRIMARY_FIELD = "FP_NO_PRIMARY_FIELD"
    FP_UNITS_MISSING = "FP_UNITS_MISSING"
    FP_PROVENANCE_MISSING = "FP_PROVENANCE_MISSING"
    FP_SOLVER_RUN_FAILED = "FP_SOLVER_RUN_FAILED"
    FP_FORBIDDEN_PATH = "FP_FORBIDDEN_PATH"
    FP_EXTERNAL_COMMAND_FORBIDDEN = "FP_EXTERNAL_COMMAND_FORBIDDEN"
    FP_RESULT_DATASET_WRITE_FORBIDDEN = "FP_RESULT_DATASET_WRITE_FORBIDDEN"
    FP_SNIPPET_TRUNCATED = "FP_SNIPPET_TRUNCATED"
    FP_HASH_FAILED = "FP_HASH_FAILED"
    FP_METADATA_ONLY = "FP_METADATA_ONLY"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultParserDiagnostic:
    """A single parser diagnostic for result scanning and mapping."""

    code: CalculiXResultParserDiagnosticCode
    severity: CalculiXResultParserSeverity
    message: str
    path: str = ""
    artifact_kind: str = ""
    suggested_fix: str = ""
    blocks_parse: bool = False
    blocks_import: bool = False

    @classmethod
    def make(
        cls,
        code: CalculiXResultParserDiagnosticCode,
        severity: CalculiXResultParserSeverity,
        message: str,
        *,
        path: str = "",
        artifact_kind: str = "",
        suggested_fix: str = "",
        blocks_parse: bool | None = None,
        blocks_import: bool | None = None,
    ) -> FEASpecCalculiXResultParserDiagnostic:
        resolved_blocks_parse = (
            severity in {CalculiXResultParserSeverity.ERROR, CalculiXResultParserSeverity.BLOCKER}
            if blocks_parse is None
            else blocks_parse
        )
        resolved_blocks_import = (
            severity in {CalculiXResultParserSeverity.ERROR, CalculiXResultParserSeverity.BLOCKER}
            if blocks_import is None
            else blocks_import
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            path=path,
            artifact_kind=artifact_kind,
            suggested_fix=suggested_fix,
            blocks_parse=resolved_blocks_parse,
            blocks_import=resolved_blocks_import,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "artifact_kind": self.artifact_kind,
            "suggested_fix": self.suggested_fix,
            "blocks_parse": self.blocks_parse,
            "blocks_import": self.blocks_import,
        }
