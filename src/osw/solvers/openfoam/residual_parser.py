"""Residual log parsing for bounded OpenFOAM template runs."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

from osw.core.diagnostics import DiagnosticReport
from osw.solvers.openfoam.model import OpenFOAMResidualSeries, OpenFOAMResidualSummary


def parse_openfoam_residuals_from_text(
    text: str,
    *,
    source_path: str | Path = "",
) -> OpenFOAMResidualSummary:
    """Parse common OpenFOAM residual log lines without requiring OpenFOAM."""

    diagnostics = DiagnosticReport()
    stripped = text.strip()
    if not stripped:
        diagnostics.add_warning(
            "openfoam-log-empty",
            "OpenFOAM log text is empty; no residuals were parsed.",
            path=source_path,
        )
        return OpenFOAMResidualSummary(diagnostics=diagnostics)

    current_time: float | None = None
    values_by_field: dict[str, list[float]] = defaultdict(list)
    initial_by_field: dict[str, list[float]] = defaultdict(list)
    iterations_by_field: dict[str, list[int]] = defaultdict(list)
    solver_iterations_by_field: dict[str, list[int]] = defaultdict(list)
    times_by_field: dict[str, list[float]] = defaultdict(list)
    global_iteration = 0
    saw_end = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        time_match = _TIME_RE.search(line)
        if time_match:
            current_time = float(time_match.group("time"))
            continue
        if _END_RE.search(line):
            saw_end = True
        if "warning" in line.lower():
            diagnostics.add_warning(
                "log-warning-detected",
                line,
                path=source_path,
            )
        if "error" in line.lower() or "fatal" in line.lower():
            diagnostics.add_error(
                "log-error-detected",
                line,
                path=source_path,
            )

        residual_match = _RESIDUAL_RE.search(line)
        if residual_match is None:
            continue
        global_iteration += 1
        field = residual_match.group("field").strip()
        initial = float(residual_match.group("initial"))
        final = float(residual_match.group("final"))
        solver_iterations = int(residual_match.group("iterations"))
        initial_by_field[field].append(initial)
        values_by_field[field].append(final)
        iterations_by_field[field].append(global_iteration)
        solver_iterations_by_field[field].append(solver_iterations)
        if current_time is not None:
            times_by_field[field].append(current_time)

    if not values_by_field:
        diagnostics.add_warning(
            "openfoam-residuals-not-found",
            "No OpenFOAM residual lines were recognized.",
            hint=(
                "Expected lines like 'Solving for Ux, Initial residual = ..., "
                "Final residual = ...'."
            ),
            path=source_path,
        )
        return OpenFOAMResidualSummary(
            diagnostics=diagnostics,
            metadata={"source_path": str(source_path) if source_path else ""},
        )

    series: list[OpenFOAMResidualSeries] = []
    final_residuals: dict[str, float] = {}
    initial_residuals: dict[str, float] = {}
    for field in sorted(values_by_field):
        values = tuple(values_by_field[field])
        final_residuals[field] = values[-1]
        initial_residuals[field] = initial_by_field[field][0]
        series.append(
            OpenFOAMResidualSeries(
                field=field,
                values=values,
                iterations=tuple(iterations_by_field[field]),
                metadata={
                    "initial_residuals": list(initial_by_field[field]),
                    "solver_iterations": list(solver_iterations_by_field[field]),
                    "times": list(times_by_field[field]),
                },
            )
        )

    converged = saw_end if saw_end else None
    diagnostics.add_info(
        "openfoam-residuals-parsed",
        f"Parsed OpenFOAM residuals for {len(series)} field(s).",
        path=source_path,
        metadata={"fields": sorted(values_by_field), "iterations": global_iteration},
    )
    return OpenFOAMResidualSummary(
        series=tuple(series),
        final_residuals=final_residuals,
        initial_residuals=initial_residuals,
        iteration_count=global_iteration,
        converged=converged,
        diagnostics=diagnostics,
        metadata={"source_path": str(source_path) if source_path else ""},
    )


def parse_openfoam_log(path: str | Path) -> OpenFOAMResidualSummary:
    source = Path(path).expanduser()
    if not source.exists():
        diagnostics = DiagnosticReport()
        diagnostics.add_error(
            "openfoam-log-missing",
            f"OpenFOAM log file does not exist: {source}",
            hint="Choose an existing log.* file or case directory.",
            path=source,
        )
        return OpenFOAMResidualSummary(diagnostics=diagnostics)
    try:
        text = source.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        diagnostics = DiagnosticReport()
        diagnostics.add_error(
            "openfoam-log-read-error",
            f"Could not read OpenFOAM log file: {exc}",
            path=source,
        )
        return OpenFOAMResidualSummary(diagnostics=diagnostics)
    return parse_openfoam_residuals_from_text(text, source_path=source)


def parse_openfoam_case_logs(case_dir: str | Path) -> OpenFOAMResidualSummary:
    root = Path(case_dir).expanduser()
    if not root.exists() or not root.is_dir():
        diagnostics = DiagnosticReport()
        diagnostics.add_error(
            "openfoam-case-missing",
            f"OpenFOAM case directory does not exist: {root}",
            hint="Generate a template case or choose an existing case directory.",
            path=root,
        )
        return OpenFOAMResidualSummary(diagnostics=diagnostics)

    logs = sorted(root.glob("log.*"))
    if not logs:
        logs = sorted(root.glob("*.log"))
    if not logs:
        stdout_path = root / "stdout.txt"
        if stdout_path.exists():
            logs = [stdout_path]
    if not logs:
        diagnostics = DiagnosticReport()
        diagnostics.add_warning(
            "openfoam-log-missing",
            "No OpenFOAM log.* files were found in the case directory.",
            hint="Run a solver explicitly or choose a directory containing log files.",
            path=root,
        )
        return OpenFOAMResidualSummary(diagnostics=diagnostics)

    combined = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in logs)
    summary = parse_openfoam_residuals_from_text(combined, source_path=root)
    summary.diagnostics.add_info(
        "openfoam-log-files",
        f"Read {len(logs)} OpenFOAM log file(s).",
        path=root,
        metadata={"logs": [str(path) for path in logs]},
    )
    return summary


_TIME_RE = re.compile(r"^Time\s*=\s*(?P<time>[-+0-9.eE]+)")
_END_RE = re.compile(r"^End\s*$", re.IGNORECASE)
_RESIDUAL_RE = re.compile(
    r"Solving for (?P<field>[^,]+),\s*"
    r"Initial residual = (?P<initial>[-+0-9.eE]+),\s*"
    r"Final residual = (?P<final>[-+0-9.eE]+),\s*"
    r"No Iterations (?P<iterations>[0-9]+)"
)
