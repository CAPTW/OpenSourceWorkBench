"""Metadata-only scanner for FEASpec CalculiX result artifacts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .calculix_result_parser_diagnostics import (
    CalculiXResultParserDiagnosticCode,
    CalculiXResultParserSeverity,
    FEASpecCalculiXResultParserDiagnostic,
)

__all__ = [
    "CalculiXResultMetadataLimits",
    "CalculiXResultFileMetadata",
    "CalculiXResultDirectoryMetadataScan",
    "CalculiXResultMetadataStatus",
    "scan_calculix_result_file_metadata",
    "scan_calculix_result_directory_metadata",
    "explain_calculix_result_metadata_scan",
]


class CalculiXResultMetadataStatus(str, Enum):
    """Scanner result status."""

    SCANNED = "scanned"
    SCANNED_WITH_WARNINGS = "scanned-with-warnings"
    BLOCKED = "blocked"
    UNSUPPORTED = "unsupported"
    LIMIT_EXCEEDED = "limit-exceeded"


@dataclass(frozen=True, slots=True)
class CalculiXResultMetadataLimits:
    """Limits used by the metadata scanner."""

    max_file_bytes: int = 100_000
    max_lines: int = 256
    max_snippet_chars: int = 160
    max_snippet_lines: int = 4
    allowed_suffixes: tuple[str, ...] = (
        ".dat",
        ".frd",
        ".sta",
        ".cvg",
        ".inp",
        ".txt",
        ".json",
        ".log",
    )


@dataclass(frozen=True, slots=True)
class CalculiXResultFileMetadata:
    """Per-file metadata-only scan output."""

    path: Path
    name: str
    suffix: str
    artifact_kind: str
    exists: bool
    is_file: bool
    byte_size: int
    sha256: str
    encoding: str
    encoding_supported: bool
    line_count: int
    line_count_truncated: bool
    first_line_snippets: tuple[str, ...]
    last_line_snippets: tuple[str, ...]
    snippet_truncated: bool
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...]
    parser_phase: str
    parse_not_implemented: bool
    status: CalculiXResultMetadataStatus

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "name": self.name,
            "suffix": self.suffix,
            "artifact_kind": self.artifact_kind,
            "exists": self.exists,
            "is_file": self.is_file,
            "byte_size": self.byte_size,
            "sha256": self.sha256,
            "encoding": self.encoding,
            "encoding_supported": self.encoding_supported,
            "line_count": self.line_count,
            "line_count_truncated": self.line_count_truncated,
            "first_line_snippets": list(self.first_line_snippets),
            "last_line_snippets": list(self.last_line_snippets),
            "snippet_truncated": self.snippet_truncated,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "parser_phase": self.parser_phase,
            "parse_not_implemented": self.parse_not_implemented,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class CalculiXResultDirectoryMetadataScan:
    """Directory scan summary for explicit result directories."""

    result_dir: Path
    exists: bool
    is_directory: bool
    status: CalculiXResultMetadataStatus
    artifacts: tuple[CalculiXResultFileMetadata, ...]
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "result_dir": str(self.result_dir),
            "exists": self.exists,
            "is_directory": self.is_directory,
            "status": self.status.value,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "artifact_count": len(self.artifacts),
        }


def scan_calculix_result_file_metadata(
    path: str | Path,
    *,
    limits: CalculiXResultMetadataLimits | None = None,
) -> CalculiXResultFileMetadata:
    """Scan an explicit file path for safe, deterministic metadata only."""

    resolved_limits = limits or CalculiXResultMetadataLimits()
    target = Path(path).expanduser()
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic] = []

    if not target.exists():
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
                f"Requested artifact does not exist: {target}",
                path=str(target),
                artifact_kind="unknown",
                blocks_parse=True,
                blocks_import=False,
            )
        )
        return _build_file_metadata(
            path=target,
            exists=False,
            is_file=False,
            byte_size=0,
            sha256="",
            encoding="",
            encoding_supported=False,
            line_count=0,
            line_count_truncated=False,
            first_line_snippets=(),
            last_line_snippets=(),
            snippet_truncated=False,
            diagnostics=tuple(diagnostics),
            parser_phase="blocked",
            parse_not_implemented=False,
            status=CalculiXResultMetadataStatus.BLOCKED,
        )

    if not target.is_file():
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_PATH_NOT_FILE,
                f"Requested artifact path is not a file: {target}",
                path=str(target),
                artifact_kind="unknown",
                blocks_parse=True,
                blocks_import=False,
            )
        )
        return _build_file_metadata(
            path=target,
            exists=True,
            is_file=False,
            byte_size=0,
            sha256="",
            encoding="",
            encoding_supported=False,
            line_count=0,
            line_count_truncated=False,
            first_line_snippets=(),
            last_line_snippets=(),
            snippet_truncated=False,
            diagnostics=tuple(diagnostics),
            parser_phase="blocked",
            parse_not_implemented=False,
            status=CalculiXResultMetadataStatus.BLOCKED,
        )

    artifact_kind = _classify_artifact_kind(target)
    parser_phase = "metadata-only"
    parse_not_implemented = artifact_kind in {"dat", "frd", "sta", "cvg"}

    byte_size = _file_size(target, diagnostics, artifact_kind)
    sha256 = _sha256(target, diagnostics, artifact_kind)

    if artifact_kind == "other" and not _is_allowed_special_suffix(target, resolved_limits):
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT,
                f"Unsupported artifact format for metadata scan: {target.suffix.lower()}",
                path=str(target),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )

    lines: tuple[str, ...] = ()
    if byte_size <= resolved_limits.max_file_bytes:
        text, encoding, encoding_supported = _read_text(target, diagnostics, artifact_kind)
        if text:
            lines = tuple(text.splitlines())
    else:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_SIZE_LIMIT_EXCEEDED,
                f"File exceeds metadata byte limit: {byte_size} > "
                f"{resolved_limits.max_file_bytes}",
                path=str(target),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )
        text = ""
        encoding = "binary"
        encoding_supported = False

    if not byte_size and not text:
        line_count = 0
        line_count_truncated = False
    else:
        line_count, line_count_truncated = _line_count(lines, resolved_limits.max_lines)

    first_line_snippets, last_line_snippets, snippet_truncated = _line_snippets(
        lines=lines,
        max_chars=resolved_limits.max_snippet_chars,
        max_lines=resolved_limits.max_snippet_lines,
    )

    if byte_size <= resolved_limits.max_file_bytes and line_count_truncated:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_LINE_LIMIT_EXCEEDED,
                "Line count exceeded metadata scan line limit.",
                path=str(target),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )

    if snippet_truncated:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_SNIPPET_TRUNCATED,
                "Snippet truncation occurred during metadata scan.",
                path=str(target),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )

    if parse_not_implemented:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_METADATA_ONLY,
                "Parser phase is metadata-only for this artifact family.",
                path=str(target),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_PARSE_NOT_IMPLEMENTED,
                "Numerical parsing for this artifact family is not implemented in this phase.",
                path=str(target),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )

    status = _derive_status(diagnostics, artifact_kind=artifact_kind)

    return _build_file_metadata(
        path=target,
        exists=True,
        is_file=True,
        byte_size=byte_size,
        sha256=sha256,
        encoding=encoding,
        encoding_supported=encoding_supported,
        line_count=line_count,
        line_count_truncated=line_count_truncated,
        first_line_snippets=first_line_snippets,
        last_line_snippets=last_line_snippets,
        snippet_truncated=snippet_truncated,
        diagnostics=tuple(diagnostics),
        parser_phase=parser_phase,
        parse_not_implemented=parse_not_implemented,
        status=status,
    )


def scan_calculix_result_directory_metadata(
    result_dir: str | Path,
    *,
    limits: CalculiXResultMetadataLimits | None = None,
) -> CalculiXResultDirectoryMetadataScan:
    """Scan immediate files in an explicit directory without recursion."""

    resolved_limits = limits or CalculiXResultMetadataLimits()
    root = Path(result_dir).expanduser()

    if not root.exists():
        diagnostics = (
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
                "Result directory does not exist.",
                path=str(root),
                artifact_kind="directory",
                blocks_parse=True,
                blocks_import=False,
            ),
        )
        return CalculiXResultDirectoryMetadataScan(
            result_dir=root,
            exists=False,
            is_directory=False,
            status=CalculiXResultMetadataStatus.BLOCKED,
            artifacts=(),
            diagnostics=diagnostics,
        )

    if not root.is_dir():
        diagnostics = (
            _diag(
                CalculiXResultParserDiagnosticCode.FP_PATH_NOT_FILE,
                "Result path exists but is not a directory.",
                path=str(root),
                artifact_kind="directory",
                blocks_parse=True,
                blocks_import=False,
            ),
        )
        return CalculiXResultDirectoryMetadataScan(
            result_dir=root,
            exists=True,
            is_directory=False,
            status=CalculiXResultMetadataStatus.BLOCKED,
            artifacts=(),
            diagnostics=diagnostics,
        )

    artifacts = tuple(
        scan_calculix_result_file_metadata(child, limits=resolved_limits)
        for child in sorted(
            (child for child in root.iterdir() if child.is_file()),
            key=lambda item: item.name,
        )
    )
    diagnostics = tuple(d for item in artifacts for d in item.diagnostics)
    status = _derive_directory_status(artifacts, diagnostics)

    return CalculiXResultDirectoryMetadataScan(
        result_dir=root,
        exists=True,
        is_directory=True,
        status=status,
        artifacts=artifacts,
        diagnostics=diagnostics,
    )


def explain_calculix_result_metadata_scan(
    scan: CalculiXResultDirectoryMetadataScan,
) -> list[str]:
    """Return a reviewer-oriented scan explanation."""

    lines = [
        f"Metadata scan status: {scan.status.value}.",
        f"Directory: {scan.result_dir}.",
        f"Artifacts scanned: {len(scan.artifacts)}.",
    ]
    for item in scan.diagnostics:
        path = f" [{item.path}]" if item.path else ""
        lines.append(f"{item.severity.value.upper()} {item.code.value}{path}: {item.message}")
    return lines


def _classify_artifact_kind(path: Path) -> str:
    """Classify CalculiX result-like artifacts by name and suffix."""

    name = path.name.lower()
    suffix = path.suffix.lower()

    if name == "run_metadata.json":
        return "run_metadata"
    if name.endswith(".manifest.json"):
        return "export_manifest"
    if name.endswith(".diagnostics.json"):
        return "export_diagnostics"
    if name == "stdout.txt":
        return "stdout"
    if name == "stderr.txt":
        return "stderr"
    if name == "readme_run_first.txt":
        return "readme"
    if suffix == ".dat":
        return "dat"
    if suffix == ".frd":
        return "frd"
    if suffix == ".sta":
        return "sta"
    if suffix == ".cvg":
        return "cvg"
    if suffix == ".inp":
        return "inp"
    if suffix == ".txt":
        return "txt"
    if suffix == ".json":
        return "json"
    if suffix == ".log":
        return "log"
    return "other"


def _is_allowed_special_suffix(path: Path, limits: CalculiXResultMetadataLimits) -> bool:
    suffix = path.suffix.lower()
    name = path.name.lower()
    if name in {"run_metadata.json", "stdout.txt", "stderr.txt", "readme_run_first.txt"}:
        return True
    if name.endswith(".manifest.json") or name.endswith(".diagnostics.json"):
        return True
    return suffix in limits.allowed_suffixes


def _read_text(
    path: Path,
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic],
    artifact_kind: str,
) -> tuple[str, str, bool]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
                f"Unable to read file bytes: {exc}",
                path=str(path),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )
        return "", "binary", False

    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig", True

    try:
        return raw.decode("utf-8"), "utf-8", True
    except UnicodeDecodeError:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_ENCODING_UNSUPPORTED,
                "UTF-8 decode failed; using replacement decoding.",
                path=str(path),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )

    try:
        return raw.decode("utf-8-sig"), "utf-8-sig", True
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace"), "utf-8-replaced", False


def _file_size(
    path: Path,
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic],
    artifact_kind: str,
) -> int:
    try:
        return path.stat().st_size
    except OSError as exc:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_HASH_FAILED,
                f"Unable to read file metadata: {exc}",
                path=str(path),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )
        return 0


def _line_count(lines: tuple[str, ...], max_lines: int) -> tuple[int, bool]:
    if max_lines < 0:
        return 0, False
    if len(lines) <= max_lines:
        return len(lines), False
    return max_lines, True


def _trim_snippet(line: str, max_chars: int) -> tuple[str, bool]:
    if max_chars < 0:
        return "", line != ""
    if len(line) <= max_chars:
        return line, False
    return line[:max_chars], True


def _line_snippets(
    *,
    lines: tuple[str, ...],
    max_chars: int,
    max_lines: int,
) -> tuple[tuple[str, ...], tuple[str, ...], bool]:
    if max_lines <= 0:
        return (), (), False

    all_lines = lines or ()
    if not all_lines:
        return (), (), False

    capture_lines = max_lines if max_lines > 0 else 0
    if capture_lines <= 0:
        return (), (), False

    first = all_lines[:capture_lines]
    last = all_lines[-capture_lines:]

    first_snippets: list[str] = []
    last_snippets: list[str] = []
    truncated = False

    for item in first:
        value, is_truncated = _trim_snippet(item, max_chars)
        first_snippets.append(value)
        truncated = truncated or is_truncated

    for item in last:
        value, is_truncated = _trim_snippet(item, max_chars)
        last_snippets.append(value)
        truncated = truncated or is_truncated

    if len(all_lines) > max_lines:
        truncated = True

    return tuple(first_snippets), tuple(last_snippets), truncated


def _sha256(
    path: Path,
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic],
    artifact_kind: str,
) -> str:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as exc:
        diagnostics.append(
            _diag(
                CalculiXResultParserDiagnosticCode.FP_HASH_FAILED,
                f"Unable to hash file: {exc}",
                path=str(path),
                artifact_kind=artifact_kind,
                blocks_parse=False,
                blocks_import=False,
            )
        )
        return ""


def _build_file_metadata(
    *,
    path: Path,
    exists: bool,
    is_file: bool,
    byte_size: int,
    sha256: str,
    encoding: str,
    encoding_supported: bool,
    line_count: int,
    line_count_truncated: bool,
    first_line_snippets: tuple[str, ...],
    last_line_snippets: tuple[str, ...],
    snippet_truncated: bool,
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...],
    parser_phase: str,
    parse_not_implemented: bool,
    status: CalculiXResultMetadataStatus,
) -> CalculiXResultFileMetadata:
    return CalculiXResultFileMetadata(
        path=path,
        name=path.name,
        suffix=path.suffix.lower(),
        artifact_kind=_classify_artifact_kind(path),
        exists=exists,
        is_file=is_file,
        byte_size=byte_size,
        sha256=sha256,
        encoding=encoding,
        encoding_supported=encoding_supported,
        line_count=line_count,
        line_count_truncated=line_count_truncated,
        first_line_snippets=first_line_snippets,
        last_line_snippets=last_line_snippets,
        snippet_truncated=snippet_truncated,
        diagnostics=diagnostics,
        parser_phase=parser_phase,
        parse_not_implemented=parse_not_implemented,
        status=status,
    )


def _derive_status(
    diagnostics: list[FEASpecCalculiXResultParserDiagnostic],
    artifact_kind: str,
) -> CalculiXResultMetadataStatus:
    if any(
        item.code
        in {
            CalculiXResultParserDiagnosticCode.FP_FILE_MISSING,
            CalculiXResultParserDiagnosticCode.FP_PATH_NOT_FILE,
        }
        for item in diagnostics
    ):
        return CalculiXResultMetadataStatus.BLOCKED
    if any(
        item.code is CalculiXResultParserDiagnosticCode.FP_UNSUPPORTED_FORMAT
        for item in diagnostics
    ):
        return CalculiXResultMetadataStatus.UNSUPPORTED
    if any(
        item.code
        in {
            CalculiXResultParserDiagnosticCode.FP_SIZE_LIMIT_EXCEEDED,
            CalculiXResultParserDiagnosticCode.FP_LINE_LIMIT_EXCEEDED,
            CalculiXResultParserDiagnosticCode.FP_SNIPPET_TRUNCATED,
        }
        for item in diagnostics
    ):
        return CalculiXResultMetadataStatus.LIMIT_EXCEEDED
    if artifact_kind == "other":
        return CalculiXResultMetadataStatus.UNSUPPORTED
    return (
        CalculiXResultMetadataStatus.SCANNED
        if not diagnostics
        else CalculiXResultMetadataStatus.SCANNED_WITH_WARNINGS
    )


def _derive_directory_status(
    scans: tuple[CalculiXResultFileMetadata, ...],
    diagnostics: tuple[FEASpecCalculiXResultParserDiagnostic, ...],
) -> CalculiXResultMetadataStatus:
    if any(scan.status is CalculiXResultMetadataStatus.BLOCKED for scan in scans):
        return CalculiXResultMetadataStatus.BLOCKED
    if any(scan.status is CalculiXResultMetadataStatus.UNSUPPORTED for scan in scans):
        return CalculiXResultMetadataStatus.UNSUPPORTED
    if any(scan.status is CalculiXResultMetadataStatus.LIMIT_EXCEEDED for scan in scans):
        return CalculiXResultMetadataStatus.LIMIT_EXCEEDED
    if any(scan.status is CalculiXResultMetadataStatus.SCANNED_WITH_WARNINGS for scan in scans):
        return CalculiXResultMetadataStatus.SCANNED_WITH_WARNINGS
    if diagnostics:
        return CalculiXResultMetadataStatus.SCANNED_WITH_WARNINGS
    if not scans:
        return CalculiXResultMetadataStatus.UNSUPPORTED
    return CalculiXResultMetadataStatus.SCANNED


def _diag(
    code: CalculiXResultParserDiagnosticCode,
    message: str,
    *,
    path: str,
    artifact_kind: str,
    blocks_parse: bool,
    blocks_import: bool,
    severity: CalculiXResultParserSeverity = CalculiXResultParserSeverity.WARNING,
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
