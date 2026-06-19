"""Text-only .frd block metadata scanner for FEASpec CalculiX artifacts."""

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
    "CalculiXFrdBlockKind",
    "CalculiXFrdBlock",
    "CalculiXFrdReferenceCandidate",
    "CalculiXFrdBlockSummary",
    "CalculiXFrdBlockScan",
    "CalculiXFrdBlockDirectoryScan",
    "CalculiXFrdBlockScanStatus",
    "CalculiXFrdBlockScanLimits",
    "scan_calculix_frd_blocks",
    "scan_calculix_frd_blocks_directory",
    "explain_calculix_frd_block_scan",
]


class CalculiXFrdBlockScanStatus(str, Enum):
    """Status for a text-only .frd block scan."""

    SCANNED = "scanned"
    SCANNED_WITH_WARNINGS = "scanned-with-warnings"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    METADATA_ONLY = "metadata-only"


class CalculiXFrdBlockKind(str, Enum):
    """Conservative block categories recognized in .frd text."""

    HEADER = "header"
    MESH_REFERENCE_CANDIDATE = "mesh_reference_candidate"
    NODE_REFERENCE_CANDIDATE = "node_reference_candidate"
    ELEMENT_REFERENCE_CANDIDATE = "element_reference_candidate"
    FIELD_REFERENCE_CANDIDATE = "field_reference_candidate"
    RESULT_BLOCK_CANDIDATE = "result_block_candidate"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CalculiXFrdBlockScanLimits:
    """Limits used by the .frd block metadata scanner."""

    max_file_bytes: int = 200_000
    max_lines: int = 1024
    max_snippet_chars: int = 160
    max_blocks: int = 96
    max_block_lines: int = 160
    max_block_snippets: int = 4
    max_unknown_blocks: int = 12
    max_reference_candidates: int = 96


@dataclass(frozen=True, slots=True)
class CalculiXFrdBlock:
    """A bounded .frd block record with no field values or topology."""

    label: str
    kind: CalculiXFrdBlockKind
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
            "label": self.label,
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
class CalculiXFrdReferenceCandidate:
    """A deferred .frd reference candidate without parsed arrays."""

    reference_kind: str
    label: str
    block_kind: CalculiXFrdBlockKind
    block_index: int
    line_number: int
    source_path: str
    snippet: str = ""
    values_parsed: bool = False
    mesh_reconstructed: bool = False
    units_inferred: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "reference_kind": self.reference_kind,
            "label": self.label,
            "block_kind": self.block_kind.value,
            "block_index": self.block_index,
            "line_number": self.line_number,
            "source_path": self.source_path,
            "snippet": self.snippet,
            "values_parsed": self.values_parsed,
            "mesh_reconstructed": self.mesh_reconstructed,
            "units_inferred": self.units_inferred,
        }


@dataclass(frozen=True, slots=True)
class CalculiXFrdBlockSummary:
    """Summary of .frd block metadata, not numerical field data."""

    kind_counts: Mapping[CalculiXFrdBlockKind, int] = field(default_factory=dict)
    reference_kind_counts: Mapping[str, int] = field(default_factory=dict)
    block_count: int = 0
    recognized_block_count: int = 0
    unknown_block_count: int = 0
    unsupported_block_count: int = 0
    reference_candidate_count: int = 0
    field_reference_candidate_count: int = 0
    mesh_reference_candidate_count: int = 0
    numeric_tokens_not_parsed: bool = False
    limitations: tuple[str, ...] = (
        ".frd block scanner only; numerical field values are not parsed.",
        "Node and element records remain deferred references; mesh is not reconstructed.",
        "Units are not inferred from .frd text.",
    )

    def to_dict(self) -> dict[str, object]:
        return {
            "kind_counts": {key.value: value for key, value in self.kind_counts.items()},
            "reference_kind_counts": dict(self.reference_kind_counts),
            "block_count": self.block_count,
            "recognized_block_count": self.recognized_block_count,
            "unknown_block_count": self.unknown_block_count,
            "unsupported_block_count": self.unsupported_block_count,
            "reference_candidate_count": self.reference_candidate_count,
            "field_reference_candidate_count": self.field_reference_candidate_count,
            "mesh_reference_candidate_count": self.mesh_reference_candidate_count,
            "numeric_tokens_not_parsed": self.numeric_tokens_not_parsed,
            "limitations": list(self.limitations),
        }


