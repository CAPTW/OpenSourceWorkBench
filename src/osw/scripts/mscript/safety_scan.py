"""Heuristic safety scan for preview-only MATLAB/Octave `.m` imports."""

from __future__ import annotations

import re

from .parser import mask_string_literals, strip_mscript_comment
from .script_model import SafetyFinding, SafetyScanResult, SafetySeverity

_FUNCTION_PATTERN = re.compile(r"(?<!\.)\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_SHELL_ESCAPE_PATTERN = re.compile(r"^\s*!")
_PY_USAGE_PATTERN = re.compile(r"\b(py\.|python\s*\()", re.IGNORECASE)
_JAVA_USAGE_PATTERN = re.compile(r"\b(java\.|java\w*\s*\()", re.IGNORECASE)

# Out of scope MATLAB/Octave application workflow markers are blocked in preview.
_BLOCKED_TOKENS = {
    "simulink": (
        "unsupported-simulink",
        "Simulink workflows are out of scope for OSW v0.1 preview import.",
        "Export data to a supported script or data format before importing.",
    ),
    "open_system": (
        "unsupported-simulink",
        "open_system indicates a Simulink or app workflow that OSW v0.1 does not support.",
        "Do not import Simulink models or app workflows through the `.m` preview path.",
    ),
    "sim": (
        "unsupported-simulink",
        "sim may execute a Simulink model and is out of scope for this preview importer.",
        "Keep Simulink execution outside OSW v0.1.",
    ),
}

_HIGH_TOKENS = {
    "system": ("external-command", "May launch shell commands."),
    "unix": ("external-command", "May launch shell commands."),
    "dos": ("external-command", "May launch shell commands."),
    "perl": ("external-command", "May launch external Perl code."),
    "delete": ("filesystem-destructive", "May remove files."),
    "rmdir": ("filesystem-destructive", "May remove directories."),
    "webread": ("network-access", "May access the network."),
    "webwrite": ("network-access", "May access the network."),
    "websave": ("network-access", "May download network content."),
    "urlread": ("network-access", "May access the network."),
    "urlwrite": ("network-access", "May write network content to disk."),
    "ftp": ("network-access", "May access remote FTP resources."),
    "tcpclient": ("network-access", "May open network connections."),
    "udpport": ("network-access", "May open network connections."),
    "serialport": ("external-device-access", "May access local serial devices."),
    "web": ("network-access", "May open web resources."),
    "eval": ("dynamic-execution", "May dynamically execute code."),
    "evalin": ("dynamic-execution", "May dynamically execute code in another workspace."),
    "feval": ("dynamic-execution", "May dynamically dispatch executable code."),
    "run": ("dynamic-execution", "May execute another script."),
    "source": ("dynamic-execution", "May execute another script."),
}

_WARNING_TOKENS = {
    "movefile": ("filesystem-mutation", "May move or rename local files."),
    "copyfile": ("filesystem-mutation", "May copy local files."),
    "mkdir": ("filesystem-mutation", "May create directories."),
    "fopen": ("filesystem-access", "May read or write local files."),
    "fclose": ("filesystem-access", "May close a file handle opened by the script."),
    "fdelete": ("filesystem-access", "May remove a file through legacy syntax."),
    "fprintf": ("filesystem-access", "May write text to a file handle."),
    "save": ("filesystem-access", "May write workspace variables to disk."),
    "load": ("filesystem-access", "May read files into the workspace."),
    "diary": ("filesystem-access", "May write command output to disk."),
    "tempname": ("filesystem-access", "May create temporary file paths."),
    "cd": ("path-environment-mutation", "May change the working directory."),
    "addpath": ("path-environment-mutation", "May mutate the MATLAB/Octave path."),
    "rmpath": ("path-environment-mutation", "May mutate the MATLAB/Octave path."),
    "path": ("path-environment-mutation", "May read or mutate the MATLAB/Octave path."),
    "restoredefaultpath": (
        "path-environment-mutation",
        "May reset the MATLAB/Octave path.",
    ),
    "getenv": ("environment-access", "May read environment variables."),
    "setenv": ("environment-access", "May mutate environment variables."),
    "python": ("foreign-runtime-bridge", "May bridge into Python from MATLAB/Octave."),
    "java": ("foreign-runtime-bridge", "May bridge into Java from MATLAB/Octave."),
}


def scan_mscript_text(text: str, *, source: str = "<memory>") -> SafetyScanResult:
    findings: list[SafetyFinding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        code = strip_mscript_comment(line).strip()
        if not code:
            continue

        lowered_code = code.lower()
        masked = mask_string_literals(code)
        masked_lower = masked.lower()

        if _SHELL_ESCAPE_PATTERN.search(masked):
            findings.append(
                _finding(
                    token="!",
                    line_no=line_number,
                    severity=SafetySeverity.HIGH,
                    code="external-command",
                    message="Shell escape may launch external commands.",
                    hint="Review manually before any future execution path.",
                    context=code,
                )
            )

        if ".slx" in lowered_code or ".mlapp" in lowered_code:
            findings.append(
                _finding(
                    token=".slx" if ".slx" in lowered_code else ".mlapp",
                    line_no=line_number,
                    severity=SafetySeverity.BLOCKED,
                    code="unsupported-simulink-app",
                    message="Simulink `.slx` and MATLAB app `.mlapp` workflows are out of scope.",
                    hint="Use exported data or a plain `.m` preview instead.",
                    context=code,
                )
            )

        if _PY_USAGE_PATTERN.search(masked):
            finding_code, message = _WARNING_TOKENS["python"]
            findings.append(
                _finding(
                    token="python",
                    line_no=line_number,
                    severity=SafetySeverity.WARNING,
                    code=finding_code,
                    message=message,
                    hint="Python bridge calls are previewed only and are not executed.",
                    context=code,
                )
            )
        if _JAVA_USAGE_PATTERN.search(masked):
            finding_code, message = _WARNING_TOKENS["java"]
            findings.append(
                _finding(
                    token="java",
                    line_no=line_number,
                    severity=SafetySeverity.WARNING,
                    code=finding_code,
                    message=message,
                    hint="Java bridge calls are previewed only and are not executed.",
                    context=code,
                )
            )

        seen_tokens: set[str] = set()
        for function_name in _called_functions(masked_lower):
            if function_name in seen_tokens:
                continue
            seen_tokens.add(function_name)
            if function_name in _BLOCKED_TOKENS:
                finding_code, message, hint = _BLOCKED_TOKENS[function_name]
                findings.append(
                    _finding(
                        token=function_name,
                        line_no=line_number,
                        severity=SafetySeverity.BLOCKED,
                        code=finding_code,
                        message=message,
                        hint=hint,
                        context=code,
                    )
                )
            elif function_name in _HIGH_TOKENS:
                finding_code, message = _HIGH_TOKENS[function_name]
                findings.append(
                    _finding(
                        token=function_name,
                        line_no=line_number,
                        severity=SafetySeverity.HIGH,
                        code=finding_code,
                        message=message,
                        hint="Review manually before any future execution path.",
                        context=code,
                    )
                )
            elif function_name in _WARNING_TOKENS:
                finding_code, message = _WARNING_TOKENS[function_name]
                findings.append(
                    _finding(
                        token=function_name,
                        line_no=line_number,
                        severity=SafetySeverity.WARNING,
                        code=finding_code,
                        message=message,
                        hint="Preview import records this behavior but does not execute it.",
                        context=code,
                    )
                )

        if "simulink" in masked_lower and "simulink" not in seen_tokens:
            finding_code, message, hint = _BLOCKED_TOKENS["simulink"]
            findings.append(
                _finding(
                    token="simulink",
                    line_no=line_number,
                    severity=SafetySeverity.BLOCKED,
                    code=finding_code,
                    message=message,
                    hint=hint,
                    context=code,
                )
            )
    return SafetyScanResult(source=source, findings=tuple(findings))


def strip_comment_for_scan(line: str) -> str:
    return strip_mscript_comment(line)


def _called_functions(code: str) -> list[str]:
    return [match.group(1).lower() for match in _FUNCTION_PATTERN.finditer(code)]


def _finding(
    *,
    token: str,
    line_no: int,
    severity: SafetySeverity,
    code: str,
    message: str,
    hint: str,
    context: str,
) -> SafetyFinding:
    return SafetyFinding(
        function=token,
        token=token,
        line=line_no,
        line_no=line_no,
        severity=severity,
        code=code,
        message=message,
        hint=hint,
        snippet=context,
        context=context,
    )


__all__ = ["scan_mscript_text", "strip_comment_for_scan", "strip_mscript_comment"]
