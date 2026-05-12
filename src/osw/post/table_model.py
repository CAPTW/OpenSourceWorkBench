"""Small table preview model for result and script data exports."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path


@dataclass(frozen=True)
class TablePreview:
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    title: str = ""
    source: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(self.columns))
        object.__setattr__(self, "rows", tuple(tuple(row) for row in self.rows))
        object.__setattr__(self, "notes", tuple(self.notes))

    def to_csv_text(self) -> str:
        output = StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(self.columns)
        writer.writerows(self.rows)
        return output.getvalue()

    def export_csv(self, output_path: str | Path) -> Path:
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.to_csv_text(), encoding="utf-8")
        return target