@dataclass(frozen=True, slots=True)
class CalculiXFrdBlockScan:
    """Text-only .frd block scan for one explicit file."""

    path: Path
    name: str
    suffix: str
    artifact_kind: str
    status: CalculiXFrdBlockScanStatus
    metadata: Mapping[str, Any]
    line_count: int
    processed_line_count: int
    line_count_truncated: bool
    summary: CalculiXFrdBlockSummary
    blocks: tuple[CalculiXFrdBlock, ...]
    reference_candidates: tuple[CalculiXFrdReferenceCandidate, ...] = ()
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = ()
    parser_phase: str = "frd-block-scan-only"
    numerical_values_parsed: bool = False
    field_values_parsed: bool = False
    numeric_values_extracted: bool = False
    mesh_reconstructed: bool = False
    visualization_arrays_built: bool = False
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
            "blocks": [block.to_dict() for block in self.blocks],
            "reference_candidates": [
                candidate.to_dict() for candidate in self.reference_candidates
            ],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "parser_phase": self.parser_phase,
            "numerical_values_parsed": self.numerical_values_parsed,
            "field_values_parsed": self.field_values_parsed,
            "numeric_values_extracted": self.numeric_values_extracted,
            "mesh_reconstructed": self.mesh_reconstructed,
            "visualization_arrays_built": self.visualization_arrays_built,
            "units_inferred": self.units_inferred,
            "writes_files": self.writes_files,
        }


@dataclass(frozen=True, slots=True)
class CalculiXFrdBlockDirectoryScan:
    """Directory-level .frd block scan for immediate files only."""

    result_dir: Path
    exists: bool
    is_directory: bool
    status: CalculiXFrdBlockScanStatus
    files: tuple[CalculiXFrdBlockScan, ...] = ()
    summary: CalculiXFrdBlockSummary = field(default_factory=CalculiXFrdBlockSummary)
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


