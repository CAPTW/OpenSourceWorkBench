"""In-memory ResultDataset schema payloads for FEASpec CalculiX results.

This module turns a reviewed draft mapping and write plan into deterministic
Python payload records. It does not persist ResultDataset files, perform
external execution, mutate ProjectSchema, or add a write-capable CLI path.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

from osw import __version__ as OSW_VERSION

from .calculix_result_dataset_schema_diagnostics import (
    CalculiXResultDatasetSchemaDiagnosticCode,
    CalculiXResultDatasetSchemaSeverity,
    FEASpecCalculiXResultDatasetSchemaDiagnostic,
)
from .calculix_result_dataset_write_plan import (
    WRITE_SCHEMA_NAME,
    WRITE_SCHEMA_VERSION,
    validate_calculix_result_dataset_write_plan,
)

__all__ = [
    "FEASpecCalculiXResultDatasetSchemaPayload",
    "FEASpecCalculiXResultDatasetSchemaValidation",
    "FEASpecCalculiXResultDatasetSchemaVersion",
    "FEASpecCalculiXResultDatasetManifestPayload",
    "FEASpecCalculiXResultDatasetDiagnosticsPayload",
    "FEASpecCalculiXResultDatasetProvenancePayload",
    "FEASpecCalculiXResultDatasetReviewReadmePayload",
    "FEASpecCalculiXResultDatasetSchemaStatus",
    "build_calculix_result_dataset_schema_payload",
    "build_calculix_result_dataset_manifest_payload",
    "build_calculix_result_dataset_diagnostics_payload",
    "build_calculix_result_dataset_provenance_payload",
    "build_calculix_result_dataset_review_readme",
    "validate_calculix_result_dataset_schema_payload",
    "explain_calculix_result_dataset_schema_payload",
]


class FEASpecCalculiXResultDatasetSchemaStatus(str, Enum):
    """Status for in-memory ResultDataset schema payloads."""

    PAYLOAD_READY = "payload-ready"
    PAYLOAD_READY_WITH_WARNINGS = "payload-ready-with-warnings"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    SCHEMA_MODEL_ONLY = "schema-model-only"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetSchemaVersion:
    """Schema and producer version metadata for a payload."""

    schema_name: str
    schema_version: str
    producer: str = "OpenSolver Workbench FEASpec CalculiX result import"
    producer_version: str = OSW_VERSION
    source_version: str = OSW_VERSION
    source_release: str = "v0.1.4-rc1"

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_name": self.schema_name,
            "schema_version": self.schema_version,
            "producer": self.producer,
            "producer_version": self.producer_version,
            "source_version": self.source_version,
            "source_release": self.source_release,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetManifestPayload:
    """In-memory manifest payload for future ResultDataset persistence."""

    schema: FEASpecCalculiXResultDatasetSchemaVersion
    dataset_id: str
    source: str
    solver: str
    analysis_type: str
    planned_files: tuple[Mapping[str, Any], ...]
    artifact_references: tuple[Mapping[str, Any], ...]
    review_required: bool = True
    writes_files: bool = False
    result_dataset_persistence: bool = False
    solver_execution_performed: bool = False
    artifact_copy_performed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema.to_dict(),
            "dataset_id": self.dataset_id,
            "source": self.source,
            "solver": self.solver,
            "analysis_type": self.analysis_type,
            "planned_files": [dict(item) for item in self.planned_files],
            "artifact_references": [
                dict(item) for item in self.artifact_references
            ],
            "review_required": self.review_required,
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
            "solver_execution_performed": self.solver_execution_performed,
            "artifact_copy_performed": self.artifact_copy_performed,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetDiagnosticsPayload:
    """In-memory diagnostics payload for a future ResultDataset."""

    diagnostics: tuple[Mapping[str, Any], ...]
    schema_diagnostics: tuple[Mapping[str, Any], ...]
    source_diagnostics: tuple[Mapping[str, Any], ...]
    write_plan_diagnostics: tuple[Mapping[str, Any], ...]
    diagnostic_count: int
    blocker_count: int
    writes_files: bool = False
    result_dataset_persistence: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "diagnostics": [dict(item) for item in self.diagnostics],
            "schema_diagnostics": [
                dict(item) for item in self.schema_diagnostics
            ],
            "source_diagnostics": [
                dict(item) for item in self.source_diagnostics
            ],
            "write_plan_diagnostics": [
                dict(item) for item in self.write_plan_diagnostics
            ],
            "diagnostic_count": self.diagnostic_count,
            "blocker_count": self.blocker_count,
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetProvenancePayload:
    """In-memory provenance payload for a future ResultDataset."""

    provenance: Mapping[str, Any]
    artifact_sources: tuple[Mapping[str, Any], ...]
    source_release: str
    source_version: str
    solver_execution_performed: bool = False
    writes_files: bool = False
    result_dataset_persistence: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "provenance": dict(self.provenance),
            "artifact_sources": [dict(item) for item in self.artifact_sources],
            "source_release": self.source_release,
            "source_version": self.source_version,
            "solver_execution_performed": self.solver_execution_performed,
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetReviewReadmePayload:
    """In-memory README payload requiring human review before persistence."""

    filename: str
    content: str
    review_required: bool = True
    writes_files: bool = False
    result_dataset_persistence: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "filename": self.filename,
            "content": self.content,
            "review_required": self.review_required,
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetSchemaValidation:
    """Validation summary for an in-memory ResultDataset schema payload."""

    status: FEASpecCalculiXResultDatasetSchemaStatus
    diagnostics: tuple[FEASpecCalculiXResultDatasetSchemaDiagnostic, ...]
    has_blockers: bool
    payload_valid: bool
    manifest_valid: bool
    readme_required: bool = True
    writes_files: bool = False
    result_dataset_persistence: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "has_blockers": self.has_blockers,
            "payload_valid": self.payload_valid,
            "manifest_valid": self.manifest_valid,
            "readme_required": self.readme_required,
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetSchemaPayload:
    """Deterministic in-memory ResultDataset schema payload bundle."""

    status: FEASpecCalculiXResultDatasetSchemaStatus
    schema: FEASpecCalculiXResultDatasetSchemaVersion
    dataset: Mapping[str, Any]
    manifest_payload: FEASpecCalculiXResultDatasetManifestPayload
    diagnostics_payload: FEASpecCalculiXResultDatasetDiagnosticsPayload
    provenance_payload: FEASpecCalculiXResultDatasetProvenancePayload
    readme_payload: FEASpecCalculiXResultDatasetReviewReadmePayload
    schema_diagnostics: tuple[
        FEASpecCalculiXResultDatasetSchemaDiagnostic,
        ...,
    ]
    source_diagnostics: tuple[Mapping[str, Any], ...]
    write_plan_diagnostics: tuple[Mapping[str, Any], ...]
    limitations: tuple[Mapping[str, Any], ...]
    planned_files: tuple[Mapping[str, Any], ...]
    artifact_references: tuple[Mapping[str, Any], ...]
    writes_files: bool = False
    result_dataset_persistence: bool = False
    solver_execution_performed: bool = False
    field_values_parsed: bool = False
    mesh_reconstructed: bool = False
    unit_inference_performed: bool = False
    engineering_correctness_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "schema": self.schema.to_dict(),
            "dataset": dict(self.dataset),
            "manifest_payload": self.manifest_payload.to_dict(),
            "diagnostics_payload": self.diagnostics_payload.to_dict(),
            "provenance_payload": self.provenance_payload.to_dict(),
            "readme_payload": self.readme_payload.to_dict(),
            "schema_diagnostics": [
                item.to_dict() for item in self.schema_diagnostics
            ],
            "source_diagnostics": [
                dict(item) for item in self.source_diagnostics
            ],
            "write_plan_diagnostics": [
                dict(item) for item in self.write_plan_diagnostics
            ],
            "limitations": [dict(item) for item in self.limitations],
            "planned_files": [dict(item) for item in self.planned_files],
            "artifact_references": [
                dict(item) for item in self.artifact_references
            ],
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
            "solver_execution_performed": self.solver_execution_performed,
            "field_values_parsed": self.field_values_parsed,
            "mesh_reconstructed": self.mesh_reconstructed,
            "unit_inference_performed": self.unit_inference_performed,
            "engineering_correctness_claimed": self.engineering_correctness_claimed,
        }


def build_calculix_result_dataset_schema_payload(
    mapping: object,
    write_plan: object,
    *,
    schema_version: str | None = None,
    producer_version: str | None = None,
    source_version: str | None = None,
    source_release: str | None = None,
) -> FEASpecCalculiXResultDatasetSchemaPayload:
    """Build an in-memory schema payload bundle without persistence."""

    mapping_payload = _object_mapping(mapping)
    write_plan_payload = _object_mapping(write_plan)
    provenance = _mapping_from_payload(mapping_payload.get("provenance"))
    artifacts = _mapping_tuple(mapping_payload.get("artifacts"))
    source_diagnostics = _mapping_tuple(mapping_payload.get("diagnostics"))
    limitations = _mapping_tuple(mapping_payload.get("limitations"))
    planned_files = _mapping_tuple(write_plan_payload.get("planned_files"))
    artifact_references = _mapping_tuple(
        write_plan_payload.get("artifact_references")
    )
    write_plan_diagnostics = _mapping_tuple(write_plan_payload.get("diagnostics"))
    schema = FEASpecCalculiXResultDatasetSchemaVersion(
        schema_name=str(
            write_plan_payload.get("schema_name") or WRITE_SCHEMA_NAME
        ),
        schema_version=str(
            schema_version
            if schema_version is not None
            else write_plan_payload.get("schema_version", WRITE_SCHEMA_VERSION)
        ),
        producer_version=str(
            producer_version
            or write_plan_payload.get("producer_version")
            or OSW_VERSION
        ),
        source_version=str(
            source_version
            or provenance.get("osw_version")
            or OSW_VERSION
        ),
        source_release=str(
            source_release
            or write_plan_payload.get("source_release")
            or provenance.get("release_tag")
            or "v0.1.4-rc1"
        ),
    )
    schema_diagnostics = _schema_diagnostics(
        mapping=mapping,
        write_plan=write_plan,
        mapping_payload=mapping_payload,
        write_plan_payload=write_plan_payload,
        schema=schema,
        artifacts=artifacts,
        provenance=provenance,
        source_diagnostics=source_diagnostics,
        limitations=limitations,
        planned_files=planned_files,
    )
    dataset = _dataset_payload(mapping_payload, schema)
    manifest_payload = _manifest_payload(
        schema=schema,
        dataset=dataset,
        planned_files=planned_files,
        artifact_references=artifact_references,
    )
    diagnostics_payload = _diagnostics_payload(
        schema_diagnostics=schema_diagnostics,
        source_diagnostics=source_diagnostics,
        write_plan_diagnostics=write_plan_diagnostics,
    )
    provenance_payload = _provenance_payload(
        provenance=provenance,
        artifacts=artifacts,
        schema=schema,
    )
    readme_payload = _review_readme_payload(schema=schema, dataset=dataset)
    status = _payload_status(schema_diagnostics)

    return FEASpecCalculiXResultDatasetSchemaPayload(
        status=status,
        schema=schema,
        dataset=dataset,
        manifest_payload=manifest_payload,
        diagnostics_payload=diagnostics_payload,
        provenance_payload=provenance_payload,
        readme_payload=readme_payload,
        schema_diagnostics=schema_diagnostics,
        source_diagnostics=source_diagnostics,
        write_plan_diagnostics=write_plan_diagnostics,
        limitations=limitations,
        planned_files=planned_files,
        artifact_references=artifact_references,
        solver_execution_performed=bool(
            mapping_payload.get("solver_execution_performed", False)
        ),
        field_values_parsed=bool(
            mapping_payload.get("frd_numerical_field_parser", False)
        ),
        mesh_reconstructed=bool(mapping_payload.get("mesh_reconstructed", False)),
        unit_inference_performed=bool(mapping_payload.get("units_inferred", False)),
        engineering_correctness_claimed=bool(
            mapping_payload.get("engineering_correctness_claimed", False)
        ),
    )


def build_calculix_result_dataset_manifest_payload(
    payload: FEASpecCalculiXResultDatasetSchemaPayload,
) -> FEASpecCalculiXResultDatasetManifestPayload:
    """Return the in-memory manifest payload from a schema bundle."""

    return payload.manifest_payload


def build_calculix_result_dataset_diagnostics_payload(
    payload: FEASpecCalculiXResultDatasetSchemaPayload,
) -> FEASpecCalculiXResultDatasetDiagnosticsPayload:
    """Return the in-memory diagnostics payload from a schema bundle."""

    return payload.diagnostics_payload


def build_calculix_result_dataset_provenance_payload(
    payload: FEASpecCalculiXResultDatasetSchemaPayload,
) -> FEASpecCalculiXResultDatasetProvenancePayload:
    """Return the in-memory provenance payload from a schema bundle."""

    return payload.provenance_payload


def build_calculix_result_dataset_review_readme(
    payload: FEASpecCalculiXResultDatasetSchemaPayload,
) -> FEASpecCalculiXResultDatasetReviewReadmePayload:
    """Return the in-memory review README payload from a schema bundle."""

    return payload.readme_payload


def validate_calculix_result_dataset_schema_payload(
    payload: FEASpecCalculiXResultDatasetSchemaPayload,
) -> FEASpecCalculiXResultDatasetSchemaValidation:
    """Validate an in-memory schema payload bundle."""

    diagnostics = list(payload.schema_diagnostics)
    schema = payload.schema
    if not schema.schema_name:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_SCHEMA_NAME_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset schema name is missing.",
                suggested_fix="Use the FEASpec CalculiX ResultDataset schema name.",
            )
        )
    if not schema.schema_version:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_SCHEMA_VERSION_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset schema version is missing.",
                suggested_fix="Build the payload with an explicit schema version.",
            )
        )
    if not schema.producer_version:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_PRODUCER_VERSION_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "Payload producer version is missing.",
                suggested_fix="Use OSW package metadata as producer version.",
            )
        )
    if not schema.source_version:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_SOURCE_VERSION_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "Payload source version is missing.",
                suggested_fix="Preserve OSW source version in provenance.",
            )
        )
    if not payload.dataset:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_PAYLOAD_INVALID,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset schema payload is empty.",
                suggested_fix="Build the payload from a reviewed draft mapping.",
            )
        )
    manifest_valid = bool(payload.manifest_payload.planned_files)
    if not manifest_valid:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_MANIFEST_INVALID,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset manifest payload has no planned files.",
                suggested_fix="Build the payload from a reviewed write plan.",
            )
        )
    if not payload.readme_payload.content:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_README_REQUIRED,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "Review README payload is required.",
                suggested_fix="Include the review-first README payload.",
            )
        )

    diagnostics_tuple = tuple(_dedupe_schema_diagnostics(diagnostics))
    has_blockers = any(item.blocks_payload for item in diagnostics_tuple)
    status = (
        FEASpecCalculiXResultDatasetSchemaStatus.BLOCKED
        if has_blockers
        else payload.status
    )
    return FEASpecCalculiXResultDatasetSchemaValidation(
        status=status,
        diagnostics=diagnostics_tuple,
        has_blockers=has_blockers,
        payload_valid=not has_blockers,
        manifest_valid=manifest_valid,
        writes_files=payload.writes_files,
        result_dataset_persistence=payload.result_dataset_persistence,
    )


def explain_calculix_result_dataset_schema_payload(
    payload: FEASpecCalculiXResultDatasetSchemaPayload,
) -> list[str]:
    """Return reviewer-readable notes for an in-memory schema payload."""

    validation = validate_calculix_result_dataset_schema_payload(payload)
    lines = [
        f"ResultDataset schema payload status: {validation.status.value}.",
        f"Schema: {payload.schema.schema_name} {payload.schema.schema_version}.",
        f"Dataset id: {payload.dataset.get('dataset_id', '')}.",
        f"Artifacts referenced: {len(payload.dataset.get('artifacts', ())) }.",
        f"Planned output files: {len(payload.planned_files)}.",
        "ResultDataset files written: false.",
        "ResultDataset persistence implemented: false.",
        "Solver execution performed by schema model: false.",
        "Human review required: true.",
    ]
    for diagnostic in validation.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


def _schema_diagnostics(
    *,
    mapping: object,
    write_plan: object,
    mapping_payload: Mapping[str, Any],
    write_plan_payload: Mapping[str, Any],
    schema: FEASpecCalculiXResultDatasetSchemaVersion,
    artifacts: Sequence[Mapping[str, Any]],
    provenance: Mapping[str, Any],
    source_diagnostics: Sequence[Mapping[str, Any]],
    limitations: Sequence[Mapping[str, Any]],
    planned_files: Sequence[Mapping[str, Any]],
) -> tuple[FEASpecCalculiXResultDatasetSchemaDiagnostic, ...]:
    diagnostics: list[FEASpecCalculiXResultDatasetSchemaDiagnostic] = [
        _diag(
            CalculiXResultDatasetSchemaDiagnosticCode.FDS_SCHEMA_MODEL_ONLY,
            CalculiXResultDatasetSchemaSeverity.INFO,
            "ResultDataset schema payloads are modeled in memory only.",
            blocks_payload=False,
        ),
        _diag(
            CalculiXResultDatasetSchemaDiagnosticCode.FDS_FILE_WRITE_FORBIDDEN,
            CalculiXResultDatasetSchemaSeverity.INFO,
            "This schema model does not write ResultDataset files.",
            blocks_payload=False,
        ),
        _diag(
            CalculiXResultDatasetSchemaDiagnosticCode.FDS_PERSISTENCE_NOT_IMPLEMENTED,
            CalculiXResultDatasetSchemaSeverity.INFO,
            "ResultDataset persistence is not implemented in this gate.",
            blocks_payload=False,
        ),
    ]
    if not mapping_payload or mapping is None:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_DRAFT_MAPPING_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset draft mapping is missing.",
                suggested_fix="Build a ResultDataset draft mapping first.",
            )
        )
    if not write_plan_payload or write_plan is None:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_WRITE_PLAN_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset write plan is missing.",
                suggested_fix="Build and review a ResultDataset write plan first.",
            )
        )
    else:
        validation = validate_calculix_result_dataset_write_plan(write_plan)
        if validation.has_blockers:
            diagnostics.append(
                _diag(
                    CalculiXResultDatasetSchemaDiagnosticCode.FDS_WRITE_PLAN_BLOCKED,
                    CalculiXResultDatasetSchemaSeverity.BLOCKER,
                    "ResultDataset write plan has blockers.",
                    suggested_fix="Resolve write-plan blockers before payload review.",
                )
            )
    if not schema.schema_name:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_SCHEMA_NAME_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset schema name is missing.",
            )
        )
    if not schema.schema_version:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_SCHEMA_VERSION_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset schema version is missing.",
            )
        )
    if not schema.producer_version:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_PRODUCER_VERSION_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "Payload producer version is missing.",
            )
        )
    if not schema.source_version:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_SOURCE_VERSION_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "Payload source version is missing.",
            )
        )
    if not artifacts:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_ARTIFACTS_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset schema payload has no artifact references.",
                suggested_fix="Rebuild the draft mapping from scanned result artifacts.",
            )
        )
    if not provenance:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_PROVENANCE_MISSING,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "ResultDataset schema payload has no provenance.",
                suggested_fix="Preserve run metadata and export manifest provenance.",
            )
        )
    if not source_diagnostics:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_DIAGNOSTICS_MISSING,
                CalculiXResultDatasetSchemaSeverity.WARNING,
                "ResultDataset schema payload has no carried source diagnostics.",
                blocks_payload=False,
            )
        )
    if not limitations:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_LIMITATIONS_MISSING,
                CalculiXResultDatasetSchemaSeverity.WARNING,
                "ResultDataset schema payload has no carried limitations.",
                blocks_payload=False,
            )
        )
    if not planned_files:
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_MANIFEST_INVALID,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "Manifest payload has no planned files.",
                suggested_fix="Build the payload from a reviewed write plan.",
            )
        )
    elif not any(
        item.get("relative_path") == "README_REVIEW_FIRST.txt"
        for item in planned_files
    ):
        diagnostics.append(
            _diag(
                CalculiXResultDatasetSchemaDiagnosticCode.FDS_README_REQUIRED,
                CalculiXResultDatasetSchemaSeverity.BLOCKER,
                "Review README is required in the planned layout.",
                suggested_fix="Use the standard ResultDataset output layout.",
            )
        )
    return tuple(_dedupe_schema_diagnostics(diagnostics))


def _dataset_payload(
    mapping_payload: Mapping[str, Any],
    schema: FEASpecCalculiXResultDatasetSchemaVersion,
) -> Mapping[str, Any]:
    return {
        "schema": schema.to_dict(),
        "dataset_id": str(mapping_payload.get("dataset_id", "")),
        "source": str(mapping_payload.get("source", "")),
        "solver": str(mapping_payload.get("solver", "CalculiX")),
        "analysis_type": str(mapping_payload.get("analysis_type", "")),
        "status": str(mapping_payload.get("status", "")),
        "artifacts": _mapping_tuple(mapping_payload.get("artifacts")),
        "status_summaries": _mapping_tuple(
            mapping_payload.get("status_summaries")
        ),
        "scalar_candidates": _mapping_tuple(
            mapping_payload.get("scalar_candidates")
        ),
        "table_candidates": _mapping_tuple(mapping_payload.get("table_candidates")),
        "field_references": _mapping_tuple(mapping_payload.get("field_references")),
        "provenance": _mapping_from_payload(mapping_payload.get("provenance")),
        "diagnostics": _mapping_tuple(mapping_payload.get("diagnostics")),
        "limitations": _mapping_tuple(mapping_payload.get("limitations")),
        "writes_files": False,
        "result_dataset_persistence": False,
        "solver_execution_performed": bool(
            mapping_payload.get("solver_execution_performed", False)
        ),
        "field_values_parsed": bool(
            mapping_payload.get("frd_numerical_field_parser", False)
        ),
        "mesh_reconstructed": bool(mapping_payload.get("mesh_reconstructed", False)),
        "unit_inference_performed": bool(mapping_payload.get("units_inferred", False)),
        "engineering_correctness_claimed": bool(
            mapping_payload.get("engineering_correctness_claimed", False)
        ),
    }


def _manifest_payload(
    *,
    schema: FEASpecCalculiXResultDatasetSchemaVersion,
    dataset: Mapping[str, Any],
    planned_files: Sequence[Mapping[str, Any]],
    artifact_references: Sequence[Mapping[str, Any]],
) -> FEASpecCalculiXResultDatasetManifestPayload:
    return FEASpecCalculiXResultDatasetManifestPayload(
        schema=schema,
        dataset_id=str(dataset.get("dataset_id", "")),
        source=str(dataset.get("source", "")),
        solver=str(dataset.get("solver", "CalculiX")),
        analysis_type=str(dataset.get("analysis_type", "")),
        planned_files=tuple(dict(item) for item in planned_files),
        artifact_references=tuple(dict(item) for item in artifact_references),
        solver_execution_performed=False,
    )


def _diagnostics_payload(
    *,
    schema_diagnostics: Sequence[FEASpecCalculiXResultDatasetSchemaDiagnostic],
    source_diagnostics: Sequence[Mapping[str, Any]],
    write_plan_diagnostics: Sequence[Mapping[str, Any]],
) -> FEASpecCalculiXResultDatasetDiagnosticsPayload:
    schema_records = tuple(item.to_dict() for item in schema_diagnostics)
    diagnostics = tuple(
        _dedupe_mappings(
            (
                *schema_records,
                *source_diagnostics,
                *write_plan_diagnostics,
            )
        )
    )
    return FEASpecCalculiXResultDatasetDiagnosticsPayload(
        diagnostics=diagnostics,
        schema_diagnostics=schema_records,
        source_diagnostics=tuple(dict(item) for item in source_diagnostics),
        write_plan_diagnostics=tuple(dict(item) for item in write_plan_diagnostics),
        diagnostic_count=len(diagnostics),
        blocker_count=sum(1 for item in diagnostics if _blocks(item)),
    )


def _provenance_payload(
    *,
    provenance: Mapping[str, Any],
    artifacts: Sequence[Mapping[str, Any]],
    schema: FEASpecCalculiXResultDatasetSchemaVersion,
) -> FEASpecCalculiXResultDatasetProvenancePayload:
    artifact_sources = tuple(
        {
            "source_path": str(item.get("source_path", "")),
            "filename": str(item.get("filename", "")),
            "suffix": str(item.get("suffix", "")),
            "sha256": str(item.get("sha256", "")),
            "size_bytes": item.get("size_bytes", 0),
        }
        for item in artifacts
    )
    return FEASpecCalculiXResultDatasetProvenancePayload(
        provenance=dict(provenance),
        artifact_sources=artifact_sources,
        source_release=schema.source_release,
        source_version=schema.source_version,
        solver_execution_performed=bool(
            provenance.get("solver_execution_performed", False)
        ),
    )


def _review_readme_payload(
    *,
    schema: FEASpecCalculiXResultDatasetSchemaVersion,
    dataset: Mapping[str, Any],
) -> FEASpecCalculiXResultDatasetReviewReadmePayload:
    dataset_id = str(dataset.get("dataset_id", ""))
    content = "\n".join(
        (
            "README_REVIEW_FIRST",
            "",
            f"Dataset id: {dataset_id}",
            f"Schema: {schema.schema_name} {schema.schema_version}",
            f"Source release: {schema.source_release}",
            "",
            "This is an in-memory ResultDataset schema payload.",
            "Human review is required before any future persistence gate.",
            "No ResultDataset persistence is implemented here.",
            "No file writes occur in this schema model.",
            "No solver execution is performed by this schema model.",
            "GitHub state verified 2026-07-14: Issue #8 is closed after bounded "
            "WSL CalculiX evidence; this workflow does not broaden that closure.",
            "External solvers are optional and are not bundled.",
            "No industrial certification is claimed.",
        )
    )
    return FEASpecCalculiXResultDatasetReviewReadmePayload(
        filename="README_REVIEW_FIRST.txt",
        content=content,
    )


def _payload_status(
    diagnostics: Sequence[FEASpecCalculiXResultDatasetSchemaDiagnostic],
) -> FEASpecCalculiXResultDatasetSchemaStatus:
    if any(item.blocks_payload for item in diagnostics):
        return FEASpecCalculiXResultDatasetSchemaStatus.BLOCKED
    if any(
        item.severity is CalculiXResultDatasetSchemaSeverity.WARNING
        for item in diagnostics
    ):
        return FEASpecCalculiXResultDatasetSchemaStatus.PAYLOAD_READY_WITH_WARNINGS
    return FEASpecCalculiXResultDatasetSchemaStatus.PAYLOAD_READY


def _object_mapping(value: object) -> Mapping[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    return {}


def _mapping_from_payload(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "to_dict"):
        payload = value.to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    return {}


def _mapping_tuple(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    records: list[Mapping[str, Any]] = []
    for item in value:
        if isinstance(item, Mapping):
            records.append(dict(item))
        elif hasattr(item, "to_dict"):
            payload = item.to_dict()
            if isinstance(payload, Mapping):
                records.append(dict(payload))
    return tuple(records)


def _dedupe_schema_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXResultDatasetSchemaDiagnostic],
) -> list[FEASpecCalculiXResultDatasetSchemaDiagnostic]:
    seen: set[tuple[CalculiXResultDatasetSchemaDiagnosticCode, str, str]] = set()
    unique: list[FEASpecCalculiXResultDatasetSchemaDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.path, diagnostic.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(diagnostic)
    return unique


def _dedupe_mappings(items: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    seen: set[tuple[str, str, str, str]] = set()
    unique: list[Mapping[str, Any]] = []
    for item in items:
        key = (
            str(item.get("code", "")),
            str(item.get("path", "")),
            str(item.get("message", "")),
            str(item.get("source", "")),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(dict(item))
    return unique


def _blocks(item: Mapping[str, Any]) -> bool:
    return bool(
        item.get("blocks_payload")
        or item.get("blocks_write")
        or item.get("blocks_import")
        or item.get("blocks_mapping")
    )


def _diag(
    code: CalculiXResultDatasetSchemaDiagnosticCode,
    severity: CalculiXResultDatasetSchemaSeverity,
    message: str,
    *,
    path: str = "",
    suggested_fix: str = "",
    blocks_payload: bool | None = None,
) -> FEASpecCalculiXResultDatasetSchemaDiagnostic:
    return FEASpecCalculiXResultDatasetSchemaDiagnostic.make(
        code,
        severity,
        message,
        path=path,
        suggested_fix=suggested_fix,
        blocks_payload=blocks_payload,
    )
