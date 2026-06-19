"""Text-only .dat metadata section scanner for FEASpec CalculiX artifacts."""

from __future__ import annotations

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
    "CalculiXDatSectionKind",
    "CalculiXDatSection",
    "CalculiXDatSectionSummary",
    "CalculiXDatSectionScan",
    "CalculiXDatSectionDirectoryScan",
    "CalculiXDatSectionScanStatus",
    "CalculiXDatSectionScanLimits",
    "scan_calculix_dat_sections",
    "scan_calculix_dat_sections_directory",
    "explain_calculix_dat_section_scan",
]


class CalculiXDatSectionScanStatus(str, Enum):
    """Status for a text-only .dat section scan."""

    SCANNED = "scanned"
    SCANNED_WITH_WARNINGS = "scanned-with-warnings"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    METADATA_ONLY = "metadata-only"


class CalculiXDatSectionKind(str, Enum):
    """Conservative section categories recognized in .dat text."""

    HEADER = "header"
    SOLVER_MESSAGE = "solver_message"
    SCALAR_CANDIDATE = "scalar_candidate"
    TABLE_CANDIDATE = "table_candidate"
    DISPLACEMENT_CANDIDATE = "displacement_candidate"
    STRESS_CANDIDATE = "stress_candidate"
    NODE_OUTPUT_CANDIDATE = "node_output_candidate"
    ELEMENT_OUTPUT_CANDIDATE = "element_output_candidate"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CalculiXDatSectionScanLimits:
    """Limits used by the .dat metadata section scanner."""

    max_file_bytes: int = 100_000
    max_lines: int = 512
    max_snippet_chars: int = 160
    max_sections: int = 64
    max_section_lines: int = 120
    max_section_snippets: int = 4
    max_unknown_sections: int = 8