def scan_calculix_frd_blocks(
    path: str | Path,
    *,
    metadata: CalculiXResultFileMetadata | None = None,
    limits: CalculiXFrdBlockScanLimits | None = None,
) -> CalculiXFrdBlockScan:
    """Scan one explicit .frd file for bounded block metadata only."""

    resolved_limits = limits or CalculiXFrdBlockScanLimits()
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
    artifact_kind = metadata_scan.artifact_kind or ("frd" if suffix == ".frd" else "other")

    if suffix != ".frd":
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT,
                ".frd block scanner accepts explicit .frd files only.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXFrdBlockScanStatus.UNSUPPORTED,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    if metadata_scan.status is CalculiXResultMetadataStatus.BLOCKED:
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXFrdBlockScanStatus.BLOCKED,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    if metadata_scan.byte_size > resolved_limits.max_file_bytes:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_TOO_LARGE,
                ".frd file exceeded the block scanner byte limit.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXFrdBlockScanStatus.METADATA_ONLY,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    text, binary_unsupported, read_diagnostics = _read_text(target, artifact_kind)
    diagnostics.extend(read_diagnostics)
    if binary_unsupported:
        return _file_scan(
            path=target,
            suffix=suffix,
            artifact_kind=artifact_kind,
            status=CalculiXFrdBlockScanStatus.UNSUPPORTED,
            metadata=metadata_payload,
            diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
        )

    raw_lines = tuple(text.splitlines()) if text else ()
    processed_lines = raw_lines[: resolved_limits.max_lines]
    line_count_truncated = len(raw_lines) > len(processed_lines)
    blocks, references, summary, scan_diagnostics = _scan_blocks(
        processed_lines,
        path=target,
        artifact_kind=artifact_kind,
        limits=resolved_limits,
    )
    diagnostics.extend(scan_diagnostics)

    if line_count_truncated:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_LIMIT_EXCEEDED,
                ".frd block scan line limit was reached; summary is partial.",
                path=str(target),
                artifact_kind=artifact_kind,
            )
        )

    status = (
        CalculiXFrdBlockScanStatus.SCANNED
        if not diagnostics
        else CalculiXFrdBlockScanStatus.SCANNED_WITH_WARNINGS
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
        blocks=tuple(blocks),
        reference_candidates=tuple(references),
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def scan_calculix_frd_blocks_directory(
    result_dir: str | Path,
    *,
    metadata_scan: CalculiXResultDirectoryMetadataScan | None = None,
    limits: CalculiXFrdBlockScanLimits | None = None,
) -> CalculiXFrdBlockDirectoryScan:
    """Scan direct .frd files in an explicit directory without recursion."""

    resolved_limits = limits or CalculiXFrdBlockScanLimits()
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
        return CalculiXFrdBlockDirectoryScan(
            result_dir=root,
            exists=False,
            is_directory=False,
            status=CalculiXFrdBlockScanStatus.BLOCKED,
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
        return CalculiXFrdBlockDirectoryScan(
            result_dir=root,
            exists=True,
            is_directory=False,
            status=CalculiXFrdBlockScanStatus.BLOCKED,
            diagnostics=tuple(diagnostics),
        )

    metadata_by_path = _metadata_by_path(metadata_scan)
    scans = tuple(
        scan_calculix_frd_blocks(
            child,
            metadata=metadata_by_path.get(child),
            limits=resolved_limits,
        )
        for child in sorted(
            (item for item in root.iterdir() if item.is_file() and item.suffix.lower() == ".frd"),
            key=lambda item: item.name,
        )
    )
    diagnostics.extend(item for scan in scans for item in scan.diagnostics)
    summary = _merge_summaries(tuple(scan.summary for scan in scans))
    status = _directory_status(scans, diagnostics)
    return CalculiXFrdBlockDirectoryScan(
        result_dir=root,
        exists=True,
        is_directory=True,
        status=status,
        files=scans,
        summary=summary,
        diagnostics=tuple(_dedupe_diagnostics(diagnostics)),
    )


def explain_calculix_frd_block_scan(
    scan: CalculiXFrdBlockScan | CalculiXFrdBlockDirectoryScan,
) -> list[str]:
    """Return a reviewer-readable explanation of a .frd block scan."""

    if isinstance(scan, CalculiXFrdBlockDirectoryScan):
        lines = [
            f"CalculiX .frd block directory scan: {scan.status.value}.",
            f"Directory: {scan.result_dir}.",
            f".frd files scanned: {len(scan.files)}.",
            "Numerical field values parsed: false.",
            "Mesh reconstructed: false.",
            "Solver execution performed: false.",
        ]
    else:
        lines = [
            f"CalculiX .frd block file scan: {scan.status.value}.",
            f"File: {scan.path}.",
            f"Blocks scanned: {len(scan.blocks)}.",
            "Numerical field values parsed: false.",
            "Mesh reconstructed: false.",
            "Solver execution performed: false.",
        ]
    counts = {key.value: value for key, value in scan.summary.kind_counts.items()}
    if counts:
        lines.append(f"Block kind counts: {counts}.")
    for diagnostic in scan.diagnostics:
        path = f" [{diagnostic.path}]" if diagnostic.path else ""
        lines.append(
            f"{diagnostic.severity.value.upper()} {diagnostic.code.value}{path}: "
            f"{diagnostic.message}"
        )
    return lines


def _scan_blocks(
    lines: Sequence[str],
    *,
    path: Path,
    artifact_kind: str,
    limits: CalculiXFrdBlockScanLimits,
) -> tuple[
    list[CalculiXFrdBlock],
    list[CalculiXFrdReferenceCandidate],
    CalculiXFrdBlockSummary,
    list[FEASpecCalculiXResultParserDiagnostic],
]:
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic] = [
        _diag(
            CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_SCAN_ONLY,
            ".frd scan is block metadata only; values, fields, and mesh are deferred.",
            path=str(path),
            artifact_kind=artifact_kind,
            severity=CalculiXResultParserSeverity.INFO,
        )
    ]
    headings = [
        (index, text, kind)
        for index, text in enumerate(lines, start=1)
        if (kind := _classify_block_header(text)) is not None
    ]
    if not headings:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FRD_NO_RECOGNIZED_BLOCKS,
                "No recognized .frd block boundaries were found.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )
        return [], [], CalculiXFrdBlockSummary(), diagnostics

    retained_headings = headings[: limits.max_blocks]
    if len(headings) > len(retained_headings):
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_LIMIT_EXCEEDED,
                ".frd block count exceeded scanner retention limits.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )

    blocks: list[CalculiXFrdBlock] = []
    unknown_retained = 0
    for position, (line_number, heading, kind) in enumerate(retained_headings):
        if (
            kind is CalculiXFrdBlockKind.UNKNOWN
            and unknown_retained >= limits.max_unknown_blocks
        ):
            continue
        if kind is CalculiXFrdBlockKind.UNKNOWN:
            unknown_retained += 1
        next_start = (
            retained_headings[position + 1][0]
            if position + 1 < len(retained_headings)
            else len(lines) + 1
        )
        natural_end = max(line_number, next_start - 1)
        bounded_end = min(natural_end, line_number + limits.max_block_lines - 1)
        if bounded_end < natural_end:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_TOO_LARGE,
                    ".frd block span exceeded scanner limits.",
                    path=str(path),
                    artifact_kind=artifact_kind,
                )
            )
        block_lines = lines[line_number - 1 : bounded_end]
        numeric_tokens_present = any(_has_digit(item) for item in block_lines)
        snippets = tuple(
            _trim_snippet(item, limits.max_snippet_chars)
            for item in block_lines[: limits.max_block_snippets]
        )
        unsupported = kind is CalculiXFrdBlockKind.UNSUPPORTED
        blocks.append(
            CalculiXFrdBlock(
                label=_trim_snippet(heading.strip(), limits.max_snippet_chars),
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
                    CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_UNSUPPORTED,
                    f"Unsupported .frd block was preserved: {heading.strip()}",
                    path=str(path),
                    artifact_kind=artifact_kind,
                )
            )
        if kind is CalculiXFrdBlockKind.UNKNOWN:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_FRD_UNKNOWN_RECORD,
                    f"Unknown .frd record was preserved: {heading.strip()}",
                    path=str(path),
                    artifact_kind=artifact_kind,
                )
            )

    references = _reference_candidates(
        blocks,
        path=path,
        limits=limits,
        diagnostics=diagnostics,
        artifact_kind=artifact_kind,
    )
    if any(block.numeric_tokens_present for block in blocks):
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FRD_FIELD_VALUES_NOT_PARSED,
                "Numeric-looking .frd tokens were kept as snippets and not parsed.",
                path=str(path),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.INFO,
            )
        )
    if any(
        block.kind
        in {
            CalculiXFrdBlockKind.MESH_REFERENCE_CANDIDATE,
            CalculiXFrdBlockKind.NODE_REFERENCE_CANDIDATE,
            CalculiXFrdBlockKind.ELEMENT_REFERENCE_CANDIDATE,
        }
        for block in blocks
    ):
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FRD_MESH_RECONSTRUCTION_FORBIDDEN,
                ".frd node or element records remain references; mesh is not reconstructed.",
                path=str(path),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.INFO,
            )
        )

    summary = _summary_from_blocks(blocks, references)
    return blocks, references, summary, diagnostics


