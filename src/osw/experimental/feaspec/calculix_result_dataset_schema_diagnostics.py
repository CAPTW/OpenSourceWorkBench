"""Diagnostics for FEASpec CalculiX ResultDataset schema payloads."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "CalculiXResultDatasetSchemaSeverity",
    "CalculiXResultDatasetSchemaDiagnosticCode",
    "FEASpecCalculiXResultDatasetSchemaDiagnostic",
]


class CalculiXResultDatasetSchemaSeverity(str, Enum):
    """Severity for ResultDataset schema-payload diagnostics."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class CalculiXResultDatasetSchemaDiagnosticCode(str, Enum):
    """Stable diagnostic code catalog for schema payload modeling."""

    FDS_SCHEMA_MODEL_ONLY = "FDS_SCHEMA_MODEL_ONLY"
    FDS_SCHEMA_NAME_MISSING = "FDS_SCHEMA_NAME_MISSING"
    FDS_SCHEMA_VERSION_MISSING = "FDS_SCHEMA_VERSION_MISSING"
    FDS_PRODUCER_VERSION_MISSING = "FDS_PRODUCER_VERSION_MISSING"
    FDS_SOURCE_VERSION_MISSING = "FDS_SOURCE_VERSION_MISSING"
    FDS_DRAFT_MAPPING_MISSING = "FDS_DRAFT_MAPPING_MISSING"
    FDS_WRITE_PLAN_MISSING = "FDS_WRITE_PLAN_MISSING"
    FDS_WRITE_PLAN_BLOCKED = "FDS_WRITE_PLAN_BLOCKED"
    FDS_ARTIFACTS_MISSING = "FDS_ARTIFACTS_MISSING"
    FDS_PROVENANCE_MISSING = "FDS_PROVENANCE_MISSING"
    FDS_DIAGNOSTICS_MISSING = "FDS_DIAGNOSTICS_MISSING"
    FDS_LIMITATIONS_MISSING = "FDS_LIMITATIONS_MISSING"
    FDS_PAYLOAD_INVALID = "FDS_PAYLOAD_INVALID"
    FDS_MANIFEST_INVALID = "FDS_MANIFEST_INVALID"
    FDS_README_REQUIRED = "FDS_README_REQUIRED"
    FDS_FILE_WRITE_FORBIDDEN = "FDS_FILE_WRITE_FORBIDDEN"
    FDS_PERSISTENCE_NOT_IMPLEMENTED = "FDS_PERSISTENCE_NOT_IMPLEMENTED"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetSchemaDiagnostic:
    """A single FEASpec CalculiX ResultDataset schema-payload diagnostic."""

    code: CalculiXResultDatasetSchemaDiagnosticCode
    severity: CalculiXResultDatasetSchemaSeverity
    message: str
    path: str = ""
    suggested_fix: str = ""
    blocks_payload: bool = False

    @classmethod
    def make(
        cls,
        code: CalculiXResultDatasetSchemaDiagnosticCode,
        severity: CalculiXResultDatasetSchemaSeverity,
        message: str,
        *,
        path: str = "",
        suggested_fix: str = "",
        blocks_payload: bool | None = None,
    ) -> FEASpecCalculiXResultDatasetSchemaDiagnostic:
        resolved_blocks = (
            severity
            in {
                CalculiXResultDatasetSchemaSeverity.ERROR,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
            }
            if blocks_payload is None
            else blocks_payload
        )
        return cls(
            code=code,
            severity=severity,
            message=message,
            path=path,
            suggested_fix=suggested_fix,
            blocks_payload=resolved_blocks,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path,
            "suggested_fix": self.suggested_fix,
            "blocks_payload": self.blocks_payload,
        }
