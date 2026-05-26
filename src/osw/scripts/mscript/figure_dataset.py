"""FigureDataset contracts for script, post-processing, and report previews."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport


class FigureFormat(StrEnum):
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    JPG = "jpg"
    CSV = "csv"
    UNKNOWN = "unknown"


SUPPORTED_FIGURE_FORMATS = (
    FigureFormat.PNG.value,
    FigureFormat.SVG.value,
    FigureFormat.PDF.value,
    FigureFormat.JPG.value,
)
SUPPORTED_FIGURE_ARTIFACT_FORMATS = (
    *SUPPORTED_FIGURE_FORMATS,
    FigureFormat.CSV.value,
)


class FigureDatasetError(RuntimeError):
    """Raised when figure dataset input cannot be loaded safely."""


@dataclass(frozen=True)
class AxisRecord:
    axis_id: str
    title: str = ""
    xlabel: str = ""
    ylabel: str = ""
    zlabel: str = ""
    xlim: tuple[float, float] | None = None
    ylim: tuple[float, float] | None = None
    zlim: tuple[float, float] | None = None
    legend: tuple[str, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "legend", tuple(str(item) for item in self.legend))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def display_label(self) -> str:
        labels = [self.xlabel, self.ylabel, self.zlabel]
        label_text = " / ".join(label for label in labels if label)
        return label_text or self.title or self.axis_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "axis_id": self.axis_id,
            "title": self.title,
            "xlabel": self.xlabel,
            "ylabel": self.ylabel,
            "zlabel": self.zlabel,
            "xlim": list(self.xlim) if self.xlim else None,
            "ylim": list(self.ylim) if self.ylim else None,
            "zlim": list(self.zlim) if self.zlim else None,
            "legend": list(self.legend),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AxisRecord:
        return cls(
            axis_id=str(payload.get("axis_id", "")),
            title=str(payload.get("title", "")),
            xlabel=str(payload.get("xlabel", "")),
            ylabel=str(payload.get("ylabel", "")),
            zlabel=str(payload.get("zlabel", "")),
            xlim=_optional_float_pair(payload.get("xlim")),
            ylim=_optional_float_pair(payload.get("ylim")),
            zlim=_optional_float_pair(payload.get("zlim")),
            legend=tuple(str(item) for item in payload.get("legend", ())),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class WorkspaceVariableSummary:
    name: str
    type_name: str
    shape: tuple[int, ...] = field(default_factory=tuple)
    dtype: str = ""
    size: int | None = None
    preview: str = ""
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "shape", tuple(int(item) for item in self.shape))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type_name": self.type_name,
            "shape": list(self.shape),
            "dtype": self.dtype,
            "size": self.size,
            "preview": self.preview,
            "source": self.source,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> WorkspaceVariableSummary:
        return cls(
            name=str(payload.get("name", "")),
            type_name=str(payload.get("type_name", "")),
            shape=tuple(int(item) for item in payload.get("shape", ()) or ()),
            dtype=str(payload.get("dtype", "")),
            size=_optional_int(payload.get("size")),
            preview=str(payload.get("preview", "")),
            source=str(payload.get("source", "")),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class FigureRecord:
    figure_id: str
    title: str = ""
    image_path: Path | None = None
    source_script: str = ""
    source_run_id: str = ""
    vector_path: Path | None = None
    pdf_path: Path | None = None
    thumbnail_path: Path | None = None
    data_path: Path | None = None
    format: str | FigureFormat = FigureFormat.UNKNOWN
    axes: tuple[AxisRecord, ...] = field(default_factory=tuple)
    raw_plot_data: Mapping[str, Any] | None = None
    reproducible_python: str | None = None
    created_at: str = ""
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        image_path = _optional_path(self.image_path)
        vector_path = _optional_path(self.vector_path)
        pdf_path = _optional_path(self.pdf_path)
        thumbnail_path = _optional_path(self.thumbnail_path)
        data_path = _optional_path(self.data_path)
        resolved_format = _format_value(self.format)
        if resolved_format == FigureFormat.UNKNOWN.value:
            resolved_format = _format_from_paths(
                image_path,
                vector_path,
                pdf_path,
                data_path,
            )
        object.__setattr__(self, "image_path", image_path)
        object.__setattr__(self, "vector_path", vector_path)
        object.__setattr__(self, "pdf_path", pdf_path)
        object.__setattr__(self, "thumbnail_path", thumbnail_path)
        object.__setattr__(self, "data_path", data_path)
        object.__setattr__(self, "format", resolved_format)
        object.__setattr__(
            self,
            "axes",
            tuple(_coerce_axis_record(axis, index) for index, axis in enumerate(self.axes, 1)),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def image_format(self) -> str:
        return str(self.format)

    @property
    def primary_path(self) -> Path | None:
        return self.image_path or self.vector_path or self.pdf_path or self.data_path

    def load_image_bytes(self) -> bytes:
        path = self.image_path or self.vector_path
        if path is None:
            msg = f"Figure record has no image/vector path: {self.figure_id}"
            raise FigureDatasetError(msg)
        if self.image_format not in {
            FigureFormat.PNG.value,
            FigureFormat.SVG.value,
            FigureFormat.JPG.value,
        }:
            msg = f"Unsupported figure image format: {path.suffix or '<none>'}"
            raise FigureDatasetError(msg)
        if not path.exists():
            msg = f"Figure image does not exist: {path}"
            raise FigureDatasetError(msg)
        return path.read_bytes()

    def report_placeholder(self) -> str:
        path = self.primary_path or Path("")
        return f"{self.figure_id}: {self.title} [{self.image_format}] at {path}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "figure_id": self.figure_id,
            "title": self.title,
            "source_script": self.source_script,
            "source_run_id": self.source_run_id,
            "image_path": _path_text(self.image_path),
            "vector_path": _path_text(self.vector_path),
            "pdf_path": _path_text(self.pdf_path),
            "thumbnail_path": _path_text(self.thumbnail_path),
            "data_path": _path_text(self.data_path),
            "format": self.image_format,
            "axes": [axis.to_dict() for axis in self.axes],
            "raw_plot_data": self.raw_plot_data,
            "reproducible_python": self.reproducible_python,
            "created_at": self.created_at,
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FigureRecord:
        return cls(
            figure_id=str(payload.get("figure_id", "")),
            title=str(payload.get("title", "")),
            source_script=str(payload.get("source_script", "")),
            source_run_id=str(payload.get("source_run_id", "")),
            image_path=_optional_path(payload.get("image_path")),
            vector_path=_optional_path(payload.get("vector_path")),
            pdf_path=_optional_path(payload.get("pdf_path")),
            thumbnail_path=_optional_path(payload.get("thumbnail_path")),
            data_path=_optional_path(payload.get("data_path")),
            format=str(payload.get("format", FigureFormat.UNKNOWN.value)),
            axes=tuple(
                AxisRecord.from_dict(axis)
                if isinstance(axis, Mapping)
                else _coerce_axis_record(axis, index)
                for index, axis in enumerate(payload.get("axes", ()), 1)
            ),
            raw_plot_data=payload.get("raw_plot_data"),
            reproducible_python=_optional_str(payload.get("reproducible_python")),
            created_at=str(payload.get("created_at", "")),
            diagnostics=DiagnosticReport.from_dict(payload.get("diagnostics", {}) or {}),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class FigureDataset:
    dataset_id: str
    figures: tuple[FigureRecord, ...] = field(default_factory=tuple)
    source: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)
    source_file: str = ""
    source_run_id: str = ""
    engine: str = "unknown"
    workspace_variables: tuple[WorkspaceVariableSummary, ...] = field(default_factory=tuple)
    stdout: str = ""
    stderr: str = ""
    warnings: tuple[str, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    artifacts: tuple[RunArtifact, ...] = field(default_factory=tuple)
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "figures", tuple(self.figures))
        object.__setattr__(self, "notes", tuple(str(note) for note in self.notes))
        object.__setattr__(
            self,
            "workspace_variables",
            tuple(self.workspace_variables),
        )
        object.__setattr__(self, "warnings", tuple(str(item) for item in self.warnings))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "metadata", dict(self.metadata))

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
            source_file=self.source_file,
            source_run_id=self.source_run_id,
            engine=self.engine,
            workspace_variables=self.workspace_variables,
            stdout=self.stdout,
            stderr=self.stderr,
            warnings=self.warnings,
            diagnostics=self.diagnostics,
            artifacts=self.artifacts,
            created_at=self.created_at,
            metadata=self.metadata,
        )

    def report_placeholders(self) -> tuple[str, ...]:
        if not self.figures:
            return ("No figure datasets registered yet.",)
        return tuple(record.report_placeholder() for record in self.figures)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source": self.source,
            "notes": list(self.notes),
            "source_file": self.source_file,
            "source_run_id": self.source_run_id,
            "engine": self.engine,
            "figures": [record.to_dict() for record in self.figures],
            "workspace_variables": [
                variable.to_dict() for variable in self.workspace_variables
            ],
            "stdout": self.stdout,
            "stderr": self.stderr,
            "warnings": list(self.warnings),
            "diagnostics": self.diagnostics.to_dict(),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> FigureDataset:
        return cls(
            dataset_id=str(payload.get("dataset_id", "")),
            figures=tuple(
                FigureRecord.from_dict(record)
                for record in payload.get("figures", ())
                if isinstance(record, Mapping)
            ),
            source=str(payload.get("source", "")),
            notes=tuple(str(note) for note in payload.get("notes", ())),
            source_file=str(payload.get("source_file", "")),
            source_run_id=str(payload.get("source_run_id", "")),
            engine=str(payload.get("engine", "unknown")),
            workspace_variables=tuple(
                WorkspaceVariableSummary.from_dict(variable)
                for variable in payload.get("workspace_variables", ())
                if isinstance(variable, Mapping)
            ),
            stdout=str(payload.get("stdout", "")),
            stderr=str(payload.get("stderr", "")),
            warnings=tuple(str(item) for item in payload.get("warnings", ())),
            diagnostics=DiagnosticReport.from_dict(payload.get("diagnostics", {}) or {}),
            artifacts=tuple(
                RunArtifact.from_dict(artifact)
                for artifact in payload.get("artifacts", ())
                if isinstance(artifact, Mapping)
            ),
            created_at=str(payload.get("created_at", "")),
            metadata=dict(payload.get("metadata", {}) or {}),
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
        title_map = titles or {}
        seen_ids: set[str] = set()
        records: list[FigureRecord] = []
        for index, path in enumerate(paths, start=1):
            image_path = Path(path)
            figure_id = _unique_figure_id(image_path, index, seen_ids)
            records.append(
                FigureRecord(
                    figure_id=figure_id,
                    title=title_map.get(image_path.stem, _title_from_stem(image_path.stem)),
                    image_path=(
                        image_path
                        if _is_raster(image_path) or _suffix(image_path) == FigureFormat.SVG.value
                        else None
                    ),
                    vector_path=(
                        image_path
                        if _suffix(image_path) == FigureFormat.SVG.value
                        else None
                    ),
                    pdf_path=image_path if _suffix(image_path) == FigureFormat.PDF.value else None,
                    format=classify_extension(image_path),
                )
            )
        return cls(dataset_id=dataset_id, figures=tuple(records), source=source)


def classify_extension(path: str | Path) -> FigureFormat:
    suffix = _suffix(path)
    if suffix == "jpeg":
        return FigureFormat.JPG
    try:
        return FigureFormat(suffix)
    except ValueError:
        return FigureFormat.UNKNOWN


def is_supported_figure_path(path: str | Path) -> bool:
    return classify_extension(path).value in SUPPORTED_FIGURE_FORMATS


def is_supported_figure_artifact_path(path: str | Path) -> bool:
    return classify_extension(path).value in SUPPORTED_FIGURE_ARTIFACT_FORMATS


def new_dataset_id(prefix: str = "figures") -> str:
    return f"{prefix}-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"


def _format_from_paths(
    image_path: Path | None,
    vector_path: Path | None,
    pdf_path: Path | None,
    data_path: Path | None,
) -> str:
    for path in (image_path, vector_path, pdf_path, data_path):
        if path is not None:
            return classify_extension(path).value
    return FigureFormat.UNKNOWN.value


def _format_value(value: str | FigureFormat) -> str:
    if isinstance(value, FigureFormat):
        return value.value
    text = str(value).strip().lower()
    if text == "jpeg":
        return FigureFormat.JPG.value
    if text in {item.value for item in FigureFormat}:
        return text
    return FigureFormat.UNKNOWN.value


def _is_raster(path: str | Path) -> bool:
    return classify_extension(path) in {FigureFormat.PNG, FigureFormat.JPG}


def _suffix(path: str | Path) -> str:
    return Path(path).suffix.lower().lstrip(".")


def _title_from_stem(stem: str) -> str:
    return stem.replace("_", " ").replace("-", " ").strip() or "figure"


def _unique_figure_id(path: Path, index: int, seen_ids: set[str]) -> str:
    base_id = path.stem or f"figure-{index}"
    figure_id = base_id
    if figure_id in seen_ids:
        figure_id = f"{base_id}-{path.suffix.lower().lstrip('.')}"
    seen_ids.add(figure_id)
    return figure_id


def _coerce_axis_record(value: object, index: int) -> AxisRecord:
    if isinstance(value, AxisRecord):
        return value
    if isinstance(value, Mapping):
        return AxisRecord.from_dict(value)
    return AxisRecord(axis_id=f"axis-{index}", title=str(value))


def _optional_float_pair(value: object) -> tuple[float, float] | None:
    if value in (None, ""):
        return None
    try:
        first, second = value  # type: ignore[misc]
    except (TypeError, ValueError):
        return None
    try:
        return float(first), float(second)
    except (TypeError, ValueError):
        return None


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _optional_path(value: object) -> Path | None:
    if value in (None, ""):
        return None
    return Path(str(value))


def _path_text(path: Path | None) -> str:
    return str(path) if path is not None else ""


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
