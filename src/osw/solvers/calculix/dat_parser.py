"""Best-effort CalculiX ``.dat`` summary parser.

This parser is intentionally small. It extracts reportable scalar summaries from
text artifacts that already exist on disk; it never runs ``ccx``.
"""

from __future__ import annotations

import math
import re
from pathlib import Path

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.solvers.log_parser import GenericLogParser, LogEvent

from .results import (
    CalculiXDisplacementSummary,
    CalculiXFieldSummary,
    CalculiXParsedResults,
    CalculiXResultStatus,
    CalculiXStressSummary,
)

DISPLACEMENT_COMPONENTS = ("U1", "U2", "U3", "MAGNITUDE")
STRESS_COMPONENTS = ("SXX", "SYY", "SZZ", "SXY", "SYZ", "SXZ", "VON_MISES")
_NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?"
_MAX_DISPLACEMENT_RE = re.compile(
    rf"max(?:imum)?\s+displacement(?:\s+magnitude)?\s*[:=]\s*({_NUMBER})"
    rf"(?:\s+(?:node|node_id)\s*[:=]?\s*(\d+))?",
    re.IGNORECASE,
)
_MAX_STRESS_RE = re.compile(
    rf"max(?:imum)?\s+(?:von\s+mises\s+)?stress\s*[:=]\s*({_NUMBER})"
    rf"(?:\s+(?:element|element_id)\s*[:=]?\s*(\d+))?",
    re.IGNORECASE,
)
_MAX_VON_MISES_RE = re.compile(
    rf"max(?:imum)?\s+von\s+mises(?:\s+stress)?\s*[:=]\s*({_NUMBER})"
    rf"(?:\s+(?:element|element_id)\s*[:=]?\s*(\d+))?",
    re.IGNORECASE,
)


def parse_calculix_dat(path: str | Path) -> CalculiXParsedResults:
    """Parse a CalculiX ``.dat`` file into a summary result object."""

    source = Path(path).expanduser()
    diagnostics = DiagnosticReport()
    if not source.exists():
        diagnostics.add_error(
            "calculix-dat-missing",
            f"CalculiX DAT artifact was not found: {source}",
            hint="Parse an existing CalculiX run directory or provide the .dat path.",
            path=source,
        )
        return CalculiXParsedResults(
            dat_path=source,
            status=CalculiXResultStatus.MISSING_ARTIFACTS,
            diagnostics=diagnostics,
        )
    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        diagnostics.add_error(
            "calculix-dat-read-error",
            f"Could not read CalculiX DAT artifact: {exc}",
            path=source,
        )
        return CalculiXParsedResults(
            dat_path=source,
            status=CalculiXResultStatus.PARSE_ERROR,
            diagnostics=diagnostics,
        )
    return parse_dat_text(text, source_path=str(source))


def parse_dat_text(text: str, source_path: str | None = None) -> CalculiXParsedResults:
    """Parse DAT text, handling simplified summary lines and small tables."""

    diagnostics = DiagnosticReport()
    source = Path(source_path) if source_path else None
    if not text.strip():
        diagnostics.add_warning(
            "calculix-dat-empty",
            "CalculiX DAT artifact is empty.",
            hint="Inspect the run log to confirm whether CalculiX produced result output.",
            path=source or "",
        )
        return CalculiXParsedResults(
            dat_path=source,
            status=CalculiXResultStatus.PARTIAL,
            diagnostics=diagnostics,
            artifacts=_artifact_tuple(source, "dat_result", "dat"),
        )

    log_events = tuple(extract_warnings_errors_from_dat(text))
    _add_log_event_diagnostics(diagnostics, log_events, source)
    for warning in _section_parse_warnings(text):
        diagnostics.add_warning(
            "calculix-dat-row-unparsed",
            warning,
            path=source or "",
        )
    displacement = extract_displacement_summary_from_dat(text)
    stress = extract_stress_summary_from_dat(text)
    fields = _field_summaries(displacement, stress)

    if displacement is None:
        diagnostics.add_warning(
            "calculix-displacement-summary-missing",
            "No max displacement summary was found in the CalculiX DAT artifact.",
            hint="Use a deck with displacement output requests or parse a richer result artifact.",
            path=source or "",
        )
    if stress is None:
        diagnostics.add_warning(
            "calculix-stress-summary-missing",
            "No max von Mises stress summary was found in the CalculiX DAT artifact.",
            hint="Use a deck with stress output requests or parse a richer result artifact.",
            path=source or "",
        )

    status = (
        CalculiXResultStatus.PARSED
        if displacement is not None or stress is not None
        else CalculiXResultStatus.PARTIAL
    )
    return CalculiXParsedResults(
        dat_path=source,
        status=status,
        displacement_summary=displacement,
        stress_summary=stress,
        field_summaries=fields,
        log_events=log_events,
        artifacts=_artifact_tuple(source, "dat_result", "dat"),
        diagnostics=diagnostics,
    )


def extract_displacement_summary_from_dat(text: str) -> CalculiXDisplacementSummary | None:
    """Extract maximum displacement from explicit lines or small displacement tables."""

    match = _MAX_DISPLACEMENT_RE.search(text)
    if match:
        return CalculiXDisplacementSummary(
            max_magnitude=float(match.group(1)),
            max_node_id=_optional_int(match.group(2)),
            unit="m",
            metadata={"source": "dat_summary_line"},
        )
    rows, _warnings = _parse_section_rows(text, "displacement")
    if not rows:
        return None
    max_row = max(rows, key=lambda item: abs(float(item["MAGNITUDE"])))
    return CalculiXDisplacementSummary(
        max_magnitude=abs(float(max_row["MAGNITUDE"])),
        max_node_id=int(max_row["entity_id"]),
        components=(
            float(max_row["U1"]),
            float(max_row["U2"]),
            float(max_row["U3"]),
        ),
        unit="m",
        metadata={"source": "dat_table"},
    )


