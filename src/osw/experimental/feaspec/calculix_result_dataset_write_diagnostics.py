"""Diagnostics for FEASpec CalculiX ResultDataset write planning and writing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "CalculiXResultDatasetWriteSeverity",
    "CalculiXResultDatasetWriteDiagnosticCode",
    "FEASpecCalculiXResultDatasetWriteDiagnostic",
]


class CalculiXResultDatasetWriteSeverity(str, Enum):
    """Severity for ResultDataset write-plan diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class CalculiXResultDatasetWriteDiagnosticCode(str, Enum):
    """Stable diagnostic code catalog for write planning and writing."""

    FDW_WRITE_NOT_IMPLEMENTED = "FDW_WRITE_NOT_IMPLEMENTED"
    FDW_OUTPUT_PATH_REQUIRED = "FDW_OUTPUT_PATH_REQUIRED"
    FDW_OUTPUT_DIRECTORY_REQUIRED = "FDW_OUTPUT_DIRECTORY_REQUIRED"
    FDW_PARENT_MISSING = "FDW_PARENT_MISSING"
    FDW_CREATE_DIR_REQUIRED = "FDW_CREATE_DIR_REQUIRED"
    FDW_OUTPUT_EXISTS = "FDW_OUTPUT_EXISTS"
    FDW_OUTPUT_NOT_EMPTY = "FDW_OUTPUT_NOT_EMPTY"
    FDW_UNSAFE_PATH = "FDW_UNSAFE_PATH"
    FDW_PATH_TRAVERSAL_REJECTED = "FDW_PATH_TRAVERSAL_REJECTED"
    FDW_DRAFT_BLOCKED = "FDW_DRAFT_BLOCKED"
    FDW_SCHEMA_VERSION_MISSING = "FDW_SCHEMA_VERSION_MISSING"
    FDW_PROVENANCE_INCOMPLETE = "FDW_PROVENANCE_INCOMPLETE"
    FDW_ARTIFACT_REFERENCE_MISSING = "FDW_ARTIFACT_REFERENCE_MISSING"
    FDW_ARTIFACT_HASH_MISMATCH = "FDW_ARTIFACT_HASH_MISMATCH"
    FDW_DIAGNOSTICS_UNREVIEWED = "FDW_DIAGNOSTICS_UNREVIEWED"
    FDW_LIMITATIONS_NOT_ACKNOWLEDGED = "FDW_LIMITATIONS_NOT_ACKNOWLEDGED"
    FDW_ATOMIC_WRITE_PLANNED_ONLY = "FDW_ATOMIC_WRITE_PLANNED_ONLY"
    FDW_ATOMIC_WRITE_NOT_IMPLEMENTED = "FDW_ATOMIC_WRITE_NOT_IMPLEMENTED"
    FDW_ARTIFACT_COPY_NOT_IMPLEMENTED = "FDW_ARTIFACT_COPY_NOT_IMPLEMENTED"
    FDW_RESULTDATASET_PERSISTENCE_FORBIDDEN = (
        "FDW_RESULTDATASET_PERSISTENCE_FORBIDDEN"
    )
    FDW_WRITE_COMPLETED = "FDW_WRITE_COMPLETED"
    FDW_WRITE_FAILED = "FDW_WRITE_FAILED"
    FDW_TEMP_WRITE_FAILED = "FDW_TEMP_WRITE_FAILED"
    FDW_TARGET_REPLACE_FAILED = "FDW_TARGET_REPLACE_FAILED"
    FDW_UNPLANNED_FILE_COLLISION = "FDW_UNPLANNED_FILE_COLLISION"
    FDW_WRITTEN_FILE_HASH_FAILED = "FDW_WRITTEN_FILE_HASH_FAILED"
    FDW_ARTIFACT_COPY_FORBIDDEN = "FDW_ARTIFACT_COPY_FORBIDDEN"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetWriteDiagnostic:
    """A single FEASpec CalculiX ResultDataset write diagnostic."""

    code: CalculiXResultDatasetWriteDiagnosticCode
    severity: CalculiXResultDatasetWriteSeverity
    message: str
    path: str = ""
    suggested_fix: str = ""
    blocks_write: bool = False

    @classmethod
    def make(
        cls,
        code: CalculiXResultDatasetWriteDiagnosticCode,
        severity: CalculiXResultDatasetWriteSeverity,
        message: str,
        *,
        path: str = "",
        suggested_fix: str = "",
        blocks_write: bool | None = None,
    ) -> FEASpecCalculiXResultDatasetWriteDiagnostic:
        resolved_blocks = (
            severity
            in {
                CalculiXResultDatasetWriteSeverity.ERROR,
                CalculiXResultDatasetWriteSeverity.BLOCKER,
            }
            if blocks_write is None
            else blocks_write
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            path=path,
            suggested_fix=suggested_fix,
            blocks_write=resolved_blocks,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "suggested_fix": self.suggested_fix,
            "blocks_write": self.blocks_write,
        }
