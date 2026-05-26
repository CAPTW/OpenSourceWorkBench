"""Best-effort MATLAB/Octave `.m` text parsing helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .script_model import FunctionSignature, PlotHint, ScriptKind

PLOT_COMMANDS = (
    "plot",
    "scatter",
    "bar",
    "histogram",
    "semilogx",
    "semilogy",
    "loglog",
    "subplot",
    "tiledlayout",
    "nexttile",
    "figure",
    "hold",
    "grid",
    "title",
    "xlabel",
    "ylabel",
    "legend",
    "contour",
    "surf",
    "mesh",
    "imagesc",
)

_FUNCTION_SIGNATURE = re.compile(
    r"^\s*function"
    r"(?:\s+(?P<outputs>\[[^\]]*\]|[A-Za-z_]\w*)\s*=\s*)?"
    r"\s*(?P<name>[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)?)"
    r"(?:\s*\((?P<inputs>[^)]*)\))?",
    re.IGNORECASE,
)
_FUNCTION_CALL = re.compile(r"(?<!\.)\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_PLOT_PATTERN = re.compile(
    r"(?<!\.)\b("
    + "|".join(re.escape(command) for command in PLOT_COMMANDS)
    + r")\b(?:\s*\(|\s*(?:;|$)|\s+\S+)",
    re.IGNORECASE,
)


def strip_mscript_comment(line: str) -> str:
    """Remove MATLAB `%` comments while preserving `%` inside single quotes."""

    in_single_quote = False
    index = 0
    while index < len(line):
        char = line[index]
        if char == "'":
            next_char = line[index + 1] if index + 1 < len(line) else ""
            if in_single_quote and next_char == "'":
                index += 2
                continue
            in_single_quote = not in_single_quote
        elif char == "%" and not in_single_quote:
            return line[:index]
        index += 1
    return line


def classify_mscript(text: str) -> ScriptKind:
    meaningful = list(_meaningful_lines(text))
    if not meaningful:
        return ScriptKind.UNKNOWN
    if any(line.strip().lower().startswith("classdef") for _line_no, line in meaningful):
        return ScriptKind.CLASSDEF
    first = meaningful[0][1].strip().lower()
    if first.startswith("function"):
        return ScriptKind.FUNCTION
    return ScriptKind.SCRIPT


def extract_function_signature(text: str) -> FunctionSignature | None:
    for line_no, code in _meaningful_lines(text):
        match = _FUNCTION_SIGNATURE.match(code)
        if not match:
            if code.strip():
                return None
            continue
        return FunctionSignature(
            name=match.group("name") or "",
            inputs=tuple(_split_names(match.group("inputs") or "")),
            outputs=tuple(_split_names((match.group("outputs") or "").strip("[]"))),
            raw_signature=code.strip(),
            line_no=line_no,
        )
    return None


def extract_first_comment_block(text: str) -> str:
    block: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            if block:
                break
            continue
        if not stripped.startswith("%"):
            break
        block.append(_clean_comment_line(stripped))
    return "\n".join(block).strip()


def extract_help_text(text: str) -> str:
    signature = extract_function_signature(text)
    lines = text.splitlines()
    if signature is not None:
        block: list[str] = []
        for line in lines[signature.line_no:]:
            stripped = line.strip()
            if not stripped:
                if block:
                    break
                continue
            if not stripped.startswith("%"):
                break
            block.append(_clean_comment_line(stripped))
        if block:
            return "\n".join(block).strip()
    return extract_first_comment_block(text)


def extract_plot_hints(text: str) -> list[PlotHint]:
    hints: list[PlotHint] = []
    for line_no, code in _code_lines(text):
        masked = mask_string_literals(code)
        for match in _PLOT_PATTERN.finditer(masked):
            hints.append(
                PlotHint(
                    command=match.group(1).lower(),
                    line_no=line_no,
                    context=code.strip(),
                )
            )
    return hints


def extract_detected_calls(text: str) -> tuple[str, ...]:
    calls: list[str] = []
    for _line_no, code in _code_lines(text):
        masked = mask_string_literals(code)
        for match in _FUNCTION_CALL.finditer(masked):
            calls.append(match.group(1).lower())
    return tuple(dict.fromkeys(calls))


def extract_imports_or_paths(text: str) -> tuple[str, ...]:
    matches: list[str] = []
    for _line_no, code in _code_lines(text):
        lowered = code.lower()
        if any(token in lowered for token in ("addpath", "rmpath", "cd(", "path(")):
            matches.append(code.strip())
    return tuple(matches)


def mask_string_literals(code: str) -> str:
    result: list[str] = []
    in_single_quote = False
    index = 0
    while index < len(code):
        char = code[index]
        if char == "'":
            next_char = code[index + 1] if index + 1 < len(code) else ""
            result.append(" ")
            if in_single_quote and next_char == "'":
                result.append(" ")
                index += 2
                continue
            in_single_quote = not in_single_quote
        elif in_single_quote:
            result.append(" ")
        else:
            result.append(char)
        index += 1
    return "".join(result)


def _meaningful_lines(text: str) -> Iterable[tuple[int, str]]:
    for line_no, code in _code_lines(text):
        stripped = code.strip()
        if stripped:
            yield line_no, stripped


def _code_lines(text: str) -> Iterable[tuple[int, str]]:
    for line_no, line in enumerate(text.splitlines(), start=1):
        yield line_no, strip_mscript_comment(line)


def _split_names(raw: str) -> list[str]:
    if not raw.strip():
        return []
    normalized = raw.replace(",", " ")
    return [part.strip() for part in normalized.split() if part.strip() and part.strip() != "~"]


def _clean_comment_line(line: str) -> str:
    return line.lstrip("%").strip()