@dataclass(frozen=True, slots=True)
class CalculiXDatSection:
    """A bounded .dat section record with no extracted values."""

    heading_text: str
    kind: CalculiXDatSectionKind
    heading_line_number: int
    line_start: int
    line_end: int
    snippets: tuple[str, ...] = ()
    unsupported: bool = False
    numeric_tokens_present: bool = False

    @property
    def line_count(self) -> int:
        return max(0, self.line_end - self.line_start + 1)

    def to_dict(self) -> dict[str, object]:
        return {
            "heading_text": self.heading_text,
            "kind": self.kind.value,
            "heading_line_number": self.heading_line_number,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "line_count": self.line_count,
            "snippets": list(self.snippets),
            "unsupported": self.unsupported,
            "numeric_tokens_present": self.numeric_tokens_present,
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatSectionSummary:
    """Summary of .dat section metadata, not parsed result data."""

    kind_counts: Mapping[CalculiXDatSectionKind, int] = field(default_factory=dict)
    section_count: int = 0
    recognized_section_count: int = 0
    unknown_section_count: int = 0
    unsupported_section_count: int = 0
    numeric_tokens_not_parsed: bool = False
    limitations: tuple[str, ...] = (
        ".dat section scanner only; no numerical result parsing is performed.",
        "Numeric-looking tokens remain text snippets and are not parsed.",
        "Table-like sections are only marked as candidates; rows and columns are not extracted.",
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "kind_counts": {key.value: value for key, value in self.kind_counts.items()},
            "section_count": self.section_count,
            "recognized_section_count": self.recognized_section_count,
            "unknown_section_count": self.unknown_section_count,
            "unsupported_section_count": self.unsupported_section_count,
            "numeric_tokens_not_parsed": self.numeric_tokens_not_parsed,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatSectionScan:
    """Text-only .dat section scan for one explicit file."""

    path: Path
    name: str
    suffix: str
    artifact_kind: str
    status: CalculiXDatSectionScanStatus
    metadata: Mapping[str, Any]
    line_count: int
    processed_line_count: int
    line_count_truncated: bool
    summary: CalculiXDatSectionSummary
    sections: tuple[CalculiXDatSection, ...]
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = ()
    parser_phase: str = "dat-section-scan-only"
    numerical_values_parsed: bool = False
    numeric_values_extracted: bool = False
    tables_extracted: bool = False
    units_inferred: bool = False
    writes_files: bool = False

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
            "sections": [section.to_dict() for section in self.sections],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "parser_phase": self.parser_phase,
            "numerical_values_parsed": self.numerical_values_parsed,
            "numeric_values_extracted": self.numeric_values_extracted,
            "tables_extracted": self.tables_extracted,
            "units_inferred": self.units_inferred,
            "writes_files": self.writes_files,
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatSectionDirectoryScan:
    """Directory-level .dat section scan for immediate files only."""

    result_dir: Path
    exists: bool
    is_directory: bool
    status: CalculiXDatSectionScanStatus
    files: tuple[CalculiXDatSectionScan, ...] = ()
    summary: CalculiXDatSectionSummary = field(default_factory=CalculiXDatSectionSummary)
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


def scan_calculix_dat_sections(
    path: str | Path,
    *,
    metadata: CalculiXResultFileMetadata | None = None,
    limits: CalculiXDatSectionScanLimits | None = None,
) -> CalculiXDatSectionScan:
    """Scan one explicit .dat file for bounded section metadata only."""

    resolved_limits = limits or CalculiXDatSectionScanLimits()
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
    artifact_kind = metadata_scan.artifact_kind or ("dat" if suffix == ".dat" else "other")

    if suffix != ".dat":
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT,
                ".dat section scanner accepts explicit .dat files only.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXDatSectionScanStatus.UNSUPPORTED,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    if metadata_scan.status is CalculiXResultMetadataStatus.BLOCKED:
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXDatSectionScanStatus.BLOCKED,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    if metadata_scan.byte_size > resolved_limits.max_file_bytes:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_TOO_LARGE,
                ".dat file exceeded the section scanner byte limit.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXDatSectionScanStatus.METADATA_ONLY,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    text, read_diagnostics = _read_text(target, artifact_kind)
    diagnostics.extend(read_diagnostics)
    raw_lines = tuple(text.splitlines()) if text else ()
    processed_lines = raw_lines[: resolved_limits.max_lines]
    line_count_truncated = len(raw_lines) > len(processed_lines)
    sections, summary, scan_diagnostics = _scan_sections(
        processed_lines,
        path=target,
        artifact_kind=artifact_kind,
        limits=resolved_limits,
    )
    diagnostics.extend(scan_diagnostics)

    if line_count_truncated:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_LINE_LIMIT_EXCEEDED,
                ".dat section scan line limit was reached; summary is partial.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )

    status = (
        CalculiXDatSectionScanStatus.SCANNED
        if not diagnostics
        else CalculiXDatSectionScanStatus.SCANNED_WITH_WARNINGS
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
        sections=tuple(sections),
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def scan_calculix_dat_sections_directory(
    result_dir: str | Path,
    *,
    metadata_scan: CalculiXResultDirectoryMetadataScan | None = None,
    limits: CalculiXDatSectionScanLimits | None = None,
) -> CalculiXDatSectionDirectoryScan:
    """Scan direct .dat files in an explicit directory without recursion."""

    resolved_limits = limits or CalculiXDatSectionScanLimits()
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
        return CalculiXDatSectionDirectoryScan(
            result_dir=root,
            exists=False,
            is_directory=False,
            status=CalculiXDatSectionScanStatus.BLOCKED,
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
        return CalculiXDatSectionDirectoryScan(
            result_dir=root,
            exists=True,
            is_directory=False,
            status=CalculiXDatSectionScanStatus.BLOCKED,
            diagnostics=tuple(diagnostics),
        )

    metadata_by_path = _metadata_by_path(metadata_scan)
    scans = tuple(
        scan_calculix_dat_sections(
            child,
            metadata=metadata_by_path.get(child),
            limits=resolved_limits,
        )
        for child in sorted(
            (item for item in root.iterdir() if item.is_file() and item.suffix.lower() == ".dat"),
            key=lambda item: item.name,
        )
    )
    diagnostics.extend(item for scan in scans for item in scan.diagnostics)
    summary = _merge_summaries(tuple(scan.summary for scan in scans))
    status = _directory_status(scans, diagnostics)
    return CalculiXDatSectionDirectoryScan(
        result_dir=root,
        exists=True,
        is_directory=True,
        status=status,
        files=scans,
        summary=summary,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def explain_calculix_dat_section_scan(
    scan: CalculiXDatSectionScan | CalculiXDatSectionDirectoryScan,
) -> list[str]:
    """Return a reviewer-readable explanation of a .dat section scan."""

    if isinstance(scan, CalculiXDatSectionDirectoryScan):
        lines = [
            f"CalculiX .dat section directory scan: {scan.status.value}.",
            f"Directory: {scan.result_dir}.",
            f".dat files scanned: {len(scan.files)}.",
            "Numerical values parsed: false.",
            "Tables extracted: false.",
            "Solver execution performed: false.",
        ]
    else:
        lines = [
            f"CalculiX .dat section file scan: {scan.status.value}.",
            f"File: {scan.path}.",
            f"Sections scanned: {len(scan.sections)}.",
            "Numerical values parsed: false.",
            "Tables extracted: false.",
            "Solver execution performed: false.",
        ]
    counts = {key.value: value for key, value in scan.summary.kind_counts.items()}
    if counts:
        lines.append(f"Section kind counts: {counts}.")
    for diagnostic in scan.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


def _scan_sections(
    lines: Sequence[str],
    *,
    path: Path,
    artifact_kind: str,
    limits: CalculiXDatSectionScanLimits,
) -> tuple[
    list[CalculiXDatSection],
    CalculiXDatSectionSummary,
    list[FEASpecCalculiXResultParserDiagnostic],
]:
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic] = [
        _diag(
            CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_SCAN_ONLY,
            ".dat scan is section metadata only; values and tables are not extracted.",
            path=str(path),
            artifact_kind=artifact_kind,
            severity=CalculiXResultParserSeverity.INFO,
        )
    ]
    headings = [
        (index, text, kind)
        for index, text in enumerate(lines, start=1)
        if (kind := _classify_heading(text)) is not None
    ]
    if not headings:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_NO_RECOGNIZED_SECTIONS,
                "No recognized .dat section headings were found.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )
        return [], CalculiXDatSectionSummary(), diagnostics

    retained_headings = headings[: limits.max_sections]
    if len(headings) > len(retained_headings):
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_TOO_LARGE,
                ".dat section count exceeded scanner retention limits.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )

    sections: list[CalculiXDatSection] = []
    unknown_retained = 0
    for position, (line_number, heading, kind) in enumerate(retained_headings):
        if (
            kind is CalculiXDatSectionKind.UNKNOWN
            and unknown_retained >= limits.max_unknown_sections
        ):
            continue
        if kind is CalculiXDatSectionKind.UNKNOWN:
            unknown_retained += 1
        next_start = (
            retained_headings[position + 1][0]
            if position + 1 < len(retained_headings)
            else len(lines) + 1
        )
        natural_end = max(line_number, next_start - 1)
        bounded_end = min(natural_end, line_number + limits.max_section_lines - 1)
        if bounded_end < natural_end:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_TOO_LARGE,
                    ".dat section line span exceeded scanner limits.",
                    path=str(path),
                    artifact_kind=artifact_kind,
                )
            )
        section_lines = lines[line_number - 1 : bounded_end]
        numeric_tokens_present = any(_has_digit(item) for item in section_lines)
        snippets = tuple(
            _trim_snippet(item, limits.max_snippet_chars)
            for item in section_lines[: limits.max_section_snippets]
        )
        unsupported = kind is CalculiXDatSectionKind.UNSUPPORTED
        sections.append(
            CalculiXDatSection(
                heading_text=_trim_snippet(heading.strip(), limits.max_snippet_chars),
                kind=kind,
                heading_line_number=line_number,
                line_start=line_number,
                line_end=bounded_end,
                snippets=snippets,
                unsupported=unsupported,
                numeric_tokens_present=numeric_tokens_present,
            )
        )
        if unsupported:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_SECTION_HEADING_UNSUPPORTED,
                    f"Unsupported .dat section heading was preserved: {heading.strip()}",
                    path=str(path),
                    artifact_kind=artifact_kind,
                )
            )
        if kind is CalculiXDatSectionKind.UNKNOWN:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_UNKNOWN_SECTION,
                    f"Unknown .dat section heading was preserved: {heading.strip()}",
                    path=str(path),
                    artifact_kind=artifact_kind,
                )
            )
        if kind is CalculiXDatSectionKind.TABLE_CANDIDATE:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_CANDIDATE_UNPARSED,
                    ".dat table candidate was identified but rows and columns were not extracted.",
                    path=str(path),
                    artifact_kind=artifact_kind,
                    severity=CalculiXResultParserSeverity.INFO,
                )
            )

    if any(section.numeric_tokens_present for section in sections):
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_NUMERIC_VALUES_NOT_PARSED,
                "Numeric-looking tokens were kept as snippets and not parsed as values.",
                path=str(path),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.INFO,
            )
        )

    summary = _summary_from_sections(sections)
    return sections, summary, diagnostics


