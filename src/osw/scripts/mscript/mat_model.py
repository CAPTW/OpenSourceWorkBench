"""Serializable models for MATLAB MAT-file previews."""

from __future__ import annotations

import csv
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from io import StringIO
from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticReport


class MatFileVersion(StrEnum):
    V4 = "v4"
    V5 = "v5"
    V6 = "v6"
    V7 = "v7"
    V72 = "v7.2"
    V73 = "v7.3"
    UNKNOWN = "unknown"


class MatVariableKind(StrEnum):
    NUMERIC = "numeric"
    LOGICAL = "logical"
    CHAR = "char"
    STRING = "string"
    STRUCT = "struct"
    CELL = "cell"
    SPARSE = "sparse"
    OBJECT = "object"
    UNKNOWN = "unknown"


class MatReadStatus(StrEnum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    DEPENDENCY_MISSING = "dependency_missing"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, init=False)
class MatVariableSummary:
    name: str
    kind: str
    type_name: str
    shape: tuple[int, ...]
    dtype: str
    size: int | None
    is_numeric: bool
    is_complex: bool
    is_sparse: bool
    preview: str
    min_value: float | None
    max_value: float | None
    mean_value: float | None
    source_file: str
    metadata: dict[str, Any]

    def __init__(
        self,
        name: str,
        shape: Sequence[int] | None = None,
        dtype: str = "",
        is_numeric: bool | None = None,
        *,
        kind: str | MatVariableKind = MatVariableKind.UNKNOWN,
        type_name: str = "",
        size: int | None = None,
        is_complex: bool = False,
        is_sparse: bool = False,
        preview: str = "",
        min_value: float | None = None,
        max_value: float | None = None,
        mean_value: float | None = None,
        source_file: str = "",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        resolved_kind = _kind_value(kind)
        resolved_shape = tuple(int(item) for item in (shape or ()))
        resolved_dtype = str(dtype)
        if is_numeric is None:
            is_numeric = resolved_kind == MatVariableKind.NUMERIC.value
        object.__setattr__(self, "name", str(name))
        object.__setattr__(self, "kind", resolved_kind)
        object.__setattr__(self, "type_name", str(type_name or resolved_kind))
        object.__setattr__(self, "shape", resolved_shape)
        object.__setattr__(self, "dtype", resolved_dtype)
        object.__setattr__(self, "size", _optional_int(size))
        object.__setattr__(self, "is_numeric", bool(is_numeric))
        object.__setattr__(self, "is_complex", bool(is_complex))
        object.__setattr__(self, "is_sparse", bool(is_sparse))
        object.__setattr__(self, "preview", str(preview))
        object.__setattr__(self, "min_value", _optional_float(min_value))
        object.__setattr__(self, "max_value", _optional_float(max_value))
        object.__setattr__(self, "mean_value", _optional_float(mean_value))
        object.__setattr__(self, "source_file", str(source_file))
        object.__setattr__(self, "metadata", dict(metadata or {}))

    @property
    def display_shape(self) -> str:
        if not self.shape:
            return "scalar"
        return "x".join(str(item) for item in self.shape)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "type_name": self.type_name,
            "shape": list(self.shape),
            "dtype": self.dtype,
            "size": self.size,
            "is_numeric": self.is_numeric,
            "is_complex": self.is_complex,
            "is_sparse": self.is_sparse,
            "preview": self.preview,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mean_value": self.mean_value,
            "source_file": self.source_file,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MatVariableSummary:
        return cls(
            name=str(payload.get("name", "")),
            shape=tuple(int(item) for item in payload.get("shape", ()) or ()),
            dtype=str(payload.get("dtype", "")),
            is_numeric=bool(payload.get("is_numeric", False)),
            kind=str(payload.get("kind", MatVariableKind.UNKNOWN.value)),
            type_name=str(payload.get("type_name", "")),
            size=_optional_int(payload.get("size")),
            is_complex=bool(payload.get("is_complex", False)),
            is_sparse=bool(payload.get("is_sparse", False)),
            preview=str(payload.get("preview", "")),
            min_value=_optional_float(payload.get("min_value")),
            max_value=_optional_float(payload.get("max_value")),
            mean_value=_optional_float(payload.get("mean_value")),
            source_file=str(payload.get("source_file", "")),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class MatTablePreview:
    variable_name: str
    columns: tuple[str, ...] = field(default_factory=tuple)
    rows: tuple[tuple[str, ...], ...] = field(default_factory=tuple)
    row_count: int = 0
    column_count: int = 0
    truncated: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "columns", tuple(str(item) for item in self.columns))
        object.__setattr__(
            self,
            "rows",
            tuple(tuple(str(cell) for cell in row) for row in self.rows),
        )
        object.__setattr__(self, "row_count", int(self.row_count or len(self.rows)))
        object.__setattr__(
            self,
            "column_count",
            int(self.column_count or len(self.columns)),
        )
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def title(self) -> str:
        return self.variable_name

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

    def to_dict(self) -> dict[str, Any]:
        return {
            "variable_name": self.variable_name,
            "columns": list(self.columns),
            "rows": [list(row) for row in self.rows],
            "row_count": self.row_count,
            "column_count": self.column_count,
            "truncated": self.truncated,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MatTablePreview:
        return cls(
            variable_name=str(payload.get("variable_name", "")),
            columns=tuple(str(item) for item in payload.get("columns", ()) or ()),
            rows=tuple(
                tuple(str(cell) for cell in row)
                for row in payload.get("rows", ()) or ()
            ),
            row_count=int(payload.get("row_count", 0) or 0),
            column_count=int(payload.get("column_count", 0) or 0),
            truncated=bool(payload.get("truncated", False)),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class MatFileSummary:
    source_path: str
    version: str | MatFileVersion = MatFileVersion.UNKNOWN
    variables: tuple[MatVariableSummary, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_path", str(self.source_path))
        object.__setattr__(self, "version", _version_value(self.version))
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def variable_names(self) -> tuple[str, ...]:
        return tuple(variable.name for variable in self.variables)

    def variable(self, name: str) -> MatVariableSummary:
        for variable in self.variables:
            if variable.name == name:
                return variable
        msg = f"MAT variable not found: {name}"
        raise KeyError(msg)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "version": self.version,
            "variables": [variable.to_dict() for variable in self.variables],
            "diagnostics": self.diagnostics.to_dict(),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MatFileSummary:
        return cls(
            source_path=str(payload.get("source_path", "")),
            version=str(payload.get("version", MatFileVersion.UNKNOWN.value)),
            variables=tuple(
                MatVariableSummary.from_dict(variable)
                for variable in payload.get("variables", ()) or ()
                if isinstance(variable, Mapping)
            ),
            diagnostics=DiagnosticReport.from_dict(payload.get("diagnostics", {}) or {}),
            metadata=dict(payload.get("metadata", {}) or {}),
        )


@dataclass(frozen=True)
class MatReadResult:
    status: str | MatReadStatus
    summary: MatFileSummary
    values: Mapping[str, Any] | None = field(default=None, repr=False, compare=False)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    source_path: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _status_value(self.status))
        object.__setattr__(self, "source_path", self.source_path or self.summary.source_path)
        if not self.diagnostics.messages and self.summary.diagnostics.messages:
            object.__setattr__(self, "diagnostics", self.summary.diagnostics)
        object.__setattr__(self, "values", dict(self.values or {}))

    @property
    def ok(self) -> bool:
        return self.status in {MatReadStatus.OK.value, MatReadStatus.WARNING.value}

    @property
    def file_path(self) -> Path:
        return Path(self.summary.source_path)

    @property
    def format_version(self) -> str:
        if self.summary.version == MatFileVersion.V73.value:
            return "7.3"
        return self.summary.version

    @property
    def variable_names(self) -> tuple[str, ...]:
        return self.summary.variable_names

    @property
    def variables(self) -> tuple[MatVariableSummary, ...]:
        return self.summary.variables

    @property
    def variable_summaries(self) -> tuple[MatVariableSummary, ...]:
        return self.summary.variables

    def variable(self, name: str) -> MatVariableSummary:
        return self.summary.variable(name)

    def value(self, name: str) -> Any:
        self.variable(name)
        values = self.values or {}
        if name not in values:
            msg = f"MAT variable data is unavailable for preview: {name}"
            raise KeyError(msg)
        return values[name]

    def table_preview(
        self,
        name: str,
        *,
        max_rows: int = 20,
        max_columns: int = 12,
    ) -> MatTablePreview:
        from osw.scripts.mscript.mat_reader import table_preview_from_value

        return table_preview_from_value(
            name,
            self.value(name),
            max_rows=max_rows,
            max_cols=max_columns,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "summary": self.summary.to_dict(),
            "diagnostics": self.diagnostics.to_dict(),
            "source_path": self.source_path,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MatReadResult:
        summary_payload = payload.get("summary", {})
        summary = (
            MatFileSummary.from_dict(summary_payload)
            if isinstance(summary_payload, Mapping)
            else MatFileSummary(source_path=str(payload.get("source_path", "")))
        )
        return cls(
            status=str(payload.get("status", MatReadStatus.ERROR.value)),
            summary=summary,
            diagnostics=DiagnosticReport.from_dict(payload.get("diagnostics", {}) or {}),
            source_path=str(payload.get("source_path", summary.source_path)),
        )


@dataclass(frozen=True)
class MatFilePreview:
    """Backward-compatible preview object used by older workflow code."""

    file_path: Path
    format_version: str
    variables: tuple[MatVariableSummary, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    _values: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "file_path", Path(self.file_path))
        object.__setattr__(self, "variables", tuple(self.variables))
        object.__setattr__(self, "_values", dict(self._values))

    @property
    def variable_names(self) -> tuple[str, ...]:
        return tuple(variable.name for variable in self.variables)

    def variable(self, name: str) -> MatVariableSummary:
        for variable in self.variables:
            if variable.name == name:
                return variable
        msg = f"MAT variable not found: {name}"
        raise KeyError(msg)

    def value(self, name: str) -> Any:
        self.variable(name)
        if name not in self._values:
            msg = f"MAT variable data is unavailable for preview: {name}"
            raise KeyError(msg)
        return self._values[name]

    def table_preview(
        self,
        name: str,
        *,
        max_rows: int = 20,
        max_columns: int = 12,
    ) -> MatTablePreview:
        from osw.scripts.mscript.mat_reader import table_preview_from_value

        return table_preview_from_value(
            name,
            self.value(name),
            max_rows=max_rows,
            max_cols=max_columns,
        )


@dataclass(frozen=True)
class MatCsvExportResult:
    status: str | MatReadStatus
    output_path: str
    variable_name: str
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    row_count: int = 0
    column_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _status_value(self.status))
        object.__setattr__(self, "output_path", str(self.output_path))
        object.__setattr__(self, "variable_name", str(self.variable_name))

    @property
    def ok(self) -> bool:
        return self.status == MatReadStatus.OK.value and not self.diagnostics.has_errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "output_path": self.output_path,
            "variable_name": self.variable_name,
            "diagnostics": self.diagnostics.to_dict(),
            "row_count": self.row_count,
            "column_count": self.column_count,
        }


def _kind_value(value: str | MatVariableKind) -> str:
    if isinstance(value, MatVariableKind):
        return value.value
    text = str(value or MatVariableKind.UNKNOWN.value).strip().lower()
    try:
        return MatVariableKind(text).value
    except ValueError:
        return MatVariableKind.UNKNOWN.value


def _version_value(value: str | MatFileVersion) -> str:
    if isinstance(value, MatFileVersion):
        return value.value
    text = str(value or MatFileVersion.UNKNOWN.value).strip().lower()
    aliases = {"4": "v4", "5": "v5", "6": "v6", "7": "v7", "7.2": "v7.2", "7.3": "v7.3"}
    text = aliases.get(text, text)
    try:
        return MatFileVersion(text).value
    except ValueError:
        return MatFileVersion.UNKNOWN.value


def _status_value(value: str | MatReadStatus) -> str:
    if isinstance(value, MatReadStatus):
        return value.value
    text = str(value or MatReadStatus.ERROR.value).strip().lower()
    try:
        return MatReadStatus(text).value
    except ValueError:
        return MatReadStatus.ERROR.value


def _optional_int(value: object) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _optional_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