def _classify_block_header(text: str) -> CalculiXFrdBlockKind | None:
    stripped = text.strip()
    if not stripped:
        return None
    lowered = stripped.lower()
    if not _looks_like_block_boundary(stripped, lowered):
        return None

    if any(token in lowered for token in ("binary", "unsupported", "opaque")):
        return CalculiXFrdBlockKind.UNSUPPORTED
    if any(
        token in lowered
        for token in ("stress", "strain", "displacement", "temperature", "field")
    ):
        return CalculiXFrdBlockKind.FIELD_REFERENCE_CANDIDATE
    if "result" in lowered:
        return CalculiXFrdBlockKind.RESULT_BLOCK_CANDIDATE
    if any(token in lowered for token in ("element", "connectivity")):
        return CalculiXFrdBlockKind.ELEMENT_REFERENCE_CANDIDATE
    if any(token in lowered for token in ("node", "coordinate")):
        return CalculiXFrdBlockKind.NODE_REFERENCE_CANDIDATE
    if any(token in lowered for token in ("mesh", "topology")):
        return CalculiXFrdBlockKind.MESH_REFERENCE_CANDIDATE
    if any(token in lowered for token in ("calculix", "frd", "header", "job", "date", "version")):
        return CalculiXFrdBlockKind.HEADER
    return CalculiXFrdBlockKind.UNKNOWN


def _looks_like_block_boundary(stripped: str, lowered: str) -> bool:
    first = stripped.split(maxsplit=1)[0]
    if first[:1] in {"-", "+"}:
        numeric_part = first[1:]
    else:
        numeric_part = first.rstrip("cC")
    if numeric_part.isdigit() and len(stripped) <= 240:
        return first.endswith(("c", "C"))
    if stripped.endswith(":"):
        return True
    if stripped.startswith(("--", "==")):
        return True
    letters = [char for char in stripped if char.isalpha()]
    if letters and all(char.isupper() for char in letters) and len(letters) >= 4:
        return True
    return any(
        token in lowered
        for token in (
            "frd header",
            "node block",
            "element block",
            "field block",
            "result block",
            "mesh block",
        )
    )


