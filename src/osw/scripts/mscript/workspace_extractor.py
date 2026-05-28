"""Extract FigureDataset and workspace summaries from explicit run artifacts."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticReport

from .figure_dataset import (
    FigureDataset,
    WorkspaceVariableSummary,
    is_supported_figure_path,
)


@dataclass(frozen=True)
class WorkspaceSummaryResult:
    variables: tuple[WorkspaceVariableSummary, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)

    def __post_init__(self) -> None:
        object.__setattr__(self, "variables", tuple(self.variables))


def extract_figure_paths(workspace: str | Path) -> tuple[Path, ...]:
    workspace_path = Path(workspace).expanduser().resolve()
    if not workspace_path.exists() or not workspace_path.is_dir():
        return ()
    return tuple(
        path
        for path in sorted(workspace_path.rglob("*"))
        if path.is_file() and is_supported_figure_path(path)
    )


def extract_figure_dataset(
    workspace: str | Path,
    *,
    dataset_id: str = "workspace-figures",
    source: str | None = None,
) -> FigureDataset:
    workspace_path = Path(workspace).expanduser().resolve()
    return FigureDataset.from_image_paths(
        extract_figure_paths(workspace_path),
        dataset_id=dataset_id,
        source=source or str(workspace_path),
    )


def extract_workspace_summary_from_artifacts(
    paths: Iterable[str | Path],
) -> tuple[WorkspaceVariableSummary, ...]:
    return extract_workspace_summary(paths).variables


def mat_summary_to_workspace_variables(summary: object) -> tuple[WorkspaceVariableSummary, ...]:
    from .mat_reader import mat_summary_to_workspace_variables as _convert

    return _convert(summary)


def extract_workspace_summary(paths: Iterable[str | Path]) -> WorkspaceSummaryResult:
    diagnostics = DiagnosticReport()
    variables: list[WorkspaceVariableSummary] = []
    for raw_path in paths:
        path = Path(raw_path)
        if not path.exists():
            diagnostics.add_warning(
                "workspace-artifact-missing",
                f"Workspace summary artifact is missing: {path}",
                hint="Regenerate the run or remove the stale summary reference.",
                path=path,
            )
            continue
        try:
            if path.suffix.lower() == ".csv":
                variables.append(summarize_csv(path))
            elif path.suffix.lower() == ".json" and path.name in {
                "workspace.json",
                "variables.json",
                "workspace_summary.json",
            }:
                variables.extend(summarize_json_variables(path))
        except (OSError, UnicodeDecodeError, csv.Error, json.JSONDecodeError, TypeError) as exc:
            diagnostics.add_warning(
                "workspace-summary-unreadable",
                f"Could not summarize workspace artifact: {path.name}",
                hint=str(exc),
                path=path,
            )
    return WorkspaceSummaryResult(tuple(variables), diagnostics)


def summarize_csv(path: str | Path, *, max_preview_rows: int = 3) -> WorkspaceVariableSummary:
    source = Path(path)
    with source.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, [])
        rows = []
        row_count = 0
        for row in reader:
            row_count += 1
            if len(rows) < max_preview_rows:
                rows.append(row)
    column_count = len(header) if header else (len(rows[0]) if rows else 0)
    preview_rows = [",".join(header)] if header else []
    preview_rows.extend(",".join(row) for row in rows)
    return WorkspaceVariableSummary(
        name=source.stem,
        type_name="table",
        shape=(row_count, column_count),
        dtype="csv",
        size=source.stat().st_size,
        preview="\n".join(preview_rows),
        source=str(source),
        metadata={"columns": header, "preview_row_count": len(rows)},
    )


def summarize_json_variables(path: str | Path) -> tuple[WorkspaceVariableSummary, ...]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        variables_payload = payload.get("variables", payload)
    else:
        variables_payload = payload
    variables: list[WorkspaceVariableSummary] = []
    if isinstance(variables_payload, Mapping):
        for name, value in variables_payload.items():
            variables.append(_summary_from_json_value(str(name), value, source))
    elif isinstance(variables_payload, list):
        for index, value in enumerate(variables_payload, start=1):
            if isinstance(value, Mapping) and "name" in value:
                variables.append(_summary_from_mapping(value, source))
            else:
                variables.append(_summary_from_json_value(f"variable_{index}", value, source))
    return tuple(variables)


def _summary_from_mapping(
    payload: Mapping[str, Any],
    source: Path,
) -> WorkspaceVariableSummary:
    shape = payload.get("shape", ())
    if isinstance(shape, str):
        parsed_shape = tuple(
            int(part) for part in shape.replace("x", ",").split(",") if part.strip().isdigit()
        )
    else:
        parsed_shape = tuple(int(item) for item in shape or ())
    return WorkspaceVariableSummary(
        name=str(payload.get("name", source.stem)),
        type_name=str(payload.get("type_name", payload.get("type", "unknown"))),
        shape=parsed_shape,
        dtype=str(payload.get("dtype", "")),
        size=_optional_int(payload.get("size")),
        preview=str(payload.get("preview", "")),
        source=str(payload.get("source", source)),
        metadata={
            str(key): value
            for key, value in payload.items()
            if key
            not in {
                "name",
                "type_name",
                "type",
                "shape",
                "dtype",
                "size",
                "preview",
                "source",
            }
        },
    )


def _summary_from_json_value(
    name: str,
    value: Any,
    source: Path,
) -> WorkspaceVariableSummary:
    shape = _shape_of(value)
    return WorkspaceVariableSummary(
        name=name,
        type_name=type(value).__name__,
        shape=shape,
        dtype=_dtype_of(value),
        size=_size_of(value),
        preview=_preview_value(value),
        source=str(source),
    )


def _shape_of(value: Any) -> tuple[int, ...]:
    if isinstance(value, list):
        if value and all(isinstance(item, list) for item in value):
            return (len(value), max(len(item) for item in value))
        return (len(value),)
    if isinstance(value, dict):
        return (len(value),)
    return ()


def _dtype_of(value: Any) -> str:
    if isinstance(value, list) and value:
        return type(value[0]).__name__
    return type(value).__name__


def _size_of(value: Any) -> int | None:
    if isinstance(value, list | dict | str):
        return len(value)
    return None


def _preview_value(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=True) if isinstance(value, list | dict) else str(value)
    return text if len(text) <= 200 else f"{text[:197]}..."


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