def _classify_heading(text: str) -> CalculiXDatSectionKind | None:
    stripped = text.strip()
    if not stripped:
        return None
    lowered = stripped.lower()
    heading_like = _looks_like_heading(stripped)

    if any(
        token in lowered
        for token in ("contact", "plastic", "nonlinear", "frequency", "buckling")
    ):
        return CalculiXDatSectionKind.UNSUPPORTED
    if any(token in lowered for token in ("displacement", "displacements")):
        return CalculiXDatSectionKind.DISPLACEMENT_CANDIDATE
    if any(token in lowered for token in ("stress", "stresses", "von mises")):
        return CalculiXDatSectionKind.STRESS_CANDIDATE
    if "node" in lowered and ("output" in lowered or "print" in lowered or "results" in lowered):
        return CalculiXDatSectionKind.NODE_OUTPUT_CANDIDATE
    if "element" in lowered and ("output" in lowered or "print" in lowered or "results" in lowered):
        return CalculiXDatSectionKind.ELEMENT_OUTPUT_CANDIDATE
    if heading_like and any(token in lowered for token in ("table", "row", "column")):
        return CalculiXDatSectionKind.TABLE_CANDIDATE
    if any(
        token in lowered
        for token in ("scalar", "summary", "maximum", "minimum", "total")
    ):
        return CalculiXDatSectionKind.SCALAR_CANDIDATE
    if any(token in lowered for token in ("warning", "error", "message", "solver", "iteration")):
        return CalculiXDatSectionKind.SOLVER_MESSAGE
    if any(token in lowered for token in ("calculix", "date", "version", "job")):
        return CalculiXDatSectionKind.HEADER
    if heading_like:
        return CalculiXDatSectionKind.UNKNOWN
    return None


