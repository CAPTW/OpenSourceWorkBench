"""In-memory ResultDataset draft mapping for FEASpec CalculiX results.

The mapping in this module consumes the safe result import plan and existing
artifact scanner payloads. It does not parse additional solver data, write
ResultDataset files, invoke external commands, or mutate ProjectSchema records.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Any

__all__ = [
    "FEASpecCalculiXResultDatasetDraftMapping",
    "FEASpecCalculiXResultDatasetDraftSummary",
    "FEASpecCalculiXResultDraftArtifact",
    "FEASpecCalculiXResultDraftScalar",
    "FEASpecCalculiXResultDraftTable",
    "FEASpecCalculiXResultDraftFieldReference",
    "FEASpecCalculiXResultDraftProvenance",
    "FEASpecCalculiXResultDraftLimitation",
    "FEASpecCalculiXResultDraftStatus",
    "build_calculix_result_dataset_draft_mapping",
    "summarize_calculix_result_dataset_draft_mapping",
    "explain_calculix_result_dataset_draft_mapping",
]


class FEASpecCalculiXResultDraftStatus(str, Enum):
    """Status for the in-memory ResultDataset draft mapping."""

    DRAFT_READY = "draft-ready"
    DRAFT_READY_WITH_WARNINGS = "draft-ready-with-warnings"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDraftArtifact:
    """Artifact metadata mapped into a ResultDataset draft reference."""

    source_path: str
    filename: str
    suffix: str
    artifact_kind: str
    role: str
    sha256: str
    size_bytes: int
    parser_summary_keys: tuple[str, ...] = ()
    source: str = "result-import-plan"

    def to_dict(self) -> dict[str, object]:
        return {
            "source_path": self.source_path,
            "filename": self.filename,
            "suffix": self.suffix,
            "artifact_kind": self.artifact_kind,
            "role": self.role,
            "sha256": self.sha256,
            "size_bytes": self.size_bytes,
            "parser_summary_keys": list(self.parser_summary_keys),
            "source": self.source,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDraftScalar:
    """Scalar preview candidate mapped from an existing .dat minimal parse."""

    label: str
    raw_value: str
    parsed_value: object
    unit: str
    source_path: str
    artifact: str
    line_number: int
    section_heading: str
    section_kind: str
    diagnostics: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "raw_value": self.raw_value,
            "parsed_value": self.parsed_value,
            "unit": self.unit,
            "source_path": self.source_path,
            "artifact": self.artifact,
            "line_number": self.line_number,
            "section_heading": self.section_heading,
            "section_kind": self.section_kind,
            "diagnostics": [dict(item) for item in self.diagnostics],
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDraftTable:
    """Table preview candidate mapped from an existing .dat minimal parse."""

    heading: str
    raw_headers: tuple[str, ...]
    raw_cells: tuple[tuple[str, ...], ...]
    parsed_cells: tuple[tuple[object, ...], ...]
    unit_context: Mapping[str, str]
    row_count: int
    column_count: int
    source_path: str
    artifact: str
    line_start: int
    line_end: int
    diagnostics: tuple[Mapping[str, Any], ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "heading": self.heading,
            "raw_headers": list(self.raw_headers),
            "raw_cells": [list(row) for row in self.raw_cells],
            "parsed_cells": [list(row) for row in self.parsed_cells],
            "unit_context": dict(self.unit_context),
            "row_count": self.row_count,
            "column_count": self.column_count,
            "source_path": self.source_path,
            "artifact": self.artifact,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "diagnostics": [dict(item) for item in self.diagnostics],
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDraftFieldReference:
    """Deferred .frd field or mesh reference, with no parsed arrays."""

    reference_kind: str
    raw_label: str
    block_kind: str
    source_path: str
    artifact: str
    block_index: int
    line_number: int
    values_parsed: bool = False
    mesh_reconstructed: bool = False
    units_inferred: bool = False
    limitation: str = ".frd field values are not parsed in this draft mapping."

    def to_dict(self) -> dict[str, object]:
        return {
            "reference_kind": self.reference_kind,
            "raw_label": self.raw_label,
            "block_kind": self.block_kind,
            "source_path": self.source_path,
            "artifact": self.artifact,
            "block_index": self.block_index,
            "line_number": self.line_number,
            "values_parsed": self.values_parsed,
            "mesh_reconstructed": self.mesh_reconstructed,
            "units_inferred": self.units_inferred,
            "limitation": self.limitation,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDraftProvenance:
    """Provenance copied from the result import plan."""

    result_dir: str
    run_metadata_path: str = ""
    export_manifest_path: str = ""
    source_feaspec_id: str = ""
    case_id: str = ""
    osw_version: str = ""
    release_tag: str = ""
    run_status: str = ""
    solver_execution_performed: bool = False
    exit_code: int | None = None
    timed_out: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "result_dir": self.result_dir,
            "run_metadata_path": self.run_metadata_path,
            "export_manifest_path": self.export_manifest_path,
            "source_feaspec_id": self.source_feaspec_id,
            "case_id": self.case_id,
            "osw_version": self.osw_version,
            "release_tag": self.release_tag,
            "run_status": self.run_status,
            "solver_execution_performed": self.solver_execution_performed,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDraftLimitation:
    """Reader-visible limitation preserved in the draft mapping."""

    message: str
    source: str = "result-import"
    blocks_mapping: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "message": self.message,
            "source": self.source,
            "blocks_mapping": self.blocks_mapping,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetDraftMapping:
    """Stable in-memory draft mapping for future ResultDataset persistence."""

    dataset_id: str
    source: str
    solver: str
    analysis_type: str
    status: FEASpecCalculiXResultDraftStatus
    artifacts: tuple[FEASpecCalculiXResultDraftArtifact, ...] = ()
    status_summaries: tuple[Mapping[str, Any], ...] = ()
    scalar_candidates: tuple[FEASpecCalculiXResultDraftScalar, ...] = ()
    table_candidates: tuple[FEASpecCalculiXResultDraftTable, ...] = ()
    field_references: tuple[FEASpecCalculiXResultDraftFieldReference, ...] = ()
    provenance: FEASpecCalculiXResultDraftProvenance | None = None
    diagnostics: tuple[Mapping[str, Any], ...] = ()
    limitations: tuple[FEASpecCalculiXResultDraftLimitation, ...] = ()
    writes_files: bool = False
    result_dataset_persistence: bool = False
    solver_execution_performed: bool = False
    frd_numerical_field_parser: bool = False
    mesh_reconstructed: bool = False
    units_inferred: bool = False
    engineering_correctness_claimed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_id": self.dataset_id,
            "source": self.source,
            "solver": self.solver,
            "analysis_type": self.analysis_type,
            "status": self.status.value,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "status_summaries": [dict(item) for item in self.status_summaries],
            "scalar_candidates": [item.to_dict() for item in self.scalar_candidates],
            "table_candidates": [item.to_dict() for item in self.table_candidates],
            "field_references": [item.to_dict() for item in self.field_references],
            "provenance": (
                self.provenance.to_dict() if self.provenance is not None else {}
            ),
            "diagnostics": [dict(item) for item in self.diagnostics],
            "limitations": [item.to_dict() for item in self.limitations],
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
            "solver_execution_performed": self.solver_execution_performed,
            "frd_numerical_field_parser": self.frd_numerical_field_parser,
            "mesh_reconstructed": self.mesh_reconstructed,
            "units_inferred": self.units_inferred,
            "engineering_correctness_claimed": self.engineering_correctness_claimed,
        }


@dataclass(frozen=True, slots=True)
class FEASpecCalculiXResultDatasetDraftSummary:
    """Compact counts for the in-memory draft mapping."""

    status: FEASpecCalculiXResultDraftStatus
    artifact_count: int
    status_summary_count: int
    scalar_candidate_count: int
    table_candidate_count: int
    field_reference_count: int
    limitation_count: int
    diagnostic_count: int
    writes_files: bool = False
    result_dataset_persistence: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "artifact_count": self.artifact_count,
            "status_summary_count": self.status_summary_count,
            "scalar_candidate_count": self.scalar_candidate_count,
            "table_candidate_count": self.table_candidate_count,
            "field_reference_count": self.field_reference_count,
            "limitation_count": self.limitation_count,
            "diagnostic_count": self.diagnostic_count,
            "writes_files": self.writes_files,
            "result_dataset_persistence": self.result_dataset_persistence,
        }


def build_calculix_result_dataset_draft_mapping(
    import_plan: object,
) -> FEASpecCalculiXResultDatasetDraftMapping:
    """Build a pure in-memory draft mapping from an import plan."""

    artifacts = tuple(_map_artifact(artifact) for artifact in _plan_artifacts(import_plan))
    status_summaries = tuple(
        _status_summary_record(artifact)
        for artifact in _plan_artifacts(import_plan)
        if _metadata_mapping(artifact).get("status_summary")
    )
    scalar_candidates = tuple(
        scalar
        for artifact in _plan_artifacts(import_plan)
        for scalar in _scalar_candidates(artifact)
    )
    table_candidates = tuple(
        table
        for artifact in _plan_artifacts(import_plan)
        for table in _table_candidates(artifact)
    )
    field_references = tuple(
        reference
        for artifact in _plan_artifacts(import_plan)
        for reference in _field_reference_candidates(artifact)
    )
    diagnostics = tuple(
        _dedupe_mappings(
            [
                *_plan_diagnostics(import_plan),
                *(
                    diagnostic
                    for artifact in _plan_artifacts(import_plan)
                    for diagnostic in _artifact_diagnostics(artifact)
                ),
            ]
        )
    )
    limitations = tuple(_draft_limitations(import_plan, _plan_artifacts(import_plan)))
    provenance = _draft_provenance(import_plan)
    status = _mapping_status(import_plan, artifacts, diagnostics)
    dataset_id = (
        provenance.case_id
        or provenance.source_feaspec_id
        or "feaspec-calculix-result-draft"
    )
    source = _plan_result_dir(import_plan) or provenance.result_dir

    return FEASpecCalculiXResultDatasetDraftMapping(
        dataset_id=dataset_id,
        source=source,
        solver="CalculiX",
        analysis_type="linear_static",
        status=status,
        artifacts=artifacts,
        status_summaries=status_summaries,
        scalar_candidates=scalar_candidates,
        table_candidates=table_candidates,
        field_references=field_references,
        provenance=provenance,
        diagnostics=diagnostics,
        limitations=limitations,
    )


def summarize_calculix_result_dataset_draft_mapping(
    mapping: FEASpecCalculiXResultDatasetDraftMapping,
) -> FEASpecCalculiXResultDatasetDraftSummary:
    """Return compact counts for CLI and report previews."""

    return FEASpecCalculiXResultDatasetDraftSummary(
        status=mapping.status,
        artifact_count=len(mapping.artifacts),
        status_summary_count=len(mapping.status_summaries),
        scalar_candidate_count=len(mapping.scalar_candidates),
        table_candidate_count=len(mapping.table_candidates),
        field_reference_count=len(mapping.field_references),
        limitation_count=len(mapping.limitations),
        diagnostic_count=len(mapping.diagnostics),
        writes_files=mapping.writes_files,
        result_dataset_persistence=mapping.result_dataset_persistence,
    )


def explain_calculix_result_dataset_draft_mapping(
    mapping: FEASpecCalculiXResultDatasetDraftMapping,
) -> list[str]:
    """Return reviewer-readable draft mapping notes."""

    summary = summarize_calculix_result_dataset_draft_mapping(mapping)
    return [
        f"ResultDataset draft mapping status: {summary.status.value}.",
        f"Artifacts mapped: {summary.artifact_count}.",
        f"Status summaries mapped: {summary.status_summary_count}.",
        f"DAT scalar candidates mapped: {summary.scalar_candidate_count}.",
        f"DAT table candidates mapped: {summary.table_candidate_count}.",
        f"FRD field references mapped: {summary.field_reference_count}.",
        "ResultDataset files written: false.",
        "ResultDataset persistence implemented: false.",
        "FRD numerical field parser implemented: false.",
        "Mesh reconstruction performed: false.",
        "Solver execution performed: false.",
    ]


def _plan_artifacts(import_plan: object) -> tuple[object, ...]:
    artifacts = getattr(import_plan, "artifacts", ())
    if isinstance(artifacts, Sequence) and not isinstance(artifacts, (str, bytes)):
        return tuple(artifacts)
    return ()


def _plan_result_dir(import_plan: object) -> str:
    result_dir = getattr(import_plan, "result_dir", "")
    return str(result_dir) if result_dir else ""


def _status_text(status: object) -> str:
    return str(getattr(status, "value", status) or "")


def _artifact_kind_text(artifact: object) -> str:
    kind = getattr(artifact, "kind", "")
    return _status_text(kind)


def _metadata_mapping(artifact: object) -> Mapping[str, Any]:
    metadata = getattr(artifact, "metadata", {})
    return metadata if isinstance(metadata, Mapping) else {}


def _map_artifact(artifact: object) -> FEASpecCalculiXResultDraftArtifact:
    metadata = _metadata_mapping(artifact)
    return FEASpecCalculiXResultDraftArtifact(
        source_path=str(getattr(artifact, "path", "")),
        filename=str(getattr(artifact, "filename", "")),
        suffix=str(getattr(artifact, "suffix", "")),
        artifact_kind=_artifact_kind_text(artifact),
        role=str(getattr(artifact, "role", "")),
        sha256=str(getattr(artifact, "sha256", "")),
        size_bytes=_int_value(getattr(artifact, "size_bytes", 0)),
        parser_summary_keys=tuple(
            key
            for key in (
                "result_parser",
                "status_summary",
                "dat_section_summary",
                "dat_minimal_parse_summary",
                "frd_block_summary",
            )
            if key in metadata
        ),
        source=str(getattr(artifact, "source", "directory")),
    )


def _status_summary_record(artifact: object) -> Mapping[str, Any]:
    metadata = _metadata_mapping(artifact)
    summary = metadata.get("status_summary")
    scan = metadata.get("status_scan")
    scan_mapping = scan if isinstance(scan, Mapping) else {}
    return {
        "artifact": str(getattr(artifact, "filename", "")),
        "artifact_kind": _artifact_kind_text(artifact),
        "source_path": str(getattr(artifact, "path", "")),
        "summary": dict(summary) if isinstance(summary, Mapping) else {},
        "line_count": _int_value(scan_mapping.get("line_count")),
        "processed_line_count": _int_value(scan_mapping.get("processed_line_count")),
    }


def _scalar_candidates(
    artifact: object,
) -> tuple[FEASpecCalculiXResultDraftScalar, ...]:
    parse_payload = _metadata_mapping(artifact).get("dat_minimal_parse")
    if not isinstance(parse_payload, Mapping):
        return ()
    scalars = parse_payload.get("scalar_candidates", ())
    if not isinstance(scalars, Sequence) or isinstance(scalars, (str, bytes)):
        return ()
    return tuple(
        FEASpecCalculiXResultDraftScalar(
            label=str(item.get("label", "")),
            raw_value=str(item.get("raw_value", "")),
            parsed_value=item.get("value"),
            unit=str(item.get("unit", "")),
            source_path=str(item.get("source_path") or getattr(artifact, "path", "")),
            artifact=str(getattr(artifact, "filename", "")),
            line_number=_int_value(item.get("line_number")),
            section_heading=str(item.get("section_heading", "")),
            section_kind=str(item.get("section_kind", "")),
        )
        for item in scalars
        if isinstance(item, Mapping)
    )


def _table_candidates(
    artifact: object,
) -> tuple[FEASpecCalculiXResultDraftTable, ...]:
    parse_payload = _metadata_mapping(artifact).get("dat_minimal_parse")
    if not isinstance(parse_payload, Mapping):
        return ()
    tables = parse_payload.get("table_candidates", ())
    if not isinstance(tables, Sequence) or isinstance(tables, (str, bytes)):
        return ()
    return tuple(
        _table_candidate_from_mapping(item, artifact)
        for item in tables
        if isinstance(item, Mapping)
    )


def _table_candidate_from_mapping(
    item: Mapping[str, Any],
    artifact: object,
) -> FEASpecCalculiXResultDraftTable:
    rows_payload = item.get("rows", ())
    raw_rows: list[tuple[str, ...]] = []
    parsed_rows: list[tuple[object, ...]] = []
    if isinstance(rows_payload, Sequence) and not isinstance(rows_payload, (str, bytes)):
        for row in rows_payload:
            if not isinstance(row, Sequence) or isinstance(row, (str, bytes)):
                continue
            raw_cells: list[str] = []
            parsed_cells: list[object] = []
            for cell in row:
                if isinstance(cell, Mapping):
                    raw_cells.append(str(cell.get("raw", "")))
                    parsed_cells.append(
                        cell.get("value") if bool(cell.get("parsed", False)) else None
                    )
                else:
                    raw_cells.append(str(cell))
                    parsed_cells.append(None)
            raw_rows.append(tuple(raw_cells))
            parsed_rows.append(tuple(parsed_cells))

    headers = _string_tuple(item.get("column_headers"))
    units = item.get("units")
    return FEASpecCalculiXResultDraftTable(
        heading=str(item.get("section_heading", "")),
        raw_headers=headers,
        raw_cells=tuple(raw_rows),
        parsed_cells=tuple(parsed_rows),
        unit_context=_string_mapping(units),
        row_count=_int_value(item.get("row_count")),
        column_count=_int_value(item.get("column_count")),
        source_path=str(item.get("source_path") or getattr(artifact, "path", "")),
        artifact=str(getattr(artifact, "filename", "")),
        line_start=_int_value(item.get("line_start")),
        line_end=_int_value(item.get("line_end")),
    )


def _field_reference_candidates(
    artifact: object,
) -> tuple[FEASpecCalculiXResultDraftFieldReference, ...]:
    scan_payload = _metadata_mapping(artifact).get("frd_block_scan")
    if not isinstance(scan_payload, Mapping):
        return ()
    candidates = scan_payload.get("reference_candidates", ())
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)):
        return ()
    return tuple(
        FEASpecCalculiXResultDraftFieldReference(
            reference_kind=str(item.get("reference_kind", "")),
            raw_label=str(item.get("label", "")),
            block_kind=str(item.get("block_kind", "")),
            source_path=str(item.get("source_path") or getattr(artifact, "path", "")),
            artifact=str(getattr(artifact, "filename", "")),
            block_index=_int_value(item.get("block_index")),
            line_number=_int_value(item.get("line_number")),
            values_parsed=bool(item.get("values_parsed", False)),
            mesh_reconstructed=bool(item.get("mesh_reconstructed", False)),
            units_inferred=bool(item.get("units_inferred", False)),
        )
        for item in candidates
        if isinstance(item, Mapping)
    )


def _draft_provenance(import_plan: object) -> FEASpecCalculiXResultDraftProvenance:
    provenance = getattr(import_plan, "provenance", None)
    if provenance is None:
        return FEASpecCalculiXResultDraftProvenance(
            result_dir=_plan_result_dir(import_plan)
        )
    return FEASpecCalculiXResultDraftProvenance(
        result_dir=str(getattr(provenance, "result_dir", _plan_result_dir(import_plan))),
        run_metadata_path=str(getattr(provenance, "run_metadata_path", "") or ""),
        export_manifest_path=str(
            getattr(provenance, "export_manifest_path", "") or ""
        ),
        source_feaspec_id=str(getattr(provenance, "source_feaspec_id", "")),
        case_id=str(getattr(provenance, "case_id", "")),
        osw_version=str(getattr(provenance, "osw_version", "")),
        release_tag=str(getattr(provenance, "release_tag", "")),
        run_status=str(getattr(provenance, "run_status", "")),
        solver_execution_performed=bool(
            getattr(provenance, "solver_execution_performed", False)
        ),
        exit_code=getattr(provenance, "exit_code", None),
        timed_out=bool(getattr(provenance, "timed_out", False)),
    )


def _plan_diagnostics(import_plan: object) -> list[Mapping[str, Any]]:
    diagnostics = getattr(import_plan, "diagnostics", ())
    if not isinstance(diagnostics, Sequence) or isinstance(diagnostics, (str, bytes)):
        return []
    return [
        _diagnostic_mapping(diagnostic, source="result-import-plan")
        for diagnostic in diagnostics
    ]


def _artifact_diagnostics(artifact: object) -> list[Mapping[str, Any]]:
    diagnostics: list[Mapping[str, Any]] = []
    metadata = _metadata_mapping(artifact)
    for key in (
        "result_parser",
        "status_scan",
        "dat_section_scan",
        "dat_minimal_parse",
        "frd_block_scan",
    ):
        payload = metadata.get(key)
        if not isinstance(payload, Mapping):
            continue
        records = payload.get("diagnostics", ())
        if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
            continue
        for record in records:
            diagnostics.append(
                _diagnostic_mapping(
                    record,
                    source=key,
                    artifact=str(getattr(artifact, "filename", "")),
                )
            )
    return diagnostics


def _diagnostic_mapping(
    diagnostic: object,
    *,
    source: str,
    artifact: str = "",
) -> Mapping[str, Any]:
    if isinstance(diagnostic, Mapping):
        payload = dict(diagnostic)
    elif hasattr(diagnostic, "to_dict"):
        payload = dict(diagnostic.to_dict())
    else:
        payload = {"message": str(diagnostic)}
    payload["source"] = source
    if artifact:
        payload["artifact"] = artifact
    return payload


def _draft_limitations(
    import_plan: object,
    artifacts: Sequence[object],
) -> list[FEASpecCalculiXResultDraftLimitation]:
    limitations: list[FEASpecCalculiXResultDraftLimitation] = []
    plan_limitations = getattr(import_plan, "limitations", ())
    if isinstance(plan_limitations, Sequence) and not isinstance(
        plan_limitations,
        (str, bytes),
    ):
        limitations.extend(
            FEASpecCalculiXResultDraftLimitation(str(item), "result-import-plan")
            for item in plan_limitations
        )
    limitations.extend(
        [
            FEASpecCalculiXResultDraftLimitation(
                "ResultDataset draft mapping only; no files are written.",
                "draft-mapping",
            ),
            FEASpecCalculiXResultDraftLimitation(
                "ResultDataset persistence is not implemented.",
                "draft-mapping",
            ),
            FEASpecCalculiXResultDraftLimitation(
                ".frd field values are not parsed.",
                "frd-block-scanner",
            ),
            FEASpecCalculiXResultDraftLimitation(
                "Mesh reconstruction is not performed.",
                "frd-block-scanner",
            ),
            FEASpecCalculiXResultDraftLimitation(
                "Units are preserved from parser outputs and are not inferred.",
                "draft-mapping",
            ),
            FEASpecCalculiXResultDraftLimitation(
                "GitHub state verified 2026-07-14: Issue #8 is closed after "
                "bounded WSL CalculiX evidence; this workflow does not broaden "
                "that closure.",
                "validation",
            ),
        ]
    )
    for artifact in artifacts:
        for key in ("status_summary", "frd_block_summary"):
            summary = _metadata_mapping(artifact).get(key)
            if not isinstance(summary, Mapping):
                continue
            for item in summary.get("limitations", ()) or ():
                limitations.append(
                    FEASpecCalculiXResultDraftLimitation(
                        str(item),
                        key,
                    )
                )
    return _dedupe_limitations(limitations)


def _mapping_status(
    import_plan: object,
    artifacts: Sequence[FEASpecCalculiXResultDraftArtifact],
    diagnostics: Sequence[Mapping[str, Any]],
) -> FEASpecCalculiXResultDraftStatus:
    plan_status = _status_text(getattr(import_plan, "status", ""))
    if plan_status == "blocked":
        return FEASpecCalculiXResultDraftStatus.BLOCKED
    if plan_status == "unsupported":
        return FEASpecCalculiXResultDraftStatus.UNSUPPORTED
    if plan_status in {"partial", "parse-not-implemented"}:
        return FEASpecCalculiXResultDraftStatus.PARTIAL
    if diagnostics:
        return FEASpecCalculiXResultDraftStatus.DRAFT_READY_WITH_WARNINGS
    if not artifacts:
        return FEASpecCalculiXResultDraftStatus.PARTIAL
    return FEASpecCalculiXResultDraftStatus.DRAFT_READY


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(str(item) for item in value)


def _string_mapping(value: object) -> Mapping[str, str]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def _int_value(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


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


def _dedupe_limitations(
    limitations: Sequence[FEASpecCalculiXResultDraftLimitation],
) -> list[FEASpecCalculiXResultDraftLimitation]:
    seen: set[tuple[str, str]] = set()
    unique: list[FEASpecCalculiXResultDraftLimitation] = []
    for item in limitations:
        key = (item.message, item.source)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
