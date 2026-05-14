"""Minimal OpenFOAM residual parser interface."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OpenFoamResidualPoint:
    """One parsed OpenFOAM linear-solver residual entry."""

    iteration: int
    field: str
    initial_residual: float
    final_residual: float | None = None
    solver_iterations: int | None = None
    time: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "field": self.field,
            "initial_residual": self.initial_residual,
            "final_residual": self.final_residual,
            "solver_iterations": self.solver_iterations,
            "time": self.time,
        }


@dataclass(frozen=True)
class OpenFoamResidualSeries:
    """Report-friendly collection of parsed residual points."""

    points: tuple[OpenFoamResidualPoint, ...]
    warnings: tuple[str, ...] = ()

    @property
    def fields(self) -> tuple[str, ...]:
        seen: dict[str, None] = {}
        for point in self.points:
            seen.setdefault(point.field, None)
        return tuple(seen)

    def to_dict(self) -> dict[str, Any]:
        return {
            "fields": list(self.fields),
            "points": [point.to_dict() for point in self.points],
            "warnings": list(self.warnings),
        }


class OpenFoamResidualParser:
    """Parse common residual log lines without depending on OpenFOAM itself."""

    def parse_text(self, text: str) -> OpenFoamResidualSeries:
        points: list[OpenFoamResidualPoint] = []
        current_time: float | None = None
        for line in text.splitlines():
            time_match = _TIME_RE.search(line)
            if time_match:
                current_time = float(time_match.group("time"))
                continue

            residual_match = _RESIDUAL_RE.search(line)
            if not residual_match:
                continue
            points.append(
                OpenFoamResidualPoint(
                    iteration=len(points) + 1,
                    field=residual_match.group("field").strip(),
                    initial_residual=float(residual_match.group("initial")),
                    final_residual=float(residual_match.group("final")),
                    solver_iterations=int(residual_match.group("iterations")),
                    time=current_time,
                )
            )

        warnings: tuple[str, ...] = ()
        if text.strip() and not points:
            warnings = ("No OpenFOAM residual lines were recognized.",)
        return OpenFoamResidualSeries(points=tuple(points), warnings=warnings)


_TIME_RE = re.compile(r"^Time\s*=\s*(?P<time>[-+0-9.eE]+)")
_RESIDUAL_RE = re.compile(
    r"Solving for (?P<field>[^,]+),\s*"
    r"Initial residual = (?P<initial>[-+0-9.eE]+),\s*"
    r"Final residual = (?P<final>[-+0-9.eE]+),\s*"
    r"No Iterations (?P<iterations>[0-9]+)"
)