def _looks_like_heading(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 3:
        return False
    if stripped.endswith(":"):
        return True
    letters = [char for char in stripped if char.isalpha()]
    if letters and all(char.isupper() for char in letters) and len(letters) >= 4:
        return True
    return stripped.startswith(("--", "==")) and len(stripped) <= 120


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
                f"Unable to read .dat artifact: {exc}",
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
                "UTF-8 decode failed; using replacement text for .dat section scan.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )
        return raw.decode("utf-8", errors="replace"), diagnostics


def _summary_from_sections(
    sections: Sequence[CalculiXDatSection],
) -> CalculiXDatSectionSummary:
    counts: Counter[CalculiXDatSectionKind] = Counter(section.kind for section in sections)
    unknown = counts[CalculiXDatSectionKind.UNKNOWN]
    unsupported = counts[CalculiXDatSectionKind.UNSUPPORTED]
    return CalculiXDatSectionSummary(
        kind_counts=dict(counts),
        section_count=len(sections),
        recognized_section_count=max(0, len(sections) - unknown),
        unknown_section_count=unknown,
        unsupported_section_count=unsupported,
        numeric_tokens_not_parsed=any(section.numeric_tokens_present for section in sections),
    )


def _merge_summaries(
    summaries: Sequence[CalculiXDatSectionSummary],
) -> CalculiXDatSectionSummary:
    counts: Counter[CalculiXDatSectionKind] = Counter()
    section_count = 0
    recognized = 0
    unknown = 0
    unsupported = 0
    numeric_tokens = False
    for summary in summaries:
        counts.update(summary.kind_counts)
        section_count += summary.section_count
        recognized += summary.recognized_section_count
        unknown += summary.unknown_section_count
        unsupported += summary.unsupported_section_count
        numeric_tokens = numeric_tokens or summary.numeric_tokens_not_parsed
    return CalculiXDatSectionSummary(
        kind_counts=dict(counts),
        section_count=section_count,
        recognized_section_count=recognized,
        unknown_section_count=unknown,
        unsupported_section_count=unsupported,
        numeric_tokens_not_parsed=numeric_tokens,
    )


def _metadata_by_path(
    metadata_scan: CalculiXResultDirectoryMetadataScan | None,
) -> Mapping[Path, CalculiXResultFileMetadata]:
    if metadata_scan is None:
        return {}
    return {item.path: item for item in metadata_scan.artifacts}


def _directory_status(
    scans: Sequence[CalculiXDatSectionScan],
    diagnostics: Sequence[FEASpecCalculiXResultParserDiagnostic],
) -> CalculiXDatSectionScanStatus:
    if any(scan.status is CalculiXDatSectionScanStatus.BLOCKED for scan in scans):
        return CalculiXDatSectionScanStatus.BLOCKED
    if not scans:
        return CalculiXDatSectionScanStatus.UNSUPPORTED
    if any(scan.status is CalculiXDatSectionScanStatus.METADATA_ONLY for scan in scans):
        return CalculiXDatSectionScanStatus.METADATA_ONLY
    if diagnostics or any(
        scan.status is CalculiXDatSectionScanStatus.SCANNED_WITH_WARNINGS
        for scan in scans
    ):
        return CalculiXDatSectionScanStatus.SCANNED_WITH_WARNINGS
    return CalculiXDatSectionScanStatus.SCANNED


def _file_scan(
    *,
    path: Path,
    suffix: str,
    artifact_kind: str,
    status: CalculiXDatSectionScanStatus,
    metadata: Mapping[str, Any],
    line_count: int = 0,
    processed_line_count: int = 0,
    line_count_truncated: bool = False,
    summary: CalculiXDatSectionSummary | None = None,
    sections: tuple[CalculiXDatSection, ...] = (),
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = (),
) -> CalculiXDatSectionScan:
    return CalculiXDatSectionScan(
        path=path,
        name=path.name,
        suffix=suffix,
        artifact_kind=artifact_kind,
        status=status,
        metadata=dict(metadata),
        line_count=line_count,
        processed_line_count=processed_line_count,
        line_count_truncated=line_count_truncated,
        summary=summary or CalculiXDatSectionSummary(),
        sections=sections,
        diagnostics=diagnostics,
    )


def _has_digit(text: str) -> bool:
    return any(char.isdigit() for char in text)


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