def _reference_candidates(
    blocks: Sequence[CalculiXFrdBlock],
    *,
    path: Path,
    limits: CalculiXFrdBlockScanLimits,
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic],
    artifact_kind: str,
) -> list[CalculiXFrdReferenceCandidate]:
    candidates: list[CalculiXFrdReferenceCandidate] = []
    for index, block in enumerate(blocks):
        reference_kind = _reference_kind(block.kind)
        if reference_kind == "":
            continue
        if len(candidates) >= limits.max_reference_candidates:
            diagnostics.append(
                _diag(
                    CalculiXResultParserDiagnosticCode.FP_FRD_BLOCK_LIMIT_EXCEEDED,
                    ".frd reference candidate count exceeded scanner limits.",
                    path=str(path),
                    artifact_kind=artifact_kind,
                )
            )
            break
        candidates.append(
            CalculiXFrdReferenceCandidate(
                reference_kind=reference_kind,
                label=block.label,
                block_kind=block.kind,
                block_index=index,
                line_number=block.heading_line_number,
                source_path=str(path),
                snippet=block.snippets[0] if block.snippets else "",
            )
        )
    if candidates:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FRD_REFERENCE_CANDIDATE_ONLY,
                ".frd references are candidates only; fields and mesh remain deferred.",
                path=str(path),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.INFO,
            )
        )
    return candidates


def _reference_kind(kind: CalculiXFrdBlockKind) -> str:
    if kind is CalculiXFrdBlockKind.MESH_REFERENCE_CANDIDATE:
        return "mesh"
    if kind is CalculiXFrdBlockKind.NODE_REFERENCE_CANDIDATE:
        return "node"
    if kind is CalculiXFrdBlockKind.ELEMENT_REFERENCE_CANDIDATE:
        return "element"
    if kind is CalculiXFrdBlockKind.FIELD_REFERENCE_CANDIDATE:
        return "field"
    if kind is CalculiXFrdBlockKind.RESULT_BLOCK_CANDIDATE:
        return "result"
    if kind is CalculiXFrdBlockKind.UNKNOWN:
        return "unknown"
    return ""


def _read_text(
    path: Path,
    artifact_kind: str,
) -> tuple[str, bool, list[FEASpecCalculiXResultParserDiagnostic]]:
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic] = []
    try:
        raw = path.read_bytes()
    except OSError as exc:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
                f"Unable to read .frd artifact: {exc}",
                path=str(path),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.ERROR,
                blocks_parse=True,
            )
        )
        return "", False, diagnostics

    if _is_binary_like(raw):
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FRD_BINARY_UNSUPPORTED,
                ".frd content appears binary or opaque for this text block scanner.",
                path=str(path),
                artifact_kind=artifact_kind,
                severity=CalculiXResultParserSeverity.WARNING,
            )
        )
        return "", True, diagnostics

    try:
        return raw.decode("utf-8"), False, diagnostics
    except UnicodeDecodeError:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_ENCODING_UNSUPPORTED,
                "UTF-8 decode failed; using replacement text for .frd block scan.",
                path=str(path),
                artifact_kind=artifact_kind,
            )
        )
        return raw.decode("utf-8", errors="replace"), False, diagnostics


