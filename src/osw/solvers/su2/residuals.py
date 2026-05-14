"""Minimal SU2 residual history parsing."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO


@dataclass(frozen=True)
class Su2ResidualPoint:
    iteration: int
    values: dict[str, float]

    def to_dict(self) -> dict[str, float | int]:
        return {"iteration": self.iteration, **self.values}


@dataclass(frozen=True)
class Su2ResidualSeries:
    points: tuple[Su2ResidualPoint, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def fields(self) -> tuple[str, ...]:
        if not self.points:
            return ()
        return tuple(self.points[0].values)

    def to_dict(self) -> dict[str, object]:
        return {
            "fields": list(self.fields),
            "points": [point.to_dict() for point in self.points],
            "warnings": list(self.warnings),
        }


class Su2ResidualParser:
    """Parse SU2 history CSV files or simple pipe-delimited console tables."""

    def parse_text(self, text: str) -> Su2ResidualSeries:
        csv_series = self._parse_csv(text)
        if csv_series.points:
            return csv_series

        pipe_series = self._parse_pipe_table(text)
        if pipe_series.points:
            return pipe_series

        return Su2ResidualSeries(
            warnings=("No SU2 residual history rows were found in the provided text.",)
        )

    def _parse_csv(self, text: str) -> Su2ResidualSeries:
        reader = csv.DictReader(StringIO(text.strip()))
        if not reader.fieldnames:
            return Su2ResidualSeries()
        if not any(
            field and field.strip().lower() in {"iter", "iteration"}
            for field in reader.fieldnames
        ):
            return Su2ResidualSeries()

        points: list[Su2ResidualPoint] = []
        warnings: list[str] = []
        for row_number, row in enumerate(reader, start=2):
            point = _point_from_mapping(row)
            if point is None:
                warnings.append(f"Skipped unreadable SU2 residual row {row_number}.")
                continue
            points.append(point)
        return Su2ResidualSeries(tuple(points), tuple(warnings))

    def _parse_pipe_table(self, text: str) -> Su2ResidualSeries:
        rows = []
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or not stripped.endswith("|"):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if not cells or all(set(cell) <= {"-"} for cell in cells if cell):
                continue
            rows.append(cells)

        if not rows:
            return Su2ResidualSeries()
        header = rows[0]
        if not header or header[0].lower() not in {"iter", "iteration"}:
            return Su2ResidualSeries()

        points: list[Su2ResidualPoint] = []
        warnings: list[str] = []
        for row_number, cells in enumerate(rows[1:], start=2):
            if len(cells) != len(header):
                warnings.append(f"Skipped unreadable SU2 residual row {row_number}.")
                continue
            point = _point_from_mapping(dict(zip(header, cells, strict=True)))
            if point is None:
                warnings.append(f"Skipped unreadable SU2 residual row {row_number}.")
                continue
            points.append(point)
        return Su2ResidualSeries(tuple(points), tuple(warnings))


def _point_from_mapping(row: dict[str, str]) -> Su2ResidualPoint | None:
    iteration_key = next(
        (key for key in row if key and key.strip().lower() in {"iter", "iteration"}),
        None,
    )
    if iteration_key is None:
        return None
    try:
        iteration = int(float(row[iteration_key]))
    except (TypeError, ValueError):
        return None

    values: dict[str, float] = {}
    for key, value in row.items():
        if key == iteration_key or key is None or key == "":
            continue
        try:
            values[key.strip()] = float(value)
        except (TypeError, ValueError):
            continue
    if not values:
        return None
    return Su2ResidualPoint(iteration=iteration, values=values)
