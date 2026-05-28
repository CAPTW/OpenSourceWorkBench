"""CalculiX result summary models for parsed artifact data."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.solvers.log_parser import LogEvent, LogSeverity


class CalculiXResultStatus(StrEnum):
    """Summary parse status for already-collected CalculiX artifacts."""

    PARSED = "parsed"
    PARTIAL = "partial"
    MISSING_ARTIFACTS = "missing_artifacts"
    PARSE_ERROR = "parse_error"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class CalculiXFieldSummary:
    """Scalar summary for a parsed CalculiX result field."""

    name: str
    component_names: tuple[str, ...] = field(default_factory=tuple)
    location: str = "unknown"
    min_value: float | None = None
    max_value: float | None = None
    mean_value: float | None = None
    max_entity_id: int | None = None
    unit: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "component_names": list(self.component_names),
            "location": self.location,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mean_value": self.mean_value,
            "max_entity_id": self.max_entity_id,
            "unit": self.unit,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CalculiXFieldSummary:
        return cls(
            name=str(data.get("name", "")),
            component_names=tuple(str(item) for item in data.get("component_names", ()) or ()),
            location=str(data.get("location", "unknown")),
            min_value=_optional_float(data.get("min_value")),
            max_value=_optional_float(data.get("max_value")),
            mean_value=_optional_float(data.get("mean_value")),
            max_entity_id=_optional_int(data.get("max_entity_id")),
            unit=str(data.get("unit", "")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXDisplacementSummary:
    """Maximum displacement summary, usually node-based."""

    max_magnitude: float | None = None
    max_node_id: int | None = None
    components: tuple[float, float, float] | None = None
    unit: str = "m"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_magnitude": self.max_magnitude,
            "max_node_id": self.max_node_id,
            "components": list(self.components) if self.components is not None else None,
            "unit": self.unit,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CalculiXDisplacementSummary:
        components = data.get("components")
        return cls(
            max_magnitude=_optional_float(data.get("max_magnitude")),
            max_node_id=_optional_int(data.get("max_node_id")),
            components=_float_tuple(components, length=3) if components is not None else None,
            unit=str(data.get("unit", "m")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXStressSummary:
    """Maximum stress summary, usually element-based."""

    max_von_mises: float | None = None
    max_principal: float | None = None
    max_element_id: int | None = None
    unit: str = "Pa"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "max_von_mises": self.max_von_mises,
            "max_principal": self.max_principal,
            "max_element_id": self.max_element_id,
            "unit": self.unit,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CalculiXStressSummary:
        return cls(
            max_von_mises=_optional_float(data.get("max_von_mises")),
            max_principal=_optional_float(data.get("max_principal")),
            max_element_id=_optional_int(data.get("max_element_id")),
            unit=str(data.get("unit", "Pa")),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXStatusSummary:
    """Small status summary parsed from `.sta` and logs."""

    completed: bool | None = None
    increments: int = 0
    last_step: int | None = None
    last_increment: int | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)
    errors: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "completed": self.completed,
            "increments": self.increments,
            "last_step": self.last_step,
            "last_increment": self.last_increment,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CalculiXStatusSummary:
        return cls(
            completed=_optional_bool(data.get("completed")),
            increments=int(data.get("increments", 0)),
            last_step=_optional_int(data.get("last_step")),
            last_increment=_optional_int(data.get("last_increment")),
            warnings=tuple(str(item) for item in data.get("warnings", ()) or ()),
            errors=tuple(str(item) for item in data.get("errors", ()) or ()),
            metadata=dict(data.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class CalculiXParsedResults:
    """Report-friendly parsed CalculiX result summary."""

    source_run_id: str = ""
    job_name: str = ""
    dat_path: Path | None = None
    frd_path: Path | None = None
    sta_path: Path | None = None
    status: CalculiXResultStatus = CalculiXResultStatus.UNKNOWN
    displacement_summary: CalculiXDisplacementSummary | None = None
    stress_summary: CalculiXStressSummary | None = None
    field_summaries: tuple[CalculiXFieldSummary, ...] = field(default_factory=tuple)
    status_summary: CalculiXStatusSummary | None = None
    log_events: tuple[LogEvent, ...] = field(default_factory=tuple)
    artifacts: tuple[RunArtifact, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_run_id": self.source_run_id,
            "job_name": self.job_name,
            "dat_path": str(self.dat_path) if self.dat_path else "",
            "frd_path": str(self.frd_path) if self.frd_path else "",
            "sta_path": str(self.sta_path) if self.sta_path else "",
            "status": self.status.value,
            "displacement_summary": (
                self.displacement_summary.to_dict()
                if self.displacement_summary is not None
                else None
            ),
            "stress_summary": (
                self.stress_summary.to_dict() if self.stress_summary is not None else None
            ),
            "field_summaries": [field_item.to_dict() for field_item in self.field_summaries],
            "status_summary": (
                self.status_summary.to_dict() if self.status_summary is not None else None
            ),
            "log_events": [_log_event_to_dict(event) for event in self.log_events],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> CalculiXParsedResults:
        displacement = data.get("displacement_summary")
        stress = data.get("stress_summary")
        status_summary = data.get("status_summary")
        return cls(
            source_run_id=str(data.get("source_run_id", "")),
            job_name=str(data.get("job_name", "")),
            dat_path=_optional_path(data.get("dat_path")),
            frd_path=_optional_path(data.get("frd_path")),
            sta_path=_optional_path(data.get("sta_path")),
            status=CalculiXResultStatus(str(data.get("status", "unknown"))),
            displacement_summary=(
                CalculiXDisplacementSummary.from_dict(displacement)
                if isinstance(displacement, Mapping)
                else None
            ),
            stress_summary=(
                CalculiXStressSummary.from_dict(stress)
                if isinstance(stress, Mapping)
                else None
            ),
            field_summaries=tuple(
                CalculiXFieldSummary.from_dict(item)
                for item in data.get("field_summaries", ()) or ()
                if isinstance(item, Mapping)
            ),
            status_summary=(
                CalculiXStatusSummary.from_dict(status_summary)
                if isinstance(status_summary, Mapping)
                else None
            ),
            log_events=tuple(
                log_event_from_dict(item)
                for item in data.get("log_events", ()) or ()
                if isinstance(item, Mapping)
            ),
            artifacts=tuple(
                RunArtifact.from_dict(dict(item))
                for item in data.get("artifacts", ()) or ()
                if isinstance(item, Mapping)
            ),
            diagnostics=DiagnosticReport.from_dict(data.get("diagnostics", {}) or {}),
            metadata=dict(data.get("metadata", {}) or {}),
        )


def merge_parsed_results(
    *results: CalculiXParsedResults | None,
    source_run_id: str = "",
    job_name: str = "",
    metadata: Mapping[str, Any] | None = None,
) -> CalculiXParsedResults:
    """Merge summary objects from DAT, STA, FRD, and log parsers."""

    available = tuple(result for result in results if result is not None)
    diagnostics = DiagnosticReport()
    artifacts: list[RunArtifact] = []
    log_events: list[LogEvent] = []
    field_summaries: list[CalculiXFieldSummary] = []
    displacement: CalculiXDisplacementSummary | None = None
    stress: CalculiXStressSummary | None = None
    status_summary: CalculiXStatusSummary | None = None
    dat_path: Path | None = None
    frd_path: Path | None = None
    sta_path: Path | None = None
    statuses: list[CalculiXResultStatus] = []
    merged_metadata: dict[str, Any] = dict(metadata or {})
    for result in available:
        diagnostics.extend(result.diagnostics)
        artifacts.extend(result.artifacts)
        log_events.extend(result.log_events)
        field_summaries.extend(result.field_summaries)
        statuses.append(result.status)
        merged_metadata.update(result.metadata)
        displacement = displacement or result.displacement_summary
        stress = stress or result.stress_summary
        status_summary = status_summary or result.status_summary
        dat_path = dat_path or result.dat_path
        frd_path = frd_path or result.frd_path
        sta_path = sta_path or result.sta_path
    status = _merged_status(statuses, diagnostics)
    return CalculiXParsedResults(
        source_run_id=source_run_id or _first_attr(available, "source_run_id"),
        job_name=job_name or _first_attr(available, "job_name"),
        dat_path=dat_path,
        frd_path=frd_path,
        sta_path=sta_path,
        status=status,
        displacement_summary=displacement,
        stress_summary=stress,
        field_summaries=tuple(_dedupe_fields(field_summaries)),
        status_summary=status_summary,
        log_events=tuple(log_events),
        artifacts=tuple(_dedupe_artifacts(artifacts)),
        diagnostics=diagnostics,
        metadata=merged_metadata,
    )


def log_event_from_dict(data: Mapping[str, object]) -> LogEvent:
    return LogEvent(
        severity=LogSeverity(str(data.get("severity", LogSeverity.INFO.value))),
        message=str(data.get("message", "")),
        line_no=int(data.get("line_no", data.get("line_number", 0))),
        timestamp=str(data.get("timestamp", "")),
        code=str(data.get("code", "")),
        metadata=dict(data.get("metadata", {}) or {}),
    )


def _log_event_to_dict(event: LogEvent) -> dict[str, Any]:
    return {
        "severity": event.severity.value,
        "message": event.message,
        "line_no": event.line_no,
        "timestamp": event.timestamp,
        "code": event.code,
        "metadata": dict(event.metadata),
    }


def _merged_status(
    statuses: Iterable[CalculiXResultStatus],
    diagnostics: DiagnosticReport,
) -> CalculiXResultStatus:
    status_set = set(statuses)
    if not status_set:
        return CalculiXResultStatus.MISSING_ARTIFACTS
    if CalculiXResultStatus.PARSE_ERROR in status_set or diagnostics.has_errors:
        return CalculiXResultStatus.PARSE_ERROR
    if CalculiXResultStatus.PARSED in status_set and (
        CalculiXResultStatus.PARTIAL in status_set
        or CalculiXResultStatus.UNSUPPORTED in status_set
    ):
        return CalculiXResultStatus.PARTIAL
    if CalculiXResultStatus.PARSED in status_set:
        return CalculiXResultStatus.PARSED
    if CalculiXResultStatus.PARTIAL in status_set:
        return CalculiXResultStatus.PARTIAL
    if CalculiXResultStatus.UNSUPPORTED in status_set:
        return CalculiXResultStatus.PARTIAL
    if CalculiXResultStatus.MISSING_ARTIFACTS in status_set:
        return CalculiXResultStatus.MISSING_ARTIFACTS
    return CalculiXResultStatus.UNKNOWN


def _dedupe_fields(
    fields: Iterable[CalculiXFieldSummary],
) -> tuple[CalculiXFieldSummary, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[CalculiXFieldSummary] = []
    for field_item in fields:
        key = (field_item.name, field_item.location)
        if key in seen:
            continue
        seen.add(key)
        unique.append(field_item)
    return tuple(unique)


def _dedupe_artifacts(artifacts: Iterable[RunArtifact]) -> tuple[RunArtifact, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[RunArtifact] = []
    for artifact in artifacts:
        key = (str(artifact.path), artifact.role)
        if key in seen:
            continue
        seen.add(key)
        unique.append(artifact)
    return tuple(unique)


def _first_attr(results: Iterable[CalculiXParsedResults], name: str) -> str:
    for result in results:
        value = str(getattr(result, name, ""))
        if value:
            return value
    return ""


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    return float(value)


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    return int(value)


def _optional_bool(value: object) -> bool | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return value
    text = str(value).casefold()
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    return None


def _optional_path(value: object) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value))


def _float_tuple(value: object, *, length: int) -> tuple[float, ...]:
    if isinstance(value, Iterable) and not isinstance(value, str | bytes):
        items = tuple(float(item) for item in value)
    else:
        items = (float(value),)
    if len(items) >= length:
        return items[:length]
    return (*items, *(0.0 for _ in range(length - len(items))))


__all__ = [
    "CalculiXDisplacementSummary",
    "CalculiXFieldSummary",
    "CalculiXParsedResults",
    "CalculiXResultStatus",
    "CalculiXStatusSummary",
    "CalculiXStressSummary",
    "log_event_from_dict",
    "merge_parsed_results",
]