def _is_binary_like(raw: bytes) -> bool:
    if b"\x00" in raw:
        return True
    if not raw:
        return False
    sample = raw[:4096]
    non_text = sum(
        1
        for byte in sample
        if byte not in b"\n\r\t\b\f" and (byte < 32 or byte > 126)
    )
    return non_text > max(8, len(sample) // 12)


def _summary_from_blocks(
    blocks: Sequence[CalculiXFrdBlock],
    references: Sequence[CalculiXFrdReferenceCandidate],
) -> CalculiXFrdBlockSummary:
    counts: Counter[CalculiXFrdBlockKind] = Counter(block.kind for block in blocks)
    reference_counts: Counter[str] = Counter(
        candidate.reference_kind for candidate in references
    )
    unknown = counts[CalculiXFrdBlockKind.UNKNOWN]
    unsupported = counts[CalculiXFrdBlockKind.UNSUPPORTED]
    return CalculiXFrdBlockSummary(
        kind_counts=dict(counts),
        reference_kind_counts=dict(reference_counts),
        block_count=len(blocks),
        recognized_block_count=max(0, len(blocks) - unknown),
        unknown_block_count=unknown,
        unsupported_block_count=unsupported,
        reference_candidate_count=len(references),
        field_reference_candidate_count=reference_counts["field"],
        mesh_reference_candidate_count=(
            reference_counts["mesh"]
            + reference_counts["node"]
            + reference_counts["element"]
        ),
        numeric_tokens_not_parsed=any(block.numeric_tokens_present for block in blocks),
    )


def _merge_summaries(
    summaries: Sequence[CalculiXFrdBlockSummary],
) -> CalculiXFrdBlockSummary:
    counts: Counter[CalculiXFrdBlockKind] = Counter()
    reference_counts: Counter[str] = Counter()
    block_count = 0
    recognized = 0
    unknown = 0
    unsupported = 0
    references = 0
    field_references = 0
    mesh_references = 0
    numeric_tokens = False
    for summary in summaries:
        counts.update(summary.kind_counts)
        reference_counts.update(summary.reference_kind_counts)
        block_count += summary.block_count
        recognized += summary.recognized_block_count
        unknown += summary.unknown_block_count
        unsupported += summary.unsupported_block_count
        references += summary.reference_candidate_count
        field_references += summary.field_reference_candidate_count
        mesh_references += summary.mesh_reference_candidate_count
        numeric_tokens = numeric_tokens or summary.numeric_tokens_not_parsed
    return CalculiXFrdBlockSummary(
        kind_counts=dict(counts),
        reference_kind_counts=dict(reference_counts),
        block_count=block_count,
        recognized_block_count=recognized,
        unknown_block_count=unknown,
        unsupported_block_count=unsupported,
        reference_candidate_count=references,
        field_reference_candidate_count=field_references,
        mesh_reference_candidate_count=mesh_references,
        numeric_tokens_not_parsed=numeric_tokens,
    )


def _metadata_by_path(
    metadata_scan: CalculiXResultDirectoryMetadataScan | None,
) -> Mapping[Path, CalculiXResultFileMetadata]:
    if metadata_scan is None:
        return {}
    return {item.path: item for item in metadata_scan.artifacts}


def _directory_status(
    scans: Sequence[CalculiXFrdBlockScan],
    diagnostics: Sequence[FEASpecCalculiXResultParserDiagnostic],
) -> CalculiXFrdBlockScanStatus:
    if any(scan.status is CalculiXFrdBlockScanStatus.BLOCKED for scan in scans):
        return CalculiXFrdBlockScanStatus.BLOCKED
    if not scans:
        return CalculiXFrdBlockScanStatus.UNSUPPORTED
    if any(scan.status is CalculiXFrdBlockScanStatus.METADATA_ONLY for scan in scans):
        return CalculiXFrdBlockScanStatus.METADATA_ONLY
    if diagnostics or any(
        scan.status is CalculiXFrdBlockScanStatus.SCANNED_WITH_WARNINGS
        for scan in scans
    ):
        return CalculiXFrdBlockScanStatus.SCANNED_WITH_WARNINGS
    return CalculiXFrdBlockScanStatus.SCANNED


def _file_scan(
    *,
    path: Path,
    suffix: str,
    artifact_kind: str,
    status: CalculiXFrdBlockScanStatus,
    metadata: Mapping[str, Any],
    line_count: int = 0,
    processed_line_count: int = 0,
    line_count_truncated: bool = False,
    summary: CalculiXFrdBlockSummary | None = None,
    blocks: tuple[CalculiXFrdBlock, ...] = (),
    reference_candidates: tuple[CalculiXFrdReferenceCandidate, ...] = (),
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...] = (),
) -> CalculiXFrdBlockScan:
    return CalculiXFrdBlockScan(
        path=path,
        name=path.name,
        suffix=suffix,
        artifact_kind=artifact_kind,
        status=status,
        metadata=dict(metadata),
        line_count=line_count,
        processed_line_count=processed_line_count,
        line_count_truncated=line_count_truncated,
        summary=summary or CalculiXFrdBlockSummary(),
        blocks=blocks,
        reference_candidates=reference_candidates,
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
