"""Minimal CalculiX result parser for v0.1 summaries."""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path

from osw.core.result_dataset import (
    ResultDataset,
    ResultField,
    ResultRow,
    ResultSummaryValue,
)

DISPLACEMENT_COMPONENTS = ("U1", "U2", "U3", "MAGNITUDE")
STRESS_COMPONENTS = ("SXX", "SYY", "SZZ", "SXY", "SYZ", "SXZ", "VON_MISES")


class CalculixResultParserError(ValueError):
    """Raised when CalculiX result data cannot be parsed."""


class CalculixFrdParserUnavailable(NotImplementedError):
    """Raised when only complex FRD data is available for this v0.1 parser."""


def parse_calculix_results(
    *,
    dat_path: str | Path | None = None,
    frd_path: str | Path | None = None,
) -> ResultDataset:
    """Parse available CalculiX result summaries, preferring the text `.dat` file."""

    warnings: list[str] = []
    if dat_path is not None:
        dataset = parse_calculix_dat(dat_path)
        if frd_path is not None:
            warnings.append(
                f"FRD parsing is not implemented for v0.1; ignored {Path(frd_path).name}."
            )
        return replace(dataset, warnings=(*dataset.warnings, *warnings))
    if frd_path is not None:
        msg = "FRD parsing is not implemented for v0.1; provide a CalculiX .dat file."
        raise CalculixFrdParserUnavailable(msg)
    raise CalculixResultParserError("A CalculiX .dat or .frd result path is required.")


def parse_calculix_dat(path: str | Path) -> ResultDataset:
    """Parse a small, table-oriented subset of CalculiX `.dat` result output."""

    source = Path(path).expanduser().resolve()
    try:
        lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        msg = f"Could not read CalculiX .dat file {source}: {exc}"
        raise CalculixResultParserError(msg) from exc

    displacement_rows: list[ResultRow] = []
    stress_rows: list[ResultRow] = []
    warnings: list[str] = []
    section: str | None = None

    for line_number, raw_line in enumerate(lines, start=1):
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

        if section == "displacement":
            row = _parse_displacement_row(line, line_number, warnings)
            if row is not None:
                displacement_rows.append(row)
        elif section == "stress":
            row = _parse_stress_row(line, line_number, warnings)
            if row is not None:
                stress_rows.append(row)

    fields = (
        ResultField(
            name="displacement",
            location="node",
            components=DISPLACEMENT_COMPONENTS,
            rows=tuple(displacement_rows),
            unit="m",
        ),
        ResultField(
            name="stress",
            location="element",
            components=STRESS_COMPONENTS,
            rows=tuple(stress_rows),
            unit="Pa",
        ),
    )
    summaries = (
        ResultSummaryValue(
            name="displacement_magnitude",
            value=_max_component(displacement_rows, "MAGNITUDE"),
            unit="m",
            source_field="displacement",
        ),
        ResultSummaryValue(
            name="von_mises_stress",
            value=_max_component(stress_rows, "VON_MISES"),
            unit="Pa",
            source_field="stress",
        ),
    )
    if not displacement_rows:
        warnings.append("No displacement rows were parsed from the CalculiX .dat file.")
    if not stress_rows:
        warnings.append("No stress rows were parsed from the CalculiX .dat file.")

    return ResultDataset(
        dataset_id=source.stem,
        source=str(source),
        solver="CalculiX",
        analysis_type="linear_static",
        fields=fields,
        summaries=summaries,
        warnings=tuple(warnings),
    )


def _parse_displacement_row(
    line: str,
    line_number: int,
    warnings: list[str],
) -> ResultRow | None:
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
    return ResultRow(
        entity_id=entity_id,
        values={"U1": u1, "U2": u2, "U3": u3, "MAGNITUDE": magnitude},
    )


def _parse_stress_row(
    line: str,
    line_number: int,
    warnings: list[str],
) -> ResultRow | None:
    parts = line.split()
    if len(parts) < 8:
        warnings.append(
            f"Could not parse stress row {line_number}: expected element and 7 values."
        )
        return None
    try:
        entity_id = int(parts[0])
        values = [float(item) for item in parts[1:8]]
    except ValueError:
        warnings.append(f"Could not parse stress row {line_number}: {line}")
        return None
    return ResultRow(entity_id=entity_id, values=dict(zip(STRESS_COMPONENTS, values, strict=True)))


def _max_component(rows: list[ResultRow], component: str) -> float:
    if not rows:
        return 0.0
    return max(abs(row.values.get(component, 0.0)) for row in rows)
