"""FigureDataset contracts for M-script and post-processing previews."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SUPPORTED_FIGURE_FORMATS = ("png", "svg")


class FigureDatasetError(RuntimeError):
    """Raised when figure dataset input cannot be loaded safely."""


@dataclass(frozen=True)
class FigureRecord:
    figure_id: str
    title: str
    image_path: Path
    axes: tuple[str, ...] = field(default_factory=tuple)
    raw_plot_data: Mapping[str, Any] | None = None
    reproducible_python: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "image_path", Path(self.image_path))
        object.__setattr__(self, "axes", tuple(self.axes))

    @property
    def image_format(self) -> str:
        return self.image_path.suffix.lower().lstrip(".")

    def load_image_bytes(self) -> bytes:
        if self.image_format not in SUPPORTED_FIGURE_FORMATS:
            msg = f"Unsupported figure image format: {self.image_path.suffix or '<none>'}"
            raise FigureDatasetError(msg)
        if not self.image_path.exists():
            msg = f"Figure image does not exist: {self.image_path}"
            raise FigureDatasetError(msg)
        return self.image_path.read_bytes()

    def report_placeholder(self) -> str:
        return f"{self.figure_id}: {self.title} [{self.image_format}] at {self.image_path}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "figure_id": self.figure_id,
            "title": self.title,
            "image_path": str(self.image_path),
            "axes": list(self.axes),
            "raw_plot_data": self.raw_plot_data,
            "reproducible_python": self.reproducible_python,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FigureRecord:
        return cls(
            figure_id=str(payload.get("figure_id", "")),
            title=str(payload.get("title", "")),
            image_path=Path(str(payload.get("image_path", ""))),
            axes=tuple(str(axis) for axis in payload.get("axes", ())),
            raw_plot_data=payload.get("raw_plot_data"),
            reproducible_python=_optional_str(payload.get("reproducible_python")),
        )


@dataclass(frozen=True)
class FigureDataset:
    dataset_id: str
    figures: tuple[FigureRecord, ...] = field(default_factory=tuple)
    source: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "figures", tuple(self.figures))
        object.__setattr__(self, "notes", tuple(self.notes))

    def __len__(self) -> int:
        return len(self.figures)

    @property
    def formats(self) -> tuple[str, ...]:
        seen: list[str] = []
        for record in self.figures:
            image_format = record.image_format
            if image_format not in seen:
                seen.append(image_format)
        return tuple(seen)

    def with_figure(self, record: FigureRecord) -> FigureDataset:
        return FigureDataset(
            dataset_id=self.dataset_id,
            figures=(*self.figures, record),
            source=self.source,
            notes=self.notes,
        )

    def report_placeholders(self) -> tuple[str, ...]:
        if not self.figures:
            return ("No figure datasets registered yet.",)
        return tuple(record.report_placeholder() for record in self.figures)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "figures": [record.to_dict() for record in self.figures],
            "source": self.source,
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FigureDataset:
        return cls(
            dataset_id=str(payload.get("dataset_id", "")),
            figures=tuple(
                FigureRecord.from_dict(record)
                for record in payload.get("figures", ())
            ),
            source=str(payload.get("source", "")),
            notes=tuple(str(note) for note in payload.get("notes", ())),
        )

    @classmethod
    def from_image_paths(
        cls,
        paths: Sequence[str | Path],
        *,
        dataset_id: str = "figures",
        source: str = "",
        titles: Mapping[str, str] | None = None,
    ) -> FigureDataset:
        records = []
        title_map = titles or {}
        seen_ids: set[str] = set()
        for index, path in enumerate(paths, start=1):
            image_path = Path(path)
            base_id = image_path.stem or f"figure-{index}"
            figure_id = base_id
            if figure_id in seen_ids:
                figure_id = f"{base_id}-{image_path.suffix.lower().lstrip('.')}"
            seen_ids.add(figure_id)
            records.append(
                FigureRecord(
                    figure_id=figure_id,
                    title=title_map.get(base_id, _title_from_stem(image_path.stem)),
                    image_path=image_path,
                )
            )
        return cls(dataset_id=dataset_id, figures=tuple(records), source=source)


def is_supported_figure_path(path: str | Path) -> bool:
    return Path(path).suffix.lower().lstrip(".") in SUPPORTED_FIGURE_FORMATS


def _title_from_stem(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").strip() or "figure"


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
