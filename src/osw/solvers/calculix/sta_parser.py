"""Minimal CalculiX ``.sta`` status parser."""

from __future__ import annotations

import re
from pathlib import Path

from osw.solvers.log_parser import GenericLogParser

from .results import CalculiXStatusSummary

_NUMBER_RE = re.compile(r"[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?")


def parse_calculix_sta(path: str | Path) -> CalculiXStatusSummary:
    """Parse a CalculiX status file without executing any solver."""

    source = Path(path).expanduser()
    if not source.exists():
        return CalculiXStatusSummary(
            completed=None,
            errors=(f"CalculiX STA artifact was not found: {source}",),
            metadata={"path": str(source), "missing": True},
        )
    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return CalculiXStatusSummary(
            completed=None,
            errors=(f"Could not read CalculiX STA artifact: {exc}",),
            metadata={"path": str(source), "read_error": True},
        )
    summary = parse_sta_text(text)
    summary.metadata.setdefault("path", str(source))
    return summary


def parse_sta_text(text: str) -> CalculiXStatusSummary:
    """Return step/increment and completion summary from STA text."""

    if not text.strip():
        return CalculiXStatusSummary(
            completed=None,
            warnings=("CalculiX STA artifact is empty.",),
            metadata={"empty": True},
        )

    last_step: int | None = None
    last_increment: int | None = None
    increment_count = 0
    for line in text.splitlines():
        parsed = _parse_step_increment(line)
        if parsed is None:
            continue
        last_step, last_increment = parsed
        increment_count += 1

    events = GenericLogParser().parse(text)
    warnings = tuple(event.message for event in events if event.severity.value == "warning")
    errors = tuple(event.message for event in events if event.severity.value == "error")
    lowered = text.casefold()
    if any(token in lowered for token in ("completed", "complete", "job finished")):
        completed: bool | None = True
    elif any(token in lowered for token in ("error", "failed", "fatal")):
        completed = False
    else:
        completed = None

    return CalculiXStatusSummary(
        completed=completed,
        increments=increment_count,
        last_step=last_step,
        last_increment=last_increment,
        warnings=warnings,
        errors=errors,
    )


def _parse_step_increment(line: str) -> tuple[int, int] | None:
    lowered = line.casefold()
    numbers = [int(float(item)) for item in _NUMBER_RE.findall(line)]
    if len(numbers) >= 2 and "step" in lowered and "inc" in lowered:
        return numbers[0], numbers[1]
    if len(numbers) >= 2 and "increment" in lowered:
        return numbers[0], numbers[1]
    if len(numbers) >= 2 and line.strip()[:1].isdigit():
        return numbers[0], numbers[1]
    return None


__all__ = ["parse_calculix_sta", "parse_sta_text"]
