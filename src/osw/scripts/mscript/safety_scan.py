"""Heuristic safety scan for preview-only `.m` imports."""

from __future__ import annotations

import re
from collections.abc import Iterable

from .script_model import SafetyFinding, SafetyScanResult

DANGEROUS_FUNCTIONS = {
    "system": "May launch shell commands.",
    "unix": "May launch shell commands.",
    "delete": "May remove files.",
    "rmdir": "May remove directories.",
    "webread": "May access the network.",
    "urlread": "May access the network.",
}
RISKY_WARNING_FUNCTIONS = {
    "fopen": "May read or write local files.",
    "fdelete": "May remove local files.",
}
_FUNCTION_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_SHELL_ESCAPE_PATTERN = re.compile(r"^\s*!")


def scan_mscript_text(text: str, *, source: str = "<memory>") -> SafetyScanResult:
    findings: list[SafetyFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        code = strip_mscript_comment(line).strip()
        if not code:
            continue
        if _SHELL_ESCAPE_PATTERN.search(code):
            findings.append(
                SafetyFinding(
                    function="!",
                    line=line_number,
                    severity="danger",
                    message="Shell escape may launch external commands.",
                    snippet=code,
                )
            )
        for function_name in _called_functions(code):
            lowered = function_name.lower()
            if lowered in DANGEROUS_FUNCTIONS:
                findings.append(
                    SafetyFinding(
                        function=lowered,
                        line=line_number,
                        severity="danger",
                        message=DANGEROUS_FUNCTIONS[lowered],
                        snippet=code,
                    )
                )
            elif lowered in RISKY_WARNING_FUNCTIONS:
                findings.append(
                    SafetyFinding(
                        function=lowered,
                        line=line_number,
                        severity="warning",
                        message=RISKY_WARNING_FUNCTIONS[lowered],
                        snippet=code,
                    )
                )
    return SafetyScanResult(source=source, findings=tuple(findings))


def strip_mscript_comment(line: str) -> str:
    """Remove line comments while preserving percent characters inside strings."""

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


def _called_functions(code: str) -> Iterable[str]:
    return (match.group(1) for match in _FUNCTION_PATTERN.finditer(code))
