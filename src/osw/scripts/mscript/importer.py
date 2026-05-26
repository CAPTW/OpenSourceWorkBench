"""Preview-only `.m` importer for MATLAB/Octave source text."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticReport
from osw.core.project_schema import ScriptRef

from .errors import MScriptImportError
from .parser import (
    classify_mscript,
    extract_detected_calls,
    extract_first_comment_block,
    extract_function_signature,
    extract_help_text,
    extract_imports_or_paths,
    extract_plot_hints,
    strip_mscript_comment,
)
from .safety_scan import scan_mscript_text
from .script_model import (
    FunctionSignature,
    SafetyFinding,
    SafetySeverity,
    ScriptKind,
    ScriptPreview,
    finding_counts,
    script_preview_id,
)


class MScriptResultStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class MScriptReadResult:
    status: MScriptResultStatus
    text: str = ""
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    source_path: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {MScriptResultStatus.OK, MScriptResultStatus.WARNING}


@dataclass(frozen=True)
class MScriptPreviewResult:
    status: MScriptResultStatus
    preview: ScriptPreview | None = None
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    source_path: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {MScriptResultStatus.OK, MScriptResultStatus.WARNING}


def is_mscript_path(path: str | Path) -> bool:
    return Path(path).suffix.lower() == ".m"


def read_mscript_text(path: str | Path) -> MScriptReadResult:
    script_path = Path(path)
    report = DiagnosticReport()
    if script_path.suffix.lower() != ".m":
        report.add_error(
            "mscript-unsupported-extension",
            "Only .m script preview is supported in this importer.",
            hint="Choose a MATLAB/Octave .m file.",
            path=script_path,
        )
        return MScriptReadResult(
            MScriptResultStatus.ERROR,
            diagnostics=report,
            source_path=str(path),
        )
    if not script_path.exists():
        report.add_error(
            "mscript-file-missing",
            f"M-script file does not exist: {script_path}",
            hint="Choose an existing .m file before preview import.",
            path=script_path,
        )
        return MScriptReadResult(
            MScriptResultStatus.ERROR,
            diagnostics=report,
            source_path=str(script_path),
        )

    try:
        return MScriptReadResult(
            MScriptResultStatus.OK,
            text=script_path.read_text(encoding="utf-8"),
            diagnostics=report,
            source_path=str(script_path),
        )
    except UnicodeDecodeError:
        text = script_path.read_text(encoding="utf-8", errors="replace")
        report.add_warning(
            "mscript-decoding-fallback",
            "M-script text was decoded with replacement characters.",
            hint="Save the script as UTF-8 for the most reliable preview.",
            path=script_path,
        )
        return MScriptReadResult(
            MScriptResultStatus.WARNING,
            text=text,
            diagnostics=report,
            source_path=str(script_path),
        )
    except OSError as exc:
        report.add_error(
            "mscript-read-failed",
            f"Could not read M-script file {script_path}: {exc}",
            hint="Check file permissions and try again.",
            path=script_path,
        )
        return MScriptReadResult(
            MScriptResultStatus.ERROR,
            diagnostics=report,
            source_path=str(script_path),
        )


def preview_mscript(path: str | Path) -> MScriptPreviewResult:
    read_result = read_mscript_text(path)
    if not read_result.ok:
        return MScriptPreviewResult(
            MScriptResultStatus.ERROR,
            diagnostics=read_result.diagnostics,
            source_path=read_result.source_path,
        )
    report = DiagnosticReport()
    report.extend(read_result.diagnostics)
    preview = preview_mscript_text(read_result.text, source_path=read_result.source_path)
    _add_preview_diagnostics(preview, report)
    status = MScriptResultStatus.WARNING if report.messages else MScriptResultStatus.OK
    if any(
        finding.severity in {SafetySeverity.HIGH.value, SafetySeverity.BLOCKED.value}
        for finding in preview.safety_findings
    ):
        status = MScriptResultStatus.WARNING
    return MScriptPreviewResult(
        status,
        preview=preview,
        diagnostics=report,
        source_path=read_result.source_path,
    )


def import_mscript_preview(path: str | Path) -> ScriptPreview:
    result = preview_mscript(path)
    if result.preview is None:
        raise MScriptImportError(result.diagnostics.summary())
    return result.preview


def preview_mscript_text(
    text: str,
    *,
    source_path: str | None = None,
    source: str | None = None,
    fallback_name: str = "script",
) -> ScriptPreview:
    resolved_source = source_path or source or "<memory>"
    lines = text.splitlines()
    code_lines = [strip_mscript_comment(line).strip() for line in lines]
    executable_lines = [line for line in code_lines if line]
    comment_count = sum(1 for line in lines if line.strip().startswith("%"))
    kind = classify_mscript(text)
    function_signature = extract_function_signature(text)
    name = _preview_name(resolved_source, fallback_name, function_signature)
    safety = scan_mscript_text(text, source=resolved_source)
    plot_hints = tuple(extract_plot_hints(text))
    metadata = {
        "preview_only": True,
        "safety_summary": _safety_summary(safety.findings),
        "plot_hint_count": len(plot_hints),
        "source_excerpt": _source_excerpt(text),
    }
    if function_signature is not None:
        metadata["function_name"] = function_signature.name
    return ScriptPreview(
        id=script_preview_id(resolved_source),
        name=name,
        source_path=resolved_source,
        kind=kind,
        line_count=len(lines),
        character_count=len(text),
        help_text=extract_help_text(text),
        first_comment_block=extract_first_comment_block(text),
        function_signature=function_signature,
        plot_hints=plot_hints,
        safety_findings=safety.findings,
        detected_calls=extract_detected_calls(text),
        imports_or_paths=extract_imports_or_paths(text),
        safe_preview_required=True,
        can_execute=False,
        metadata=metadata,
        executable_line_count=len(executable_lines),
        comment_line_count=comment_count,
        entrypoint=function_signature.name if function_signature is not None else None,
        safety=safety,
    )


def create_script_ref(preview: ScriptPreview) -> ScriptRef:
    metadata: dict[str, Any] = {
        "preview": preview.to_dict(),
        "kind": preview.kind.value,
        "line_count": preview.line_count,
        "character_count": preview.character_count,
        "safety_summary": preview.safety_summary(),
        "plot_hint_count": len(preview.plot_hints),
        "safe_preview_required": True,
        "can_execute": False,
    }
    if preview.function_signature is not None:
        metadata["function_name"] = preview.function_signature.name
        metadata["raw_signature"] = preview.function_signature.raw_signature
    return ScriptRef(
        id=preview.id,
        path=preview.source_path,
        language="matlab_octave",
        name=preview.name if preview.name.endswith(".m") else Path(preview.source_path).name,
        role="preview",
        status="previewed",
        safe_preview_required=True,
        metadata=metadata,
    )


def _preview_name(
    source_path: str,
    fallback_name: str,
    function_signature: FunctionSignature | None,
) -> str:
    if function_signature is not None:
        return function_signature.name
    if source_path and source_path != "<memory>":
        return Path(source_path).stem
    return fallback_name


def _add_preview_diagnostics(preview: ScriptPreview, report: DiagnosticReport) -> None:
    if preview.line_count == 0:
        report.add_warning(
            "mscript-empty-file",
            "M-script file is empty.",
            hint="Preview contains no executable MATLAB/Octave statements.",
            path=preview.source_path,
        )
    if preview.kind is ScriptKind.UNKNOWN:
        report.add_warning(
            "mscript-kind-unknown",
            "M-script kind could not be classified from executable text.",
            hint="Comments-only and empty files are accepted as preview-only imports.",
            path=preview.source_path,
        )
    if preview.kind is ScriptKind.CLASSDEF:
        report.add_warning(
            "mscript-classdef-limited",
            (
                "classdef files are detected, but class execution and toolbox behavior "
                "are out of scope."
            ),
            hint="Review class metadata manually; OSW will not instantiate or execute the class.",
            path=preview.source_path,
        )
    for finding in preview.safety_findings:
        if finding.severity in {SafetySeverity.HIGH.value, SafetySeverity.BLOCKED.value}:
            report.add_warning(
                finding.code,
                finding.message,
                hint=finding.hint,
                path=preview.source_path,
                metadata={"line_no": finding.line_no, "token": finding.token},
            )


def _safety_summary(findings: tuple[SafetyFinding, ...]) -> str:
    counts = finding_counts(findings)
    return (
        f"blocked={counts.get(SafetySeverity.BLOCKED.value, 0)}, "
        f"high={counts.get(SafetySeverity.HIGH.value, 0)}, "
        f"warnings={counts.get(SafetySeverity.WARNING.value, 0)}"
    )


def _source_excerpt(text: str, *, max_lines: int = 160, max_chars: int = 12_000) -> str:
    excerpt = "\n".join(text.splitlines()[:max_lines])
    if len(excerpt) > max_chars:
        excerpt = f"{excerpt[:max_chars]}\n% ... preview truncated ..."
    return excerpt


__all__ = [
    "MScriptImportError",
    "MScriptPreviewResult",
    "MScriptReadResult",
    "MScriptResultStatus",
    "classify_mscript",
    "create_script_ref",
    "extract_function_signature",
    "extract_help_text",
    "extract_plot_hints",
    "import_mscript_preview",
    "is_mscript_path",
    "preview_mscript",
    "preview_mscript_text",
    "read_mscript_text",
]
