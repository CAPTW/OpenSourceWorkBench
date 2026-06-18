"""Text-only status scanner for FEASpec CalculiX .sta and .cvg artifacts."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .calculix_result_metadata_scanner import (
    CalculiXResultDirectoryMetadataScan,
    CalculiXResultFileMetadata,
    CalculiXResultMetadataLimits,
    CalculiXResultMetadataStatus,
    scan_calculix_result_file_metadata,
)
from .calculix_result_parser_diagnostics import (
    CalculiXResultParserDiagnosticCode,
    CalculiXResultParserSeverity,
    FEASpecCalculiXResultParserDiagnostic,
)

__all__ = [
    "CalculiXStatusLineCategory",
    "CalculiXStatusLine",
    "CalculiXStatusSummary",
    "CalculiXStatusFileScan",
    "CalculiXStatusDirectoryScan",
    "CalculiXStatusScanStatus",
    "CalculiXStatusScanLimits",
    "scan_calculix_status_file",
    "scan_calculix_status_directory",
    "explain_calculix_status_scan",
]

SUPPORTED_STATUS_SUFFIXES = frozenset({".sta", ".cvg"})
_NUMERIC_TOKEN_RE = re.compile(
    r"(?<![A-Za-z])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
)


class CalculiXStatusScanStatus(str, Enum):
    """Status for a text-only CalculiX status scan."""

    SCANNED = "scanned"
    SCANNED_WITH_WARNINGS = "scanned-with-warnings"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    METADATA_ONLY = "metadata-only"


class CalculiXStatusLineCategory(str, Enum):
    """Text categories recognized in .sta and .cvg status files."""

    PROGRESS = "progress"
    CONVERGENCE = "convergence"
    WARNING = "warning"
    ERROR = "error"
    COMPLETION = "completion"
    FAILURE = "failure"
    INFORMATIONAL = "informational"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CalculiXStatusScanLimits:
    """Limits used by the text-only status scanner."""

    max_file_bytes: int = 100_000
    max_lines: int = 256
    max_snippet_chars: int = 160
    max_matched_lines: int = 64
    max_unknown_lines: int = 8


@dataclass(frozen=True, slots=True)
class CalculiXStatusLine:
    """A bounded status-line snippet from a .sta or .cvg file."""

    line_number: int
    category: CalculiXStatusLineCategory
    snippet: str
    raw_text_snippet: str
    numeric_tokens_present: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "line_number": self.line_number,
            "category": self.category.value,
            "snippet": self.snippet,
            "raw_text_snippet": self.raw_text_snippet,
            "numeric_tokens_present": self.numeric_tokens_present,
        }


@dataclass(frozen=True, slots=True)
class CalculiXStatusSummary:
    """Text-only summary of status indicators, not numerical convergence data."""

    category_counts: Mapping[CalculiXStatusLineCategory, int] = field(
        default_factory=dict
    )
    recognized_line_count: int = 0
    unknown_line_count: int = 0
    warning_count: int = 0
    error_count: int = 0
    completion_indicated: bool = False
    failure_indicated: bool = False
    numeric_tokens_not_parsed: bool = False
    limitations: tuple[str, ...] = (
        "Text status scanner only; no numerical result parsing is performed.",
        "Numeric convergence tokens remain text snippets and are not parsed.",
        "Completion and failure indicators are textual hints, not correctness claims.",
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "category_counts": {
                key.value: value for key, value in self.category_counts.items()
            },
            "recognized_line_count": self.recognized_line_count,
            "unknown_line_count": self.unknown_line_count,
            "warning_count": self.warning_count,
            "error_count": self.error_count,
            "completion_indicated": self.completion_indicated,
            "failure_indicated": self.failure_indicated,
            "numeric_tokens_not_parsed": self.numeric_tokens_not_parsed,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class CalculiXStatusFileScan:
    """Text-only status scan for one explicit .sta or .cvg file."""

    path: Path
    name: str
    suffix: str
    artifact_kind: str
    status: CalculiXStatusScanStatus
    metadata: Mapping[str, Any]
    line_count: int
    processed_line_count: int
    line_count_truncated: bool
    summary: CalculiXStatusSummary
    lines: tuple[CalculiXStatusLine, ...]
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = ()
    parser_phase: str = "status-text-only"
    numerical_values_parsed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "name": self.name,
            "suffix": self.suffix,
            "artifact_kind": self.artifact_kind,
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "line_count": self.line_count,
            "processed_line_count": self.processed_line_count,
            "line_count_truncated": self.line_count_truncated,
            "summary": self.summary.to_dict(),
            "lines": [line.to_dict() for line in self.lines],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "parser_phase": self.parser_phase,
            "numerical_values_parsed": self.numerical_values_parsed,
        }


@dataclass(frozen=True, slots=True)
class CalculiXStatusDirectoryScan:
    """Directory-level status scan for immediate .sta and .cvg files only."""

    result_dir: Path
    exists: bool
    is_directory: bool
    status: CalculiXStatusScanStatus
    files: tuple[CalculiXStatusFileScan, ...] = ()
    summary: CalculiXStatusSummary = field(default_factory=CalculiXStatusSummary)
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = ()
    recursive: bool = False
    writes_files: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "result_dir": str(self.result_dir),
            "exists": self.exists,
            "is_directory": self.is_directory,
            "status": self.status.value,
            "files": [item.to_dict() for item in self.files],
            "file_count": len(self.files),
            "summary": self.summary.to_dict(),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "recursive": self.recursive,
            "writes_files": self.writes_files,
        }


def scan_calculix_status_file(
    path: str | Path,
    *,
    metadata: CalculiXResultFileMetadata | None = None,
    limits: CalculiXStatusScanLimits | None = None,
) -> CalculiXStatusFileScan:
    """Scan one explicit .sta or .cvg file for bounded text status indicators."""

    resolved_limits = limits or CalculiXStatusScanLimits()
    target = Path(path).expanduser()
    suffix = target.suffix.lower()
    metadata_scan = metadata or scan_calculix_result_file_metadata(
        target,
        limits=CalculiXResultMetadataLimits(
            max_file_bytes=resolved_limits.max_file_bytes,
            max_lines=resolved_limits.max_lines,
            max_snippet_chars=resolved_limits.max_snippet_chars,
        ),
    )
    metadata_payload = metadata_scan.to_dict()
    diagnostics = list(metadata_scan.diagnostics)
    artifact_kind = _metadata_artifact_kind(metadata_scan, suffix=suffix)

    if suffix not in SUPPORTED_STATUS_SUFFIXES:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT,
                "Status scanner accepts explicit .sta and .cvg files only.",
                path=str(target),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.WARNING,
            )
        )
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXStatusScanStatus.UNSUPPORTED,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    if metadata_scan.status is CalculiXResultMetadataStatus.BLOCKED:
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXStatusScanStatus.BLOCKED,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    if metadata_scan.byte_size > resolved_limits.max_file_bytes:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_STATUS_PARTIAL_SUMMARY,
                "Status file exceeded the status scanner byte limit.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXStatusScanStatus.METADATA_ONLY,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    text, read_diagnostics = _read_text(target, artifact_kind)
    diagnostics.extend(read_diagnostics)
    raw_lines = tuple(text.splitlines()) if text else ()
    processed_lines = raw_lines[: resolved_limits.max_lines]
    line_count_truncated = len(raw_lines) > len(processed_lines)
    retained_lines, summary, scan_diagnostics = _scan_lines(
        processed_lines,
        path=target,
        artifact_kind=artifact_kind,
        limits=resolved_limits,
    )
    diagnostics.extend(scan_diagnostics)

    if line_count_truncated:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_LINE_LIMIT_EXCEEDED,
                "Status scan line limit was reached; summary is partial.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_STATUS_PARTIAL_SUMMARY,
                "Only a bounded prefix of status lines was scanned.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )

    status = (
        CalculiXStatusScanStatus.SCANNED
        if not diagnostics
        else CalculiXStatusScanStatus.SCANNED_WITH_WARNINGS
    )
    return _file_scan(
        path=target,
        suffix=suffix,
        artifact_kind=artifact_kind,
        status=status,
        metadata=metadata_payload,
        line_count=len(raw_lines),
        processed_line_count=len(processed_lines),
        line_count_truncated=line_count_truncated,
        summary=summary,
        lines=tuple(retained_lines),
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def scan_calculix_status_directory(
    result_dir: str | Path,
    *,
    metadata_scan: CalculiXResultDirectoryMetadataScan | None = None,
    limits: CalculiXStatusScanLimits | None = None,
) -> CalculiXStatusDirectoryScan:
    """Scan direct .sta and .cvg files in an explicit directory without writes."""

    resolved_limits = limits or CalculiXStatusScanLimits()
    root = Path(result_dir).expanduser()
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic] = []

    if not root.exists():
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
                "Result directory does not exist.",
                path=str(root),
                artifact_kind="directory",
                severity=CalculiXResultParserSeverity.BLOCKER,
                blocks_parse=True,
            )
        )
        return CalculiXStatusDirectoryScan(
            result_dir=root,
            exists=False,
            is_directory=False,
            status=CalculiXStatusScanStatus.BLOCKED,
            diagnostics=tuple(diagnostics),
        )

    if not root.is_dir():
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_PATH_NOT_FILE,
                "Result path exists but is not a directory.",
                path=str(root),
                artifact_kind="directory",
                severity=CalculiXResultParserSeverity.BLOCKER,
                blocks_parse=True,
            )
        )
        return CalculiXStatusDirectoryScan(
            result_dir=root,
            exists=True,
            is_directory=False,
            status=CalculiXStatusScanStatus.BLOCKED,
            diagnostics=tuple(diagnostics),
        )

    metadata_by_path = _metadata_by_path(metadata_scan)
    scans = tuple(
        scan_calculix_status_file(
            child,
            metadata=metadata_by_path.get(child),
            limits=resolved_limits,
        )
        for child in sorted(
            (
                item
                for item in root.iterdir()
                if item.is_file() and item.suffix.lower() in SUPPORTED_STATUS_SUFFIXES
            ),
            key=lambda item: item.name,
        )
    )
    diagnostics.extend(item for scan in scans for item in scan.diagnostics)
    summary = _merge_summaries(tuple(scan.summary for scan in scans))
    status = _directory_status(scans, diagnostics)
    return CalculiXStatusDirectoryScan(
        result_dir=root,
        exists=True,
        is_directory=True,
        status=status,
        files=scans,
        summary=summary,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def explain_calculix_status_scan(
    scan: CalculiXStatusFileScan | CalculiXStatusDirectoryScan,
) -> list[str]:
    """Return a reviewer-readable explanation of a text status scan."""

    if isinstance(scan, CalculiXStatusDirectoryScan):
        lines = [
            f"CalculiX status directory scan: {scan.status.value}.",
            f"Directory: {scan.result_dir}.",
            f"Status files scanned: {len(scan.files)}.",
            "Numerical convergence values parsed: false.",
            "Solver execution performed: false.",
        ]
    else:
        lines = [
            f"CalculiX status file scan: {scan.status.value}.",
            f"File: {scan.path}.",
            f"Artifact kind: {scan.artifact_kind}.",
            "Numerical convergence values parsed: false.",
            "Solver execution performed: false.",
        ]
    counts = {
        key.value: value for key, value in scan.summary.category_counts.items()
    }
    if counts:
        lines.append(f"Category counts: {counts}.")
    for diagnostic in scan.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


def _scan_lines(
    lines: Sequence[str],
    *,
    path: Path,
    artifact_kind: str,
    limits: CalculiXStatusScanLimits,
) -> tuple[
    list[CalculiXStatusLine],
    CalculiXStatusSummary,
    list[FEASpecCalculiXResultParserDiagnostic],
]:
    retained: list[CalculiXStatusLine] = []
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic] = [
        _diag(
            CalculiXResultParserDiagnosticCode.FP_STATUS_SCAN_ONLY,
            "Status scan is text-only; numerical values are not parsed.",
            path=str(path),
            artifact_kind=artifact_kind,
            severity=CalculiXResultParserSeverity.INFO,
        )
    ]
    category_counts: Counter[CalculiXStatusLineCategory] = Counter()
    recognized_count = 0
    unknown_count = 0
    retained_matched = 0
    retained_unknown = 0
    numeric_tokens_not_parsed = False

    for line_number, text in enumerate(lines, start=1):
        category = _classify_status_line(text)
        category_counts[category] += 1
        numeric_tokens_present = bool(_NUMERIC_TOKEN_RE.search(text))
        if (
            category
            in {
                CalculiXStatusLineCategory.CONVERGENCE,
                CalculiXStatusLineCategory.PROGRESS,
            }
            and numeric_tokens_present
        ):
            numeric_tokens_not_parsed = True
        if category is CalculiXStatusLineCategory.UNKNOWN:
            unknown_count += 1
            if retained_unknown >= limits.max_unknown_lines:
                continue
            retained_unknown += 1
        else:
            recognized_count += 1
            if retained_matched >= limits.max_matched_lines:
                continue
            retained_matched += 1
        retained.append(
            CalculiXStatusLine(
                line_number=line_number,
                category=category,
                snippet=_trim_snippet(text, limits.max_snippet_chars),
                raw_text_snippet=_trim_snippet(text, limits.max_snippet_chars),
                numeric_tokens_present=numeric_tokens_present,
            )
        )

    if recognized_count == 0:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_STATUS_NO_RECOGNIZED_LINES,
                "No recognized status, progress, convergence, warning, or error lines.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )
    if numeric_tokens_not_parsed:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_STATUS_NUMERIC_VALUES_NOT_PARSED,
                "Numeric-looking tokens were kept as text and not parsed as values.",
                path=str(path),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.INFO,
            )
        )
    if retained_matched < recognized_count or retained_unknown < unknown_count:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_STATUS_PARTIAL_SUMMARY,
                "Status line snippets were bounded by retention limits.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )

    summary = CalculiXStatusSummary(
        category_counts=dict(category_counts),
        recognized_line_count=recognized_count,
        unknown_line_count=unknown_count,
        warning_count=category_counts[CalculiXStatusLineCategory.WARNING],
        error_count=category_counts[CalculiXStatusLineCategory.ERROR],
        completion_indicated=category_counts[
            CalculiXStatusLineCategory.COMPLETION
        ]
        > 0,
        failure_indicated=category_counts[CalculiXStatusLineCategory.FAILURE] > 0,
        numeric_tokens_not_parsed=numeric_tokens_not_parsed,
    )
    return retained, summary, diagnostics


def _classify_status_line(text: str) -> CalculiXStatusLineCategory:
    lowered = text.lower()
    if not lowered.strip():
        return CalculiXStatusLineCategory.UNKNOWN
    if any(token in lowered for token in ("fatal", "error")):
        return CalculiXStatusLineCategory.ERROR
    if any(
        token in lowered
        for token in (
            "not converged",
            "diverg",
            "failed",
            "failure",
            "aborted",
            "error termination",
            "no convergence",
        )
    ):
        return CalculiXStatusLineCategory.FAILURE
    if any(token in lowered for token in ("warning", "caution")):
        return CalculiXStatusLineCategory.WARNING
    if any(
        token in lowered
        for token in (
            "completed",
            "complete",
            "successfully",
            "normal termination",
            "finished",
            "end of analysis",
        )
    ):
        return CalculiXStatusLineCategory.COMPLETION
    if any(
        token in lowered
        for token in (
            "converg",
            "residual",
            "equilibrium",
            "contact iteration",
            "cutback",
        )
    ):
        return CalculiXStatusLineCategory.CONVERGENCE
    if any(
        token in lowered
        for token in (
            "increment",
            "iteration",
            "step",
            "cycle",
            "time",
            "percentage",
            "progress",
        )
    ):
        return CalculiXStatusLineCategory.PROGRESS
    if any(
        token in lowered
        for token in (
            "calculix",
            "reading",
            "writing",
            "started",
            "start",
            "analysis",
            "job",
            "solver",
        )
    ):
        return CalculiXStatusLineCategory.INFORMATIONAL
    return CalculiXStatusLineCategory.UNKNOWN


def _read_text(
    path: Path,
    artifact_kind: str,
) -> tuple[str, list[FEASpecCalculiXResultParserDiagnostic]]:
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic] = []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
                f"Unable to read status artifact: {exc}",
                path=str(path),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.ERROR,
                blocks_parse=True,
            )
        )
        return "", diagnostics

    try:
        return raw.decode("utf-8"), diagnostics
    except UnicodeDecodeError:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_ENCODING_UNSUPPORTED,
                "UTF-8 decode failed; using replacement text for status scan.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )
        return raw.decode("utf-8", errors="replace"), diagnostics


def _metadata_artifact_kind(
    metadata: CalculiXResultFileMetadata,
    *,
    suffix: str,
) -> str:
    if metadata.artifact_kind:
        return metadata.artifact_kind
    if suffix == ".sta":
        return "sta"
    if suffix == ".cvg":
        return "cvg"
    return "other"


def _metadata_by_path(
    metadata_scan: CalculiXResultDirectoryMetadataScan | None,
) -> Mapping[Path, CalculiXResultFileMetadata]:
    if metadata_scan is None:
        return {}
    return {item.path: item for item in metadata_scan.artifacts}


def _merge_summaries(
    summaries: Sequence[CalculiXStatusSummary],
) -> CalculiXStatusSummary:
    counts: Counter[CalculiXStatusLineCategory] = Counter()
    recognized = 0
    unknown = 0
    warnings = 0
    errors = 0
    completion = False
    failure = False
    numeric_tokens = False
    for summary in summaries:
        counts.update(summary.category_counts)
        recognized += summary.recognized_line_count
        unknown += summary.unknown_line_count
        warnings += summary.warning_count
        errors += summary.error_count
        completion = completion or summary.completion_indicated
        failure = failure or summary.failure_indicated
        numeric_tokens = numeric_tokens or summary.numeric_tokens_not_parsed
    return CalculiXStatusSummary(
        category_counts=dict(counts),
        recognized_line_count=recognized,
        unknown_line_count=unknown,
        warning_count=warnings,
        error_count=errors,
        completion_indicated=completion,
        failure_indicated=failure,
        numeric_tokens_not_parsed=numeric_tokens,
    )


def _directory_status(
    scans: Sequence[CalculiXStatusFileScan],
    diagnostics: Sequence[FEASpecCalculiXResultParserDiagnostic],
) -> CalculiXStatusScanStatus:
    if any(scan.status is CalculiXStatusScanStatus.BLOCKED for scan in scans):
        return CalculiXStatusScanStatus.BLOCKED
    if not scans:
        return CalculiXStatusScanStatus.UNSUPPORTED
    if any(scan.status is CalculiXStatusScanStatus.METADATA_ONLY for scan in scans):
        return CalculiXStatusScanStatus.METADATA_ONLY
    if diagnostics or any(
        scan.status is CalculiXStatusScanStatus.SCANNED_WITH_WARNINGS
        for scan in scans
    ):
        return CalculiXStatusScanStatus.SCANNED_WITH_WARNINGS
    return CalculiXStatusScanStatus.SCANNED


def _file_scan(
    *,
    path: Path,
    suffix: str,
    artifact_kind: str,
    status: CalculiXStatusScanStatus,
    metadata: Mapping[str, Any],
    line_count: int = 0,
    processed_line_count: int = 0,
    line_count_truncated: bool = False,
    summary: CalculiXStatusSummary | None = None,
    lines: tuple[CalculiXStatusLine, ...] = (),
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = (),
) -> CalculiXStatusFileScan:
    return CalculiXStatusFileScan(
        path=path,
        name=path.name,
        suffix=suffix,
        artifact_kind=artifact_kind,
        status=status,
        metadata=dict(metadata),
        line_count=line_count,
        processed_line_count=processed_line_count,
        line_count_truncated=line_count_truncated,
        summary=summary or CalculiXStatusSummary(),
        lines=lines,
        diagnostics=diagnostics,
    )


def _trim_snippet(text: str, max_chars: int) -> str:
    if max_chars <= 0:
        return ""
    return text if len(text) <= max_chars else text[:max_chars]


def _diag(
    code: CalculiXResultParserDiagnosticCode,
    message: str,
    *,
    path: str,
    artifact_kind: str,
    severity: CalculiXResultParserSeverity = CalculiXResultParserSeverity.WARNING,
    blocks_parse: bool = False,
    blocks_import: bool = False,
) -> FEASpecCalculiXResultParserDiagnostic:
    return FEASpecCalculiXResultParserDiagnostic.make(
        code,
        severity,
        message,
        path=path,
        artifact_kind=artifact_kind,
        blocks_parse=blocks_parse,
        blocks_import=blocks_import,
    )


def _dedupe_diagnostics(
    diagnostics: Sequence[FEASpecCalculiXResultParserDiagnostic],
) -> list[FEASpecCalculiXResultParserDiagnostic]:
    seen: set[tuple[CalculiXResultParserDiagnosticCode, str, str]] = set()
    unique: list[FEASpecCalculiXResultParserDiagnostic] = []
    for diagnostic in diagnostics:
        key = (diagnostic.code, diagnostic.path, diagnostic.message)
        if key not in seen:
            seen.add(key)
            unique.append(diagnostic)
    return unique
