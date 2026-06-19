"""Minimal bounded .dat parser for reviewed FEASpec CalculiX candidates."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .calculix_result_dat_section_scanner import (
    CalculiXDatSection,
    CalculiXDatSectionDirectoryScan,
    CalculiXDatSectionKind,
    CalculiXDatSectionScan,
    CalculiXDatSectionScanStatus,
    scan_calculix_dat_sections,
    scan_calculix_dat_sections_directory,
)
from .calculix_result_metadata_scanner import (
    CalculiXResultDirectoryMetadataScan,
    CalculiXResultFileMetadata,
)
from .calculix_result_parser_diagnostics import (
    CalculiXResultParserDiagnosticCode,
    CalculiXResultParserSeverity,
    FEASpecCalculiXResultParserDiagnostic,
)

__all__ = [
    "CalculiXDatMinimalParseStatus",
    "CalculiXDatMinimalParseLimits",
    "CalculiXDatScalarCandidate",
    "CalculiXDatTableCandidate",
    "CalculiXDatUnsupportedContent",
    "CalculiXDatMinimalParseResult",
    "CalculiXDatMinimalDirectoryParseResult",
    "CalculiXDatValueCell",
    "CalculiXDatUnitContext",
    "parse_calculix_dat_minimal",
    "parse_calculix_dat_directory_minimal",
    "explain_calculix_dat_minimal_parse",
]


class CalculiXDatMinimalParseStatus(str, Enum):
    """Status for the bounded minimal .dat parse slice."""

    PARSED = "parsed"
    PARSED_WITH_WARNINGS = "parsed-with-warnings"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    NO_SUPPORTED_SECTIONS = "no-supported-sections"


@dataclass(frozen=True, slots=True)
class CalculiXDatMinimalParseLimits:
    """Limits for accepting scalar and table preview candidates."""

    max_file_bytes: int = 100_000
    max_lines: int = 512
    max_scalar_candidates: int = 100
    max_table_rows: int = 25
    max_table_columns: int = 12
    max_section_lines: int = 120
    max_snippet_chars: int = 160
    max_unsupported_snippets: int = 25


@dataclass(frozen=True, slots=True)
class CalculiXDatUnitContext:
    """Explicit unit context supplied by a caller, never inferred."""

    scalar_units: Mapping[str, str] = field(default_factory=dict)
    table_column_units: Mapping[str, str] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, object] | None,
    ) -> CalculiXDatUnitContext:
        if payload is None:
            return cls()
        scalars = payload.get("scalar_units", {})
        columns = payload.get("table_column_units", {})
        return cls(
            scalar_units=_string_mapping(scalars),
            table_column_units=_string_mapping(columns),
        )

    def scalar_unit(self, label: str) -> str:
        return _lookup_unit(self.scalar_units, label)

    def table_unit(self, column: str) -> str:
        return _lookup_unit(self.table_column_units, column)

    def to_dict(self) -> dict[str, object]:
        return {
            "scalar_units": dict(self.scalar_units),
            "table_column_units": dict(self.table_column_units),
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatValueCell:
    """A raw table cell with an optional bounded numeric preview value."""

    raw: str
    value: float | None = None
    unit: str = ""
    row_number: int = 0
    column_name: str = ""
    line_number: int = 0
    parsed: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "raw": self.raw,
            "value": self.value,
            "unit": self.unit,
            "row_number": self.row_number,
            "column_name": self.column_name,
            "line_number": self.line_number,
            "parsed": self.parsed,
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatScalarCandidate:
    """Explicit scalar preview candidate from a known .dat section."""

    label: str
    raw_value: str
    value: float
    unit: str
    raw_line: str
    line_number: int
    section_heading: str
    section_kind: str
    source_path: str

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "raw_value": self.raw_value,
            "value": self.value,
            "unit": self.unit,
            "raw_line": self.raw_line,
            "line_number": self.line_number,
            "section_heading": self.section_heading,
            "section_kind": self.section_kind,
            "source_path": self.source_path,
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatTableCandidate:
    """Small explicit table preview candidate with preserved raw cells."""

    section_heading: str
    section_kind: str
    source_path: str
    header_line_number: int
    column_headers: tuple[str, ...]
    units: Mapping[str, str]
    rows: tuple[tuple[CalculiXDatValueCell, ...], ...]
    raw_lines: tuple[str, ...]
    line_start: int
    line_end: int

    @property
    def row_count(self) -> int:
        return len(self.rows)

    @property
    def column_count(self) -> int:
        return len(self.column_headers)

    @property
    def parsed_numeric_value_count(self) -> int:
        return sum(1 for row in self.rows for cell in row if cell.parsed)

    def to_dict(self) -> dict[str, object]:
        return {
            "section_heading": self.section_heading,
            "section_kind": self.section_kind,
            "source_path": self.source_path,
            "header_line_number": self.header_line_number,
            "column_headers": list(self.column_headers),
            "units": dict(self.units),
            "rows": [[cell.to_dict() for cell in row] for row in self.rows],
            "row_count": self.row_count,
            "column_count": self.column_count,
            "parsed_numeric_value_count": self.parsed_numeric_value_count,
            "raw_lines": list(self.raw_lines),
            "line_start": self.line_start,
            "line_end": self.line_end,
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatUnsupportedContent:
    """Unsupported or skipped .dat section content preserved for review."""

    section_heading: str
    section_kind: str
    source_path: str
    line_start: int
    line_end: int
    reason: str
    snippets: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "section_heading": self.section_heading,
            "section_kind": self.section_kind,
            "source_path": self.source_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "reason": self.reason,
            "snippets": list(self.snippets),
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatMinimalParseResult:
    """Minimal .dat parse result for one explicit file."""

    path: Path
    name: str
    suffix: str
    status: CalculiXDatMinimalParseStatus
    metadata: Mapping[str, Any]
    section_scan: Mapping[str, Any]
    scalar_candidates: tuple[CalculiXDatScalarCandidate, ...] = ()
    table_candidates: tuple[CalculiXDatTableCandidate, ...] = ()
    unsupported_content: tuple[CalculiXDatUnsupportedContent, ...] = ()
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = ()
    parser_phase: str = "dat-minimal-parser"
    minimal_parser: bool = True
    freeform_parser: bool = False
    frd_parser: bool = False
    units_inferred: bool = False
    writes_files: bool = False

    @property
    def scalar_count(self) -> int:
        return len(self.scalar_candidates)

    @property
    def table_count(self) -> int:
        return len(self.table_candidates)

    @property
    def parsed_numeric_value_count(self) -> int:
        return len(self.scalar_candidates) + sum(
            table.parsed_numeric_value_count for table in self.table_candidates
        )

    def summary_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "scalar_candidate_count": self.scalar_count,
            "table_candidate_count": self.table_count,
            "unsupported_content_count": len(self.unsupported_content),
            "parsed_numeric_value_count": self.parsed_numeric_value_count,
            "minimal_parser": self.minimal_parser,
            "freeform_parser": self.freeform_parser,
            "frd_parser": self.frd_parser,
            "units_inferred": self.units_inferred,
            "writes_files": self.writes_files,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "name": self.name,
            "suffix": self.suffix,
            "status": self.status.value,
            "metadata": dict(self.metadata),
            "section_scan": dict(self.section_scan),
            "scalar_candidates": [item.to_dict() for item in self.scalar_candidates],
            "table_candidates": [item.to_dict() for item in self.table_candidates],
            "unsupported_content": [
                item.to_dict() for item in self.unsupported_content
            ],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "summary": self.summary_dict(),
            "parser_phase": self.parser_phase,
            "minimal_parser": self.minimal_parser,
            "freeform_parser": self.freeform_parser,
            "frd_parser": self.frd_parser,
            "units_inferred": self.units_inferred,
            "writes_files": self.writes_files,
        }


@dataclass(frozen=True, slots=True)
class CalculiXDatMinimalDirectoryParseResult:
    """Minimal parser result for direct .dat files in a directory."""

    result_dir: Path
    exists: bool
    is_directory: bool
    status: CalculiXDatMinimalParseStatus
    files: tuple[CalculiXDatMinimalParseResult, ...] = ()
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = ()
    recursive: bool = False
    writes_files: bool = False

    @property
    def scalar_count(self) -> int:
        return sum(item.scalar_count for item in self.files)

    @property
    def table_count(self) -> int:
        return sum(item.table_count for item in self.files)

    @property
    def parsed_numeric_value_count(self) -> int:
        return sum(item.parsed_numeric_value_count for item in self.files)

    def summary_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "file_count": len(self.files),
            "scalar_candidate_count": self.scalar_count,
            "table_candidate_count": self.table_count,
            "parsed_numeric_value_count": self.parsed_numeric_value_count,
            "writes_files": self.writes_files,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "result_dir": str(self.result_dir),
            "exists": self.exists,
            "is_directory": self.is_directory,
            "status": self.status.value,
            "files": [item.to_dict() for item in self.files],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "recursive": self.recursive,
            "writes_files": self.writes_files,
            "summary": self.summary_dict(),
        }


_SCALAR_RE = re.compile(
    r"^\s*(?P<label>[A-Za-z][A-Za-z0-9_ .()/+-]{0,96})\s*(?:=|:)\s*"
    r"(?P<value>\S+)(?:\s+(?P<unit>[^\s#]+))?\s*(?:#.*)?$"
)
_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?$")


def parse_calculix_dat_minimal(
    path: str | Path,
    *,
    section_scan: CalculiXDatSectionScan | None = None,
    metadata: CalculiXResultFileMetadata | None = None,
    unit_context: CalculiXDatUnitContext | Mapping[str, object] | None = None,
    limits: CalculiXDatMinimalParseLimits | None = None,
) -> CalculiXDatMinimalParseResult:
    """Parse the smallest supported .dat scalar/table candidate subset."""

    resolved_limits = limits or CalculiXDatMinimalParseLimits()
    context = _resolve_unit_context(unit_context)
    target = Path(path).expanduser()
    suffix = target.suffix.lower()
    if suffix != ".dat":
        diagnostic = _diag(
            CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT,
            ".dat minimal parser accepts explicit .dat files only.",
            path=str(target),
        )
        return _result(
            path=target,
            suffix=suffix,
            status=CalculiXDatMinimalParseStatus.UNSUPPORTED,
            diagnostics=(diagnostic,),
        )

    scan = section_scan or scan_calculix_dat_sections(
        target,
        metadata=metadata,
    )
    diagnostics = list(scan.diagnostics)
    diagnostics.extend(
        [
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_PARSE_MINIMAL_ONLY,
                "Minimal .dat parser accepts only bounded scalar/table candidates.",
                path=str(target),
                severity=CalculiXResultParserSeverity.INFO,
            ),
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_UNIT_INFERENCE_FORBIDDEN,
                "Units must be explicit; unit inference is not performed.",
                path=str(target),
                severity=CalculiXResultParserSeverity.INFO,
            ),
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_RAW_TEXT_PRESERVED,
                "Raw .dat text snippets and line provenance are preserved.",
                path=str(target),
                severity=CalculiXResultParserSeverity.INFO,
            ),
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_RESULT_DATASET_WRITE_FORBIDDEN,
                "ResultDataset persistence is forbidden in this parser gate.",
                path=str(target),
                severity=CalculiXResultParserSeverity.INFO,
            ),
        ]
    )
    if scan.status in {
        CalculiXDatSectionScanStatus.BLOCKED,
        CalculiXDatSectionScanStatus.UNSUPPORTED,
    }:
        return _result(
            path=target,
            suffix=suffix,
            status=CalculiXDatMinimalParseStatus.BLOCKED,
            metadata=scan.metadata,
            section_scan=scan.to_dict(),
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    text, read_diagnostics = _read_text(target)
    diagnostics.extend(read_diagnostics)
    if read_diagnostics:
        return _result(
            path=target,
            suffix=suffix,
            status=CalculiXDatMinimalParseStatus.BLOCKED,
            metadata=scan.metadata,
            section_scan=scan.to_dict(),
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    lines = tuple(text.splitlines())
    scalars: list[CalculiXDatScalarCandidate] = []
    tables: list[CalculiXDatTableCandidate] = []
    unsupported: list[CalculiXDatUnsupportedContent] = []
    partial = False

    for section in scan.sections:
        section_lines = _lines_for_section(lines, section, resolved_limits)
        if section.kind is CalculiXDatSectionKind.UNSUPPORTED:
            unsupported.append(_unsupported(section, target, "unsupported section"))
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_UNSUPPORTED_SECTION_SKIPPED,
                    f"Unsupported .dat section skipped: {section.heading_text}",
                    path=str(target),
                )
            )
            continue
        if section.kind is CalculiXDatSectionKind.UNKNOWN:
            unsupported.append(_unsupported(section, target, "unknown section"))
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_UNKNOWN_TABLE_SKIPPED,
                    f"Unknown .dat section skipped: {section.heading_text}",
                    path=str(target),
                )
            )
            continue
        if section.kind is CalculiXDatSectionKind.SCALAR_CANDIDATE:
            scalar_count_before = len(scalars)
            scalar_partial = _parse_scalar_section(
                section,
                section_lines,
                target,
                context,
                resolved_limits,
                scalars,
                diagnostics,
            )
            partial = partial or scalar_partial
            if len(scalars) == scalar_count_before:
                unsupported.append(_unsupported(section, target, "no supported scalar"))
            continue
        if section.kind in _TABLE_SECTION_KINDS:
            table = _parse_table_section(
                section,
                section_lines,
                target,
                context,
                resolved_limits,
                diagnostics,
            )
            if table is None:
                scalar_count_before = len(scalars)
                scalar_partial = _parse_scalar_section(
                    section,
                    section_lines,
                    target,
                    context,
                    resolved_limits,
                    scalars,
                    diagnostics,
                )
                partial = partial or scalar_partial
                if len(scalars) == scalar_count_before:
                    unsupported.append(_unsupported(section, target, "no supported table"))
            else:
                tables.append(table)
            partial = partial or _has_limit_diagnostic(diagnostics)

    status = _parse_status(scalars, tables, diagnostics, partial)
    return _result(
        path=target,
        suffix=suffix,
        status=status,
        metadata=scan.metadata,
        section_scan=scan.to_dict(),
        scalar_candidates=tuple(scalars),
        table_candidates=tuple(tables),
        unsupported_content=tuple(unsupported[: resolved_limits.max_unsupported_snippets]),
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def parse_calculix_dat_directory_minimal(
    result_dir: str | Path,
    *,
    section_directory_scan: CalculiXDatSectionDirectoryScan | None = None,
    metadata_scan: CalculiXResultDirectoryMetadataScan | None = None,
    unit_context: CalculiXDatUnitContext | Mapping[str, object] | None = None,
    limits: CalculiXDatMinimalParseLimits | None = None,
) -> CalculiXDatMinimalDirectoryParseResult:
    """Parse direct .dat files in a directory without recursion or writes."""

    resolved_limits = limits or CalculiXDatMinimalParseLimits()
    context = _resolve_unit_context(unit_context)
    root = Path(result_dir).expanduser()
    if not root.exists():
        diagnostic = _diag(
            CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
            "Result directory does not exist.",
            path=str(root),
            severity=CalculiXResultParserSeverity.BLOCKER,
            blocks_parse=True,
        )
        return CalculiXDatMinimalDirectoryParseResult(
            result_dir=root,
            exists=False,
            is_directory=False,
            status=CalculiXDatMinimalParseStatus.BLOCKED,
            diagnostics=(diagnostic,),
        )
    if not root.is_dir():
        diagnostic = _diag(
            CalculiXResultParserDiagnosticCode.FP_PATH_NOT_FILE,
            "Result path exists but is not a directory.",
            path=str(root),
            severity=CalculiXResultParserSeverity.BLOCKER,
            blocks_parse=True,
        )
        return CalculiXDatMinimalDirectoryParseResult(
            result_dir=root,
            exists=True,
            is_directory=False,
            status=CalculiXDatMinimalParseStatus.BLOCKED,
            diagnostics=(diagnostic,),
        )

    section_scan = section_directory_scan or scan_calculix_dat_sections_directory(
        root,
        metadata_scan=metadata_scan,
    )
    section_by_path = {item.path: item for item in section_scan.files}
    files = tuple(
        parse_calculix_dat_minimal(
            child,
            section_scan=section_by_path.get(child),
            unit_context=context,
            limits=resolved_limits,
        )
        for child in sorted(
            (item for item in root.iterdir() if item.is_file() and item.suffix.lower() == ".dat"),
            key=lambda item: item.name,
        )
    )
    diagnostics = tuple(
        _dedupe_diagnostics(
            [diagnostic for item in files for diagnostic in item.diagnostics]
        )
    )
    return CalculiXDatMinimalDirectoryParseResult(
        result_dir=root,
        exists=True,
        is_directory=True,
        status=_directory_status(files, diagnostics),
        files=files,
        diagnostics=diagnostics,
    )


def explain_calculix_dat_minimal_parse(
    result: CalculiXDatMinimalParseResult | CalculiXDatMinimalDirectoryParseResult,
) -> list[str]:
    """Return reviewer-readable parse status lines."""

    if isinstance(result, CalculiXDatMinimalDirectoryParseResult):
        lines = [
            f"CalculiX .dat minimal directory parse: {result.status.value}.",
            f"Directory: {result.result_dir}.",
            f".dat files parsed: {len(result.files)}.",
            f"Scalar candidates: {result.scalar_count}.",
            f"Table candidates: {result.table_count}.",
            "Writes files: false.",
        ]
    else:
        lines = [
            f"CalculiX .dat minimal parse: {result.status.value}.",
            f"File: {result.path}.",
            f"Scalar candidates: {result.scalar_count}.",
            f"Table candidates: {result.table_count}.",
            "Free-form parser: false.",
            "Units inferred: false.",
            "Writes files: false.",
        ]
    for diagnostic in result.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


_TABLE_SECTION_KINDS = {
    CalculiXDatSectionKind.TABLE_CANDIDATE,
    CalculiXDatSectionKind.DISPLACEMENT_CANDIDATE,
    CalculiXDatSectionKind.STRESS_CANDIDATE,
    CalculiXDatSectionKind.NODE_OUTPUT_CANDIDATE,
    CalculiXDatSectionKind.ELEMENT_OUTPUT_CANDIDATE,
}


def _parse_scalar_section(
    section: CalculiXDatSection,
    section_lines: Sequence[tuple[int, str]],
    path: Path,
    unit_context: CalculiXDatUnitContext,
    limits: CalculiXDatMinimalParseLimits,
    scalars: list[CalculiXDatScalarCandidate],
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic],
) -> bool:
    partial = False
    for line_number, raw_line in section_lines:
        if len(scalars) >= limits.max_scalar_candidates:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_SCALAR_LIMIT_EXCEEDED,
                    ".dat scalar candidate limit exceeded.",
                    path=str(path),
                )
            )
            return True
        match = _SCALAR_RE.match(raw_line)
        if match is None:
            if _has_numeric_token(raw_line):
                diagnostics.append(
                    _diag(
                        CalculiXResultParserDiagnosticCode.FP_DAT_AMBIGUOUS_VALUE_SKIPPED,
                        "Ambiguous scalar-like .dat line was skipped.",
                        path=str(path),
                    )
                )
            continue
        label = _clean_label(match.group("label"))
        raw_value = match.group("value")
        unit = str(match.group("unit") or "").strip()
        if not unit:
            unit = unit_context.scalar_unit(label)
        if not unit:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_UNITS_MISSING,
                    f"Scalar candidate lacks explicit unit context: {label}",
                    path=str(path),
                )
            )
            continue
        try:
            value = float(raw_value)
        except ValueError:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_DAT_NUMERIC_CONVERSION_FAILED,
                    f"Scalar candidate value could not be parsed: {label}",
                    path=str(path),
                )
            )
            continue
        scalars.append(
            CalculiXDatScalarCandidate(
                label=label,
                raw_value=raw_value,
                value=value,
                unit=unit,
                raw_line=raw_line,
                line_number=line_number,
                section_heading=section.heading_text,
                section_kind=section.kind.value,
                source_path=str(path),
            )
        )
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_SCALAR_CANDIDATE_PARSED,
                f"Scalar candidate parsed with explicit unit: {label}",
                path=str(path),
                severity=CalculiXResultParserSeverity.INFO,
            )
        )
    return partial


def _parse_table_section(
    section: CalculiXDatSection,
    section_lines: Sequence[tuple[int, str]],
    path: Path,
    unit_context: CalculiXDatUnitContext,
    limits: CalculiXDatMinimalParseLimits,
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic],
) -> CalculiXDatTableCandidate | None:
    body = [(number, text) for number, text in section_lines[1:] if text.strip()]
    if not body:
        return None
    header_number, header_line = body[0]
    delimiter = _detect_delimiter(header_line)
    if delimiter == "":
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_UNKNOWN_TABLE_SKIPPED,
                f"Table candidate lacks an explicit delimiter: {section.heading_text}",
                path=str(path),
            )
        )
        return None
    headers = _split_delimited(header_line, delimiter)
    if len(headers) < 2:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_UNKNOWN_TABLE_SKIPPED,
                f"Table candidate lacks multiple columns: {section.heading_text}",
                path=str(path),
            )
        )
        return None
    if len(headers) > limits.max_table_columns:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_COLUMN_LIMIT_EXCEEDED,
                ".dat table candidate column limit exceeded.",
                path=str(path),
            )
        )
        headers = headers[: limits.max_table_columns]

    units: dict[str, str] = {}
    row_start = 1
    if len(body) > 1:
        unit_cells = _split_delimited(body[1][1], delimiter)
        if unit_cells and unit_cells[0].strip().lower() in {"unit", "units"}:
            row_start = 2
            aligned_unit_cells = unit_cells[1:]
            for header, unit in zip(headers, aligned_unit_cells, strict=False):
                unit = unit.strip()
                if unit and unit.lower() not in {"-", "none"}:
                    units[header] = unit
    for header in headers:
        context_unit = unit_context.table_unit(header)
        if context_unit and header not in units:
            units[header] = context_unit

    data_lines = body[row_start:]
    if len(data_lines) > limits.max_table_rows:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_ROW_LIMIT_EXCEEDED,
                ".dat table candidate row limit exceeded.",
                path=str(path),
            )
        )
        data_lines = data_lines[: limits.max_table_rows]

    rows: list[tuple[CalculiXDatValueCell, ...]] = []
    missing_unit_columns: set[str] = set()
    conversion_failed = False
    for row_number, (line_number, line) in enumerate(data_lines, start=1):
        raw_cells = _split_delimited(line, delimiter)[: len(headers)]
        if len(raw_cells) < len(headers):
            raw_cells = raw_cells + [""] * (len(headers) - len(raw_cells))
        cells: list[CalculiXDatValueCell] = []
        for header, raw in zip(headers, raw_cells, strict=False):
            raw = raw.strip()
            unit = units.get(header, "")
            parsed = False
            value: float | None = None
            if _is_identifier_column(header):
                cells.append(
                    CalculiXDatValueCell(
                        raw=raw,
                        unit="",
                        row_number=row_number,
                        column_name=header,
                        line_number=line_number,
                    )
                )
                continue
            if _NUMBER_RE.match(raw):
                if not unit:
                    missing_unit_columns.add(header)
                else:
                    try:
                        value = float(raw)
                        parsed = True
                    except ValueError:
                        conversion_failed = True
            cells.append(
                CalculiXDatValueCell(
                    raw=raw,
                    value=value,
                    unit=unit,
                    row_number=row_number,
                    column_name=header,
                    line_number=line_number,
                    parsed=parsed,
                )
            )
        rows.append(tuple(cells))

    for column in sorted(missing_unit_columns):
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_UNITS_MISSING,
                f"Table numeric column lacks explicit unit context: {column}",
                path=str(path),
            )
        )
    if conversion_failed:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_DAT_NUMERIC_CONVERSION_FAILED,
                f"Table candidate had malformed numeric text: {section.heading_text}",
                path=str(path),
            )
        )
    table = CalculiXDatTableCandidate(
        section_heading=section.heading_text,
        section_kind=section.kind.value,
        source_path=str(path),
        header_line_number=header_number,
        column_headers=tuple(headers),
        units=units,
        rows=tuple(rows),
        raw_lines=tuple(text for _, text in body[: row_start + len(rows)]),
        line_start=section.line_start,
        line_end=section.line_end,
    )
    diagnostics.append(
        _diag(
            CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_CANDIDATE_PARSED,
            f"Table candidate parsed with explicit boundaries: {section.heading_text}",
            path=str(path),
            severity=CalculiXResultParserSeverity.INFO,
        )
    )
    return table


def _lines_for_section(
    lines: Sequence[str],
    section: CalculiXDatSection,
    limits: CalculiXDatMinimalParseLimits,
) -> tuple[tuple[int, str], ...]:
    start = max(1, section.line_start)
    end = min(len(lines), section.line_end, start + limits.max_section_lines - 1)
    return tuple((number, lines[number - 1]) for number in range(start, end + 1))


def _unsupported(
    section: CalculiXDatSection,
    path: Path,
    reason: str,
) -> CalculiXDatUnsupportedContent:
    return CalculiXDatUnsupportedContent(
        section_heading=section.heading_text,
        section_kind=section.kind.value,
        source_path=str(path),
        line_start=section.line_start,
        line_end=section.line_end,
        reason=reason,
        snippets=section.snippets,
    )


def _detect_delimiter(line: str) -> str:
    if "|" in line:
        return "|"
    if "," in line:
        return ","
    return ""


def _split_delimited(line: str, delimiter: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip(delimiter).split(delimiter)]


def _is_identifier_column(header: str) -> bool:
    return _normalize_key(header) in {"id", "node", "element", "label", "name"}


def _has_numeric_token(line: str) -> bool:
    return any(_NUMBER_RE.match(token.strip("(),;")) for token in line.split())


def _clean_label(label: str) -> str:
    return " ".join(label.strip().split())


def _lookup_unit(mapping: Mapping[str, str], key: str) -> str:
    if key in mapping:
        return mapping[key]
    normalized = _normalize_key(key)
    for candidate, unit in mapping.items():
        if _normalize_key(candidate) == normalized:
            return unit
    return ""


def _normalize_key(value: str) -> str:
    return "".join(char.lower() for char in value if char.isalnum() or char == "_")


def _string_mapping(payload: object) -> Mapping[str, str]:
    if not isinstance(payload, Mapping):
        return {}
    return {
        str(key): str(value)
        for key, value in payload.items()
        if key not in (None, "") and value not in (None, "")
    }


def _resolve_unit_context(
    unit_context: CalculiXDatUnitContext | Mapping[str, object] | None,
) -> CalculiXDatUnitContext:
    if isinstance(unit_context, CalculiXDatUnitContext):
        return unit_context
    return CalculiXDatUnitContext.from_mapping(unit_context)


def _read_text(
    path: Path,
) -> tuple[str, list[FEASpecCalculiXResultParserDiagnostic]]:
    try:
        return path.read_text(encoding="utf-8"), []
    except OSError as exc:
        return "", [
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
                f"Unable to read .dat artifact: {exc}",
                path=str(path),
                severity=CalculiXResultParserSeverity.BLOCKER,
                blocks_parse=True,
            )
        ]
    except UnicodeDecodeError as exc:
        return "", [
            _diag(
                CalculiXResultParserDiagnosticCode.FP_ENCODING_UNSUPPORTED,
                f"Unable to decode .dat artifact as UTF-8: {exc}",
                path=str(path),
                severity=CalculiXResultParserSeverity.ERROR,
                blocks_parse=True,
            )
        ]


def _parse_status(
    scalars: Sequence[CalculiXDatScalarCandidate],
    tables: Sequence[CalculiXDatTableCandidate],
    diagnostics: Sequence[FEASpecCalculiXResultParserDiagnostic],
    partial: bool,
) -> CalculiXDatMinimalParseStatus:
    if any(diagnostic.blocks_parse for diagnostic in diagnostics):
        return CalculiXDatMinimalParseStatus.BLOCKED
    if partial or _has_limit_diagnostic(diagnostics):
        return CalculiXDatMinimalParseStatus.PARTIAL
    if not scalars and not tables:
        return CalculiXDatMinimalParseStatus.NO_SUPPORTED_SECTIONS
    if any(
        diagnostic.severity
        in {CalculiXResultParserSeverity.WARNING, CalculiXResultParserSeverity.ERROR}
        for diagnostic in diagnostics
    ):
        return CalculiXDatMinimalParseStatus.PARSED_WITH_WARNINGS
    return CalculiXDatMinimalParseStatus.PARSED


def _directory_status(
    files: Sequence[CalculiXDatMinimalParseResult],
    diagnostics: Sequence[FEASpecCalculiXResultParserDiagnostic],
) -> CalculiXDatMinimalParseStatus:
    if any(item.status is CalculiXDatMinimalParseStatus.BLOCKED for item in files):
        return CalculiXDatMinimalParseStatus.BLOCKED
    if not files:
        return CalculiXDatMinimalParseStatus.NO_SUPPORTED_SECTIONS
    if any(item.status is CalculiXDatMinimalParseStatus.PARTIAL for item in files):
        return CalculiXDatMinimalParseStatus.PARTIAL
    if any(
        item.status is CalculiXDatMinimalParseStatus.PARSED_WITH_WARNINGS
        for item in files
    ) or any(
        diagnostic.severity
        in {CalculiXResultParserSeverity.WARNING, CalculiXResultParserSeverity.ERROR}
        for diagnostic in diagnostics
    ):
        return CalculiXDatMinimalParseStatus.PARSED_WITH_WARNINGS
    if any(item.status is CalculiXDatMinimalParseStatus.PARSED for item in files):
        return CalculiXDatMinimalParseStatus.PARSED
    return CalculiXDatMinimalParseStatus.NO_SUPPORTED_SECTIONS


def _has_limit_diagnostic(
    diagnostics: Sequence[FEASpecCalculiXResultParserDiagnostic],
) -> bool:
    return any(
        diagnostic.code
        in {
            CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_ROW_LIMIT_EXCEEDED,
            CalculiXResultParserDiagnosticCode.FP_DAT_TABLE_COLUMN_LIMIT_EXCEEDED,
            CalculiXResultParserDiagnosticCode.FP_DAT_SCALAR_LIMIT_EXCEEDED,
        }
        for diagnostic in diagnostics
    )


def _result(
    *,
    path: Path,
    suffix: str,
    status: CalculiXDatMinimalParseStatus,
    metadata: Mapping[str, Any] | None = None,
    section_scan: Mapping[str, Any] | None = None,
    scalar_candidates: tuple[CalculiXDatScalarCandidate, ...] = (),
    table_candidates: tuple[CalculiXDatTableCandidate, ...] = (),
    unsupported_content: tuple[CalculiXDatUnsupportedContent, ...] = (),
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = (),
) -> CalculiXDatMinimalParseResult:
    return CalculiXDatMinimalParseResult(
        path=path,
        name=path.name,
        suffix=suffix,
        status=status,
        metadata=dict(metadata or {}),
        section_scan=dict(section_scan or {}),
        scalar_candidates=scalar_candidates,
        table_candidates=table_candidates,
        unsupported_content=unsupported_content,
        diagnostics=diagnostics,
    )


def _diag(
    code: CalculiXResultParserDiagnosticCode,
    message: str,
    *,
    path: str,
    severity: CalculiXResultParserSeverity = CalculiXResultParserSeverity.WARNING,
    blocks_parse: bool = False,
) -> FEASpecCalculiXResultParserDiagnostic:
    return FEASpecCalculiXResultParserDiagnostic.make(
        code,
        severity,
        message,
        path=path,
        artifact_kind="dat",
        blocks_parse=blocks_parse,
        blocks_import=False,
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
