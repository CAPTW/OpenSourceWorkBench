"""Serializable preview models for MATLAB/Octave `.m` imports."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any


class ScriptKind(StrEnum):
    SCRIPT = "script"
    FUNCTION = "function"
    CLASSDEF = "classdef"
    UNKNOWN = "unknown"


MScriptKind = ScriptKind


class ScriptLanguage(StrEnum):
    MATLAB_OCTAVE = "matlab_octave"


class SafetySeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SafetyFinding:
    function: str = ""
    line: int = 0
    severity: str | SafetySeverity = SafetySeverity.WARNING
    message: str = ""
    snippet: str = ""
    code: str = ""
    hint: str = ""
    line_no: int | None = None
    column: int | None = None
    token: str = ""
    context: str = ""

    def __post_init__(self) -> None:
        severity = _severity_value(self.severity)
        line_no = self.line_no if self.line_no is not None else (self.line or None)
        line = self.line or int(line_no or 0)
        token = self.token or self.function
        function = self.function or token
        context = self.context or self.snippet
        snippet = self.snippet or context
        code = self.code or _code_from_token(token, severity)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "line_no", line_no)
        object.__setattr__(self, "line", line)
        object.__setattr__(self, "token", token)
        object.__setattr__(self, "function", function)
        object.__setattr__(self, "context", context)
        object.__setattr__(self, "snippet", snippet)
        object.__setattr__(self, "code", code)

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": str(self.severity),
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "line_no": self.line_no,
            "column": self.column,
            "token": self.token,
            "context": self.context,
            "function": self.function,
            "line": self.line,
            "snippet": self.snippet,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SafetyFinding:
        return cls(
            function=str(data.get("function", data.get("token", ""))),
            line=int(data.get("line", data.get("line_no", 0)) or 0),
            severity=str(data.get("severity", SafetySeverity.WARNING.value)),
            message=str(data.get("message", "")),
            snippet=str(data.get("snippet", data.get("context", ""))),
            code=str(data.get("code", "")),
            hint=str(data.get("hint", "")),
            line_no=_optional_int(data.get("line_no")),
            column=_optional_int(data.get("column")),
            token=str(data.get("token", data.get("function", ""))),
            context=str(data.get("context", data.get("snippet", ""))),
        )


@dataclass(frozen=True)
class FunctionSignature:
    name: str
    inputs: tuple[str, ...] = field(default_factory=tuple)
    outputs: tuple[str, ...] = field(default_factory=tuple)
    raw_signature: str = ""
    line_no: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "inputs", tuple(str(item) for item in self.inputs if item))
        object.__setattr__(self, "outputs", tuple(str(item) for item in self.outputs if item))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "raw_signature": self.raw_signature,
            "line_no": self.line_no,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any] | None) -> FunctionSignature | None:
        if not data:
            return None
        return cls(
            name=str(data.get("name", "")),
            inputs=tuple(str(item) for item in data.get("inputs", ())),
            outputs=tuple(str(item) for item in data.get("outputs", ())),
            raw_signature=str(data.get("raw_signature", "")),
            line_no=int(data.get("line_no", 0) or 0),
        )


@dataclass(frozen=True)
class PlotHint:
    command: str
    line_no: int
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "command": self.command,
            "line_no": self.line_no,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> PlotHint:
        return cls(
            command=str(data.get("command", "")),
            line_no=int(data.get("line_no", 0) or 0),
            context=str(data.get("context", "")),
        )


@dataclass(frozen=True)
class SafetyScanResult:
    source: str
    findings: tuple[SafetyFinding, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "findings", tuple(self.findings))

    @property
    def is_safe_for_preview(self) -> bool:
        return not any(
            str(finding.severity) in {SafetySeverity.HIGH.value, SafetySeverity.BLOCKED.value}
            for finding in self.findings
        )

    @property
    def high_or_blocked_count(self) -> int:
        return sum(
            1
            for finding in self.findings
            if str(finding.severity) in {SafetySeverity.HIGH.value, SafetySeverity.BLOCKED.value}
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "is_safe_for_preview": self.is_safe_for_preview,
            "findings": [finding.to_dict() for finding in self.findings],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> SafetyScanResult:
        return cls(
            source=str(data.get("source", "")),
            findings=tuple(
                SafetyFinding.from_dict(item)
                for item in data.get("findings", ())
                if isinstance(item, Mapping)
            ),
        )


@dataclass(frozen=True)
class ScriptPreview:
    id: str
    name: str
    source_path: str
    language: str | ScriptLanguage = ScriptLanguage.MATLAB_OCTAVE
    kind: ScriptKind = ScriptKind.UNKNOWN
    line_count: int = 0
    character_count: int = 0
    help_text: str = ""
    first_comment_block: str = ""
    function_signature: FunctionSignature | None = None
    plot_hints: tuple[PlotHint, ...] = field(default_factory=tuple)
    safety_findings: tuple[SafetyFinding, ...] = field(default_factory=tuple)
    detected_calls: tuple[str, ...] = field(default_factory=tuple)
    imports_or_paths: tuple[str, ...] = field(default_factory=tuple)
    safe_preview_required: bool = True
    can_execute: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    executable_line_count: int = 0
    comment_line_count: int = 0
    entrypoint: str | None = None
    safety: SafetyScanResult | None = None

    def __post_init__(self) -> None:
        kind = self.kind if isinstance(self.kind, ScriptKind) else ScriptKind(str(self.kind))
        language = (
            self.language.value if isinstance(self.language, ScriptLanguage) else str(self.language)
        )
        plot_hints = tuple(self.plot_hints)
        findings = tuple(self.safety_findings)
        safety = self.safety or SafetyScanResult(self.source_path, findings)
        if not findings:
            findings = tuple(safety.findings)
        entrypoint = self.entrypoint
        if entrypoint is None and self.function_signature is not None:
            entrypoint = self.function_signature.name
        object.__setattr__(self, "kind", kind)
        object.__setattr__(self, "language", language)
        object.__setattr__(self, "plot_hints", plot_hints)
        object.__setattr__(self, "safety_findings", findings)
        object.__setattr__(self, "safety", safety)
        object.__setattr__(self, "detected_calls", tuple(dict.fromkeys(self.detected_calls)))
        object.__setattr__(self, "imports_or_paths", tuple(self.imports_or_paths))
        object.__setattr__(self, "metadata", dict(self.metadata))
        object.__setattr__(self, "entrypoint", entrypoint)

    @property
    def source(self) -> str:
        return self.source_path

    @property
    def contains_plot_call(self) -> bool:
        return bool(self.plot_hints)

    def safety_summary(self) -> str:
        blocked = sum(
            1
            for finding in self.safety_findings
            if finding.severity == SafetySeverity.BLOCKED.value
        )
        high = sum(
            1 for finding in self.safety_findings if finding.severity == SafetySeverity.HIGH.value
        )
        warnings = sum(
            1
            for finding in self.safety_findings
            if finding.severity == SafetySeverity.WARNING.value
        )
        return f"blocked={blocked}, high={high}, warnings={warnings}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "source_path": self.source_path,
            "source": self.source_path,
            "language": self.language,
            "kind": self.kind.value,
            "line_count": self.line_count,
            "character_count": self.character_count,
            "help_text": self.help_text,
            "first_comment_block": self.first_comment_block,
            "function_signature": (
                self.function_signature.to_dict() if self.function_signature else None
            ),
            "plot_hints": [hint.to_dict() for hint in self.plot_hints],
            "safety_findings": [finding.to_dict() for finding in self.safety_findings],
            "detected_calls": list(self.detected_calls),
            "imports_or_paths": list(self.imports_or_paths),
            "safe_preview_required": self.safe_preview_required,
            "can_execute": self.can_execute,
            "metadata": dict(self.metadata),
            "executable_line_count": self.executable_line_count,
            "comment_line_count": self.comment_line_count,
            "entrypoint": self.entrypoint,
            "contains_plot_call": self.contains_plot_call,
            "safety": self.safety.to_dict() if self.safety else None,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> ScriptPreview:
        findings = tuple(
            SafetyFinding.from_dict(item)
            for item in data.get("safety_findings", ())
            if isinstance(item, Mapping)
        )
        safety_payload = data.get("safety")
        safety = (
            SafetyScanResult.from_dict(safety_payload)
            if isinstance(safety_payload, Mapping)
            else None
        )
        if not findings and safety is not None:
            findings = safety.findings
        return cls(
            id=str(data.get("id", _preview_id_from_path(str(data.get("source_path", ""))))),
            name=str(data.get("name", "")),
            source_path=str(data.get("source_path", data.get("source", ""))),
            language=str(data.get("language", ScriptLanguage.MATLAB_OCTAVE.value)),
            kind=ScriptKind(str(data.get("kind", ScriptKind.UNKNOWN.value))),
            line_count=int(data.get("line_count", 0) or 0),
            character_count=int(data.get("character_count", 0) or 0),
            help_text=str(data.get("help_text", "")),
            first_comment_block=str(data.get("first_comment_block", "")),
            function_signature=FunctionSignature.from_dict(
                data.get("function_signature")
                if isinstance(data.get("function_signature"), Mapping)
                else None
            ),
            plot_hints=tuple(
                PlotHint.from_dict(item)
                for item in data.get("plot_hints", ())
                if isinstance(item, Mapping)
            ),
            safety_findings=findings,
            detected_calls=tuple(str(item) for item in data.get("detected_calls", ())),
            imports_or_paths=tuple(str(item) for item in data.get("imports_or_paths", ())),
            safe_preview_required=bool(data.get("safe_preview_required", True)),
            can_execute=bool(data.get("can_execute", False)),
            metadata=dict(data.get("metadata", {}) or {}),
            executable_line_count=int(data.get("executable_line_count", 0) or 0),
            comment_line_count=int(data.get("comment_line_count", 0) or 0),
            entrypoint=(
                str(data["entrypoint"])
                if data.get("entrypoint") not in (None, "")
                else None
            ),
            safety=safety,
        )


MScriptPreview = ScriptPreview


def script_preview_id(source_path: str | Path) -> str:
    return _preview_id_from_path(str(source_path))


def _preview_id_from_path(source_path: str) -> str:
    stem = Path(source_path).stem if source_path else "script"
    slug = "".join(char.lower() if char.isalnum() else "-" for char in stem).strip("-")
    return f"script-{slug or 'preview'}"


def _severity_value(value: str | SafetySeverity) -> str:
    if isinstance(value, SafetySeverity):
        return value.value
    text = str(value).strip().lower()
    if text == "danger":
        return SafetySeverity.HIGH.value
    return text or SafetySeverity.WARNING.value


def _code_from_token(token: str, severity: str) -> str:
    token_slug = token.strip().casefold().replace(".", "-") or "script"
    return f"mscript-{severity}-{token_slug}"


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def finding_counts(findings: Iterable[SafetyFinding]) -> dict[str, int]:
    counts = {
        SafetySeverity.INFO.value: 0,
        SafetySeverity.WARNING.value: 0,
        SafetySeverity.HIGH.value: 0,
        SafetySeverity.BLOCKED.value: 0,
    }
    for finding in findings:
        counts[str(finding.severity)] = counts.get(str(finding.severity), 0) + 1
    return counts