def extract_stress_summary_from_dat(text: str) -> CalculiXStressSummary | None:
    """Extract maximum von Mises stress from explicit lines or small stress tables."""

    match = _MAX_VON_MISES_RE.search(text) or _MAX_STRESS_RE.search(text)
    if match:
        return CalculiXStressSummary(
            max_von_mises=float(match.group(1)),
            max_element_id=_optional_int(match.group(2)),
            unit="Pa",
            metadata={"source": "dat_summary_line"},
        )
    rows, _warnings = _parse_section_rows(text, "stress")
    if not rows:
        return None
    max_row = max(rows, key=lambda item: abs(float(item["VON_MISES"])))
    return CalculiXStressSummary(
        max_von_mises=abs(float(max_row["VON_MISES"])),
        max_element_id=int(max_row["entity_id"]),
        unit="Pa",
        metadata={"source": "dat_table"},
    )


def extract_warnings_errors_from_dat(text: str) -> list[LogEvent]:
    """Return generic warning/error events found in DAT text."""

    return GenericLogParser().parse(text)


def _parse_section_rows(text: str, section_name: str) -> tuple[list[dict[str, float]], list[str]]:
    section: str | None = None
    rows: list[dict[str, float]] = []
    warnings: list[str] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("DISPLACEMENTS") or upper.startswith("DISPLACEMENT"):
            section = "displacement"
            continue
        if upper.startswith("STRESSES") or upper.startswith("STRESS"):
            section = "stress"
            continue
        if upper.startswith("NODE") or upper.startswith("ELEMENT"):
            continue
        if section != section_name:
            continue
        if section_name == "displacement":
            row = _parse_displacement_row(line, line_number, warnings)
        else:
            row = _parse_stress_row(line, line_number, warnings)
        if row is not None:
            rows.append(row)
    return rows, warnings


def _section_parse_warnings(text: str) -> tuple[str, ...]:
    warnings: list[str] = []
    for section_name in ("displacement", "stress"):
        _rows, section_warnings = _parse_section_rows(text, section_name)
        warnings.extend(section_warnings)
    return tuple(warnings)


def _parse_displacement_row(
    line: str,
    line_number: int,
    warnings: list[str],
) -> dict[str, float] | None:
    parts = line.split()
    if len(parts) < 4:
        warnings.append(f"Could not parse displacement row {line_number}: expected node U1 U2 U3.")
        return None
    try:
        entity_id = int(parts[0])
        u1, u2, u3 = (float(parts[1]), float(parts[2]), float(parts[3]))
    except ValueError:
        warnings.append(f"Could not parse displacement row {line_number}: {line}")
        return None
    magnitude = math.sqrt(u1 * u1 + u2 * u2 + u3 * u3)
    return {
        "entity_id": float(entity_id),
        "U1": u1,
        "U2": u2,
        "U3": u3,
        "MAGNITUDE": magnitude,
    }


def _parse_stress_row(
    line: str,
    line_number: int,
    warnings: list[str],
) -> dict[str, float] | None:
    parts = line.split()
    if len(parts) < 8:
        warnings.append(f"Could not parse stress row {line_number}: expected element and 7 values.")
        return None
    try:
        entity_id = int(parts[0])
        values = [float(item) for item in parts[1:8]]
    except ValueError:
        warnings.append(f"Could not parse stress row {line_number}: {line}")
        return None
    return {"entity_id": float(entity_id), **dict(zip(STRESS_COMPONENTS, values, strict=True))}


def _field_summaries(
    displacement: CalculiXDisplacementSummary | None,
    stress: CalculiXStressSummary | None,
) -> tuple[CalculiXFieldSummary, ...]:
    fields: list[CalculiXFieldSummary] = []
    if displacement is not None and displacement.max_magnitude is not None:
        fields.append(
            CalculiXFieldSummary(
                name="displacement_magnitude",
                component_names=DISPLACEMENT_COMPONENTS,
                location="node",
                max_value=displacement.max_magnitude,
                max_entity_id=displacement.max_node_id,
                unit=displacement.unit,
            )
        )
    if stress is not None and stress.max_von_mises is not None:
        fields.append(
            CalculiXFieldSummary(
                name="von_mises_stress",
                component_names=("VON_MISES",),
                location="element",
                max_value=stress.max_von_mises,
                max_entity_id=stress.max_element_id,
                unit=stress.unit,
            )
        )
    return tuple(fields)


def _add_log_event_diagnostics(
    diagnostics: DiagnosticReport,
    events: tuple[LogEvent, ...],
    source: Path | None,
) -> None:
    for event in events:
        if event.severity.value == "warning":
            diagnostics.add_warning(
                "log-warning-detected",
                event.message,
                path=source or "",
                metadata={"line_no": event.line_no},
            )
        elif event.severity.value == "error":
            diagnostics.add_error(
                "log-error-detected",
                event.message,
                path=source or "",
                metadata={"line_no": event.line_no},
            )


def _artifact_tuple(path: Path | None, role: str, fmt: str) -> tuple[RunArtifact, ...]:
    if path is None:
        return ()
    return (RunArtifact(path, role, f"CalculiX {fmt.upper()} result artifact.", format=fmt),)


def _optional_int(value: str | None) -> int | None:
    return int(value) if value not in (None, "") else None


__all__ = [
    "DISPLACEMENT_COMPONENTS",
    "STRESS_COMPONENTS",
    "extract_displacement_summary_from_dat",
    "extract_stress_summary_from_dat",
    "extract_warnings_errors_from_dat",
    "parse_calculix_dat",
    "parse_dat_text",
]
