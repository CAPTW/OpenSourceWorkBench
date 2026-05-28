"""Preview-only MATLAB MAT data reader."""

from __future__ import annotations

import csv
import importlib.util
import json
import math
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticReport
from osw.core.project_schema import ScriptRef

from .figure_dataset import FigureDataset, WorkspaceVariableSummary, new_dataset_id
from .mat_model import (
    MatCsvExportResult,
    MatFilePreview,
    MatFileSummary,
    MatFileVersion,
    MatReadResult,
    MatReadStatus,
    MatTablePreview,
    MatVariableKind,
    MatVariableSummary,
)

_AUTO = object()
_HDF5_SIGNATURE = b"\x89HDF\r\n\x1a\n"
_MATLAB_INTERNAL_NAMES = {"__header__", "__version__", "__globals__"}


class MatReaderError(RuntimeError):
    """Raised when a MAT preview variable cannot be accessed."""


class MatReader:
    """Read `.mat` files into metadata and small preview tables.

    The reader never executes MATLAB/Octave code. SciPy is imported lazily for
    MATLAB v4 through v7.2 files. MAT v7.3 is HDF5-backed and uses optional
    `hdf5storage` or `h5py` only when available.
    """

    def __init__(
        self,
        *,
        scipy_loadmat: Callable[..., Mapping[str, Any]] | None | object = _AUTO,
        hdf5storage_loadmat: Callable[..., Mapping[str, Any]] | None | object = _AUTO,
        h5py_module: object | None | object = _AUTO,
    ) -> None:
        self.scipy_loadmat = _resolve_scipy_loadmat() if scipy_loadmat is _AUTO else scipy_loadmat
        self.hdf5storage_loadmat = (
            _resolve_hdf5storage_loadmat()
            if hdf5storage_loadmat is _AUTO
            else hdf5storage_loadmat
        )
        self.h5py_module = _resolve_h5py() if h5py_module is _AUTO else h5py_module

    def read(
        self,
        path: str | Path,
        *,
        variable_names: Sequence[str] | None = None,
        max_preview_rows: int = 20,
        max_preview_cols: int = 12,
    ) -> MatReadResult:
        return read_mat_file(
            path,
            variable_names=variable_names,
            max_preview_rows=max_preview_rows,
            max_preview_cols=max_preview_cols,
            scipy_loadmat=self.scipy_loadmat,
            hdf5storage_loadmat=self.hdf5storage_loadmat,
            h5py_module=self.h5py_module,
        )


def is_mat_path(path: str | Path) -> bool:
    return Path(path).suffix.lower() == ".mat"


def scipy_available() -> bool:
    return importlib.util.find_spec("scipy") is not None


def hdf5_mat_reader_available() -> bool:
    return (
        importlib.util.find_spec("hdf5storage") is not None
        or importlib.util.find_spec("h5py") is not None
    )


def is_hdf5_mat_v73(path: str | Path) -> bool:
    mat_path = Path(path)
    try:
        return mat_path.read_bytes()[:8] == _HDF5_SIGNATURE
    except OSError:
        return False


def detect_mat_version(path: str | Path) -> MatFileVersion:
    mat_path = Path(path)
    if not is_mat_path(mat_path) or not mat_path.exists():
        return MatFileVersion.UNKNOWN
    try:
        header = mat_path.read_bytes()[:128]
    except OSError:
        return MatFileVersion.UNKNOWN
    if header.startswith(_HDF5_SIGNATURE):
        return MatFileVersion.V73
    if header.startswith(b"MATLAB 5.0 MAT-file"):
        return MatFileVersion.V7
    if _looks_like_v4_header(header):
        return MatFileVersion.V4
    return MatFileVersion.UNKNOWN


def mat_reader_capabilities() -> dict[str, Any]:
    return {
        "formats": ["v4", "v5", "v6", "v7", "v7.2", "v7.3"],
        "scipy_loadmat": scipy_available(),
        "hdf5storage": importlib.util.find_spec("hdf5storage") is not None,
        "h5py": importlib.util.find_spec("h5py") is not None,
        "executes_code": False,
    }


def read_mat_summary(path: str | Path) -> MatFileSummary:
    return read_mat_file(path).summary


def read_mat_file(
    path: str | Path,
    variable_names: Sequence[str] | None = None,
    *,
    max_preview_rows: int = 20,
    max_preview_cols: int = 12,
    scipy_loadmat: Callable[..., Mapping[str, Any]] | None | object = _AUTO,
    hdf5storage_loadmat: Callable[..., Mapping[str, Any]] | None | object = _AUTO,
    h5py_module: object | None | object = _AUTO,
) -> MatReadResult:
    mat_path = Path(path).expanduser()
    diagnostics = DiagnosticReport()
    if not is_mat_path(mat_path):
        diagnostics.add_error(
            "mat-invalid-extension",
            "Only .mat files can be previewed by the MAT reader.",
            hint="Choose a MATLAB MAT data file with the .mat extension.",
            path=mat_path,
        )
        return _empty_result(mat_path, MatReadStatus.ERROR, diagnostics)
    if not mat_path.exists():
        diagnostics.add_error(
            "mat-file-missing",
            f"MAT file does not exist: {mat_path}",
            hint="Check the path and try again.",
            path=mat_path,
        )
        return _empty_result(mat_path, MatReadStatus.ERROR, diagnostics)

    mat_path = mat_path.resolve()
    version = detect_mat_version(mat_path)
    if version == MatFileVersion.V73:
        return _read_v73(
            mat_path,
            diagnostics,
            variable_names=variable_names,
            max_preview_rows=max_preview_rows,
            max_preview_cols=max_preview_cols,
            hdf5storage_loadmat=(
                _resolve_hdf5storage_loadmat()
                if hdf5storage_loadmat is _AUTO
                else hdf5storage_loadmat
            ),
            h5py_module=_resolve_h5py() if h5py_module is _AUTO else h5py_module,
        )

    header = _safe_header(mat_path)
    if len(header) < 20:
        diagnostics.add_error(
            "mat-file-corrupt",
            "MAT file is too small to contain a valid MATLAB MAT payload.",
            hint="Regenerate or re-export the MAT file.",
            path=mat_path,
        )
        return _empty_result(mat_path, MatReadStatus.ERROR, diagnostics, version=version)

    active_loadmat = _resolve_scipy_loadmat() if scipy_loadmat is _AUTO else scipy_loadmat
    if active_loadmat is None:
        diagnostics.add_error(
            "mat-scipy-missing",
            "SciPy is required to preview MATLAB MAT v4-v7.2 files.",
            hint="Install scipy, for example: python -m pip install -e .[mscript]",
            path=mat_path,
        )
        return _empty_result(
            mat_path,
            MatReadStatus.DEPENDENCY_MISSING,
            diagnostics,
            version=version,
        )

    try:
        payload = dict(
            active_loadmat(
                str(mat_path),
                squeeze_me=False,
                struct_as_record=False,
            )
        )
    except Exception as exc:
        diagnostics.add_error(
            "mat-load-failed",
            f"Could not read MAT file: {exc}",
            hint="Verify that the file is a supported MATLAB MAT v4-v7.2 file.",
            path=mat_path,
        )
        return _empty_result(mat_path, MatReadStatus.ERROR, diagnostics, version=version)
    return _result_from_payload(
        mat_path,
        version,
        payload,
        diagnostics,
        variable_names=variable_names,
        max_preview_rows=max_preview_rows,
        max_preview_cols=max_preview_cols,
    )


def variable_summary_from_value(
    name: str,
    value: Any,
    source_path: str | Path | None = None,
) -> MatVariableSummary:
    shape = _shape_of(value)
    dtype = _dtype_of(value)
    type_name = _type_name_of(value)
    is_sparse = _is_sparse_like(value)
    is_complex = _is_complex_value(value)
    kind = _kind_of(value, dtype=dtype, is_sparse=is_sparse)
    stats = _numeric_stats(value) if kind == MatVariableKind.NUMERIC else {}
    return MatVariableSummary(
        name=name,
        kind=kind,
        type_name=type_name,
        shape=shape,
        dtype=dtype,
        size=_size_of(value),
        is_numeric=kind == MatVariableKind.NUMERIC.value,
        is_complex=is_complex,
        is_sparse=is_sparse,
        preview=_preview_value(value),
        min_value=stats.get("min"),
        max_value=stats.get("max"),
        mean_value=stats.get("mean"),
        source_file=str(source_path or ""),
        metadata=_summary_metadata(value),
    )


def table_preview_from_value(
    name: str,
    value: Any,
    *,
    max_rows: int = 20,
    max_cols: int = 12,
) -> MatTablePreview:
    data_rows, row_count, column_count, truncated = _value_to_table_rows(
        value,
        max_rows=max_rows,
        max_cols=max_cols,
    )
    columns = tuple(f"col_{index}" for index in range(column_count or 1))
    return MatTablePreview(
        variable_name=name,
        columns=columns,
        rows=data_rows,
        row_count=row_count,
        column_count=column_count,
        truncated=truncated,
    )


def export_variable_to_csv(
    path: str | Path,
    variable_name: str,
    out_csv_path: str | Path,
) -> MatCsvExportResult:
    result = read_mat_file(path, variable_names=(variable_name,))
    diagnostics = DiagnosticReport()
    diagnostics.extend(result.diagnostics)
    if not result.ok:
        return MatCsvExportResult(
            result.status,
            str(out_csv_path),
            variable_name,
            diagnostics,
        )
    try:
        value = result.value(variable_name)
    except KeyError:
        diagnostics.add_error(
            "mat-variable-missing",
            f"MAT variable was not found: {variable_name}",
            hint="Use mat-vars to list available variables.",
            path=path,
        )
        return MatCsvExportResult(
            MatReadStatus.ERROR,
            str(out_csv_path),
            variable_name,
            diagnostics,
        )
    if not _is_csv_exportable_numeric(value):
        diagnostics.add_error(
            "mat-csv-unsupported-variable",
            f"MAT variable cannot be exported to CSV: {variable_name}",
            hint="CSV export supports real numeric 1D or 2D arrays.",
            path=path,
        )
        return MatCsvExportResult(
            MatReadStatus.UNSUPPORTED,
            str(out_csv_path),
            variable_name,
            diagnostics,
        )

    rows, row_count, column_count, _truncated = _value_to_table_rows(
        value,
        max_rows=_max_int(),
        max_cols=_max_int(),
    )
    columns = (variable_name,) if column_count == 1 else tuple(
        f"{variable_name}_{index + 1}" for index in range(column_count)
    )
    target = Path(out_csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(columns)
        writer.writerows(rows)
    return MatCsvExportResult(
        MatReadStatus.OK,
        str(target),
        variable_name,
        diagnostics,
        row_count=row_count,
        column_count=column_count,
    )


def export_mat_variable_csv(
    preview_or_path: MatReadResult | MatFilePreview | str | Path,
    variable_name: str,
    output_path: str | Path,
) -> Path:
    """Backward-compatible CSV export helper."""

    if isinstance(preview_or_path, str | Path):
        result = export_variable_to_csv(preview_or_path, variable_name, output_path)
        if not result.ok:
            msg = result.diagnostics.summary()
            raise MatReaderError(msg)
        return Path(result.output_path)
    value = preview_or_path.value(variable_name)
    if not _is_csv_exportable_numeric(value):
        msg = f"MAT variable cannot be exported to CSV: {variable_name}"
        raise MatReaderError(msg)
    preview = table_preview_from_value(
        variable_name,
        value,
        max_rows=_max_int(),
        max_cols=_max_int(),
    )
    return preview.export_csv(output_path)


def mat_summary_to_workspace_variables(
    summary: MatFileSummary | MatReadResult,
) -> tuple[WorkspaceVariableSummary, ...]:
    mat_summary = summary.summary if isinstance(summary, MatReadResult) else summary
    return tuple(_workspace_variable_from_mat(variable) for variable in mat_summary.variables)


def mat_file_to_figure_dataset(
    summary: MatFileSummary | MatReadResult,
    *,
    source_file: str | Path | None = None,
) -> FigureDataset:
    mat_summary = summary.summary if isinstance(summary, MatReadResult) else summary
    source = str(source_file or mat_summary.source_path)
    return FigureDataset(
        dataset_id=new_dataset_id("mat-workspace"),
        source_file=source,
        engine="imported",
        workspace_variables=mat_summary_to_workspace_variables(mat_summary),
        diagnostics=mat_summary.diagnostics,
        metadata={
            "mat_version": mat_summary.version,
            "variable_count": len(mat_summary.variables),
        },
    )


def create_mat_script_ref(result: MatReadResult, *, ref_id: str | None = None) -> ScriptRef:
    summary = result.summary
    path = summary.source_path
    metadata = {
        "data_type": "matlab_mat",
        "mat_summary": summary.to_dict(),
        "variable_count": len(summary.variables),
        "variables": [variable.to_dict() for variable in summary.variables],
    }
    return ScriptRef(
        id=ref_id or _mat_ref_id(path),
        name=Path(path).name,
        path=path,
        language="matlab_mat",
        role="data",
        status="previewed" if result.ok else "diagnostic",
        safe_preview_required=True,
        metadata=metadata,
    )


def _read_v73(
    path: Path,
    diagnostics: DiagnosticReport,
    *,
    variable_names: Sequence[str] | None,
    max_preview_rows: int,
    max_preview_cols: int,
    hdf5storage_loadmat: Callable[..., Mapping[str, Any]] | None,
    h5py_module: object | None,
) -> MatReadResult:
    if hdf5storage_loadmat is not None:
        try:
            payload = dict(hdf5storage_loadmat(str(path)))
        except Exception as exc:  # pragma: no cover - optional backend varies.
            diagnostics.add_error(
                "mat-v73-load-failed",
                f"Could not read MAT v7.3 file with hdf5storage: {exc}",
                hint="Try re-exporting the file or inspect it with HDF5 tooling.",
                path=path,
            )
            return _empty_result(path, MatReadStatus.ERROR, diagnostics, version=MatFileVersion.V73)
        return _result_from_payload(
            path,
            MatFileVersion.V73,
            payload,
            diagnostics,
            variable_names=variable_names,
            max_preview_rows=max_preview_rows,
            max_preview_cols=max_preview_cols,
        )
    if h5py_module is not None:
        return _read_v73_h5py_tree(path, diagnostics, h5py_module)

    diagnostics.add_warning(
        "mat-v73-dependency-missing",
        "MAT v7.3 is HDF5-based. Optional HDF5 MAT support is unavailable.",
        hint="Install hdf5storage or h5py optional support to inspect MAT v7.3 files.",
        path=path,
    )
    return _empty_result(
        path,
        MatReadStatus.DEPENDENCY_MISSING,
        diagnostics,
        version=MatFileVersion.V73,
    )


def _read_v73_h5py_tree(
    path: Path,
    diagnostics: DiagnosticReport,
    h5py_module: object,
) -> MatReadResult:
    variables: list[MatVariableSummary] = []
    try:
        with h5py_module.File(path, "r") as handle:  # type: ignore[attr-defined]
            for name in sorted(handle.keys()):
                item = handle[name]
                shape = tuple(int(part) for part in getattr(item, "shape", ()) or ())
                dtype = str(getattr(item, "dtype", "group"))
                kind = MatVariableKind.NUMERIC if shape else MatVariableKind.STRUCT
                variables.append(
                    MatVariableSummary(
                        name=name,
                        kind=kind,
                        type_name=type(item).__name__,
                        shape=shape,
                        dtype=dtype,
                        size=_safe_size(item),
                        preview="HDF5 dataset summary" if shape else "HDF5 group",
                        source_file=str(path),
                    )
                )
    except Exception as exc:  # pragma: no cover - optional backend varies.
        diagnostics.add_error(
            "mat-v73-h5py-summary-failed",
            f"Could not summarize MAT v7.3 HDF5 tree: {exc}",
            path=path,
        )
        return _empty_result(path, MatReadStatus.ERROR, diagnostics, version=MatFileVersion.V73)
    diagnostics.add_info(
        "mat-v73-h5py-summary",
        "MAT v7.3 HDF5 tree was summarized without full MATLAB object reconstruction.",
        hint="Install hdf5storage for richer v7.3 value loading.",
        path=path,
    )
    summary = MatFileSummary(
        source_path=str(path),
        version=MatFileVersion.V73,
        variables=tuple(variables),
        diagnostics=diagnostics,
        metadata={"reader": "h5py-tree-summary"},
    )
    return MatReadResult(MatReadStatus.WARNING, summary, diagnostics=diagnostics)


def _result_from_payload(
    path: Path,
    version: MatFileVersion,
    payload: Mapping[str, Any],
    diagnostics: DiagnosticReport,
    *,
    variable_names: Sequence[str] | None,
    max_preview_rows: int,
    max_preview_cols: int,
) -> MatReadResult:
    selected = set(variable_names or ())
    public_payload = {
        name: value
        for name, value in payload.items()
        if name not in _MATLAB_INTERNAL_NAMES and (not selected or name in selected)
    }
    variables = tuple(
        variable_summary_from_value(name, public_payload[name], source_path=path)
        for name in sorted(public_payload)
    )
    if variable_names:
        missing = sorted(selected - set(public_payload))
        for name in missing:
            diagnostics.add_warning(
                "mat-variable-missing",
                f"Requested MAT variable was not found: {name}",
                hint="Use mat-vars to list available variables.",
                path=path,
            )
    for variable_name, value in public_payload.items():
        try:
            table_preview_from_value(
                variable_name,
                value,
                max_rows=max_preview_rows,
                max_cols=max_preview_cols,
            )
        except Exception:
            continue
    summary = MatFileSummary(
        source_path=str(path),
        version=version,
        variables=variables,
        diagnostics=diagnostics,
        metadata={"reader": "scipy-loadmat" if version != MatFileVersion.V73 else "hdf5storage"},
    )
    status = MatReadStatus.WARNING if diagnostics.has_warnings else MatReadStatus.OK
    return MatReadResult(status, summary, values=public_payload, diagnostics=diagnostics)


def _empty_result(
    path: str | Path,
    status: MatReadStatus,
    diagnostics: DiagnosticReport,
    *,
    version: MatFileVersion = MatFileVersion.UNKNOWN,
) -> MatReadResult:
    summary = MatFileSummary(
        source_path=str(path),
        version=version,
        variables=(),
        diagnostics=diagnostics,
    )
    return MatReadResult(status, summary, values={}, diagnostics=diagnostics)


def _workspace_variable_from_mat(variable: MatVariableSummary) -> WorkspaceVariableSummary:
    return WorkspaceVariableSummary(
        name=variable.name,
        type_name=variable.kind,
        shape=variable.shape,
        dtype=variable.dtype,
        size=variable.size,
        preview=variable.preview,
        source=variable.source_file,
        metadata={
            "mat_kind": variable.kind,
            "mat_type_name": variable.type_name,
            "is_numeric": variable.is_numeric,
            "is_complex": variable.is_complex,
            "is_sparse": variable.is_sparse,
            "min_value": variable.min_value,
            "max_value": variable.max_value,
            "mean_value": variable.mean_value,
        },
    )


def _shape_of(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is not None:
        return tuple(int(item) for item in shape)
    if isinstance(value, list | tuple):
        if value and all(isinstance(item, list | tuple) for item in value):
            return (len(value), max(len(item) for item in value))
        return (len(value),)
    if isinstance(value, str):
        return (len(value),)
    return ()


def _dtype_of(value: Any) -> str:
    dtype = getattr(value, "dtype", None)
    return str(dtype) if dtype is not None else type(value).__name__


def _type_name_of(value: Any) -> str:
    module = type(value).__module__
    name = type(value).__name__
    return name if module == "builtins" else f"{module}.{name}"


def _kind_of(value: Any, *, dtype: str, is_sparse: bool) -> str:
    if is_sparse:
        return MatVariableKind.SPARSE.value
    if isinstance(value, str):
        return MatVariableKind.STRING.value
    kind = getattr(getattr(value, "dtype", None), "kind", "")
    if kind == "b":
        return MatVariableKind.LOGICAL.value
    if kind in "iufc":
        return MatVariableKind.NUMERIC.value
    if kind in {"U", "S"}:
        return MatVariableKind.CHAR.value
    if kind == "O":
        if _looks_like_cell(value):
            return MatVariableKind.CELL.value
        return MatVariableKind.STRUCT.value
    if dtype in {"bool", "boolean"}:
        return MatVariableKind.LOGICAL.value
    if dtype in {"int", "float", "complex"}:
        return MatVariableKind.NUMERIC.value
    return MatVariableKind.UNKNOWN.value


def _is_sparse_like(value: Any) -> bool:
    return hasattr(value, "tocoo") and hasattr(value, "shape")


def _is_complex_value(value: Any) -> bool:
    if isinstance(value, complex):
        return True
    if getattr(getattr(value, "dtype", None), "kind", "") == "c":
        return True
    return False


def _size_of(value: Any) -> int | None:
    size = getattr(value, "size", None)
    if size is not None:
        try:
            return int(size)
        except (TypeError, ValueError):
            return None
    if isinstance(value, str | list | tuple | dict):
        return len(value)
    return None


def _safe_size(value: Any) -> int | None:
    try:
        size = getattr(value, "size", None)
        return int(size) if size is not None else None
    except (TypeError, ValueError):
        return None


def _numeric_stats(value: Any) -> dict[str, float]:
    if _is_sparse_like(value) or _is_complex_value(value):
        return {}
    try:
        import numpy as np
    except ModuleNotFoundError:
        return _numeric_stats_python(value)
    try:
        array = np.asarray(value, dtype=float)
        if array.size == 0:
            return {}
        finite = array[np.isfinite(array)]
        if finite.size == 0:
            return {}
        return {
            "min": float(np.min(finite)),
            "max": float(np.max(finite)),
            "mean": float(np.mean(finite)),
        }
    except (TypeError, ValueError, OverflowError):
        return {}


def _numeric_stats_python(value: Any) -> dict[str, float]:
    flat = [float(item) for item in _flatten(value) if _is_finite_number(item)]
    if not flat:
        return {}
    return {"min": min(flat), "max": max(flat), "mean": sum(flat) / len(flat)}


def _preview_value(value: Any, *, max_chars: int = 240) -> str:
    if _is_sparse_like(value):
        text = f"sparse {getattr(value, 'shape', '')} with {getattr(value, 'nnz', '?')} entries"
    elif isinstance(value, str):
        text = value
    elif hasattr(value, "tolist"):
        try:
            text = json.dumps(value.tolist(), ensure_ascii=True, default=str)
        except (TypeError, ValueError):
            text = str(value)
    else:
        try:
            text = json.dumps(value, ensure_ascii=True, default=str)
        except (TypeError, ValueError):
            text = str(value)
    return text if len(text) <= max_chars else f"{text[: max_chars - 3]}..."


def _summary_metadata(value: Any) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    fields = getattr(value, "_fieldnames", None)
    if fields:
        metadata["fields"] = list(fields)
    if _is_sparse_like(value):
        metadata["nnz"] = getattr(value, "nnz", None)
    return metadata


def _value_to_table_rows(
    value: Any,
    *,
    max_rows: int,
    max_cols: int,
) -> tuple[tuple[tuple[str, ...], ...], int, int, bool]:
    if _is_sparse_like(value):
        return ((("sparse preview deferred",),), 1, 1, False)
    data = value.tolist() if hasattr(value, "tolist") else value
    if isinstance(data, str):
        rows = ((data,),)
        return rows, 1, 1, False
    if not isinstance(data, list | tuple):
        rows = ((str(data),),)
        return rows, 1, 1, False
    if not data:
        return (), 0, 0, False
    if not isinstance(data[0], list | tuple):
        row_count = len(data)
        rows = tuple((str(item),) for item in data[:max_rows])
        return rows, row_count, 1, row_count > max_rows
    row_count = len(data)
    column_count = max((len(row) for row in data), default=0)
    rows = tuple(
        tuple(str(item) for item in row[:max_cols])
        for row in data[:max_rows]
    )
    truncated = row_count > max_rows or column_count > max_cols
    return rows, row_count, column_count, truncated


def _is_csv_exportable_numeric(value: Any) -> bool:
    if _is_sparse_like(value) or _is_complex_value(value):
        return False
    kind = _kind_of(value, dtype=_dtype_of(value), is_sparse=False)
    if kind != MatVariableKind.NUMERIC.value:
        return False
    shape = _shape_of(value)
    return len(shape) in {0, 1, 2}


def _looks_like_cell(value: Any) -> bool:
    shape = _shape_of(value)
    return bool(shape and getattr(getattr(value, "dtype", None), "kind", "") == "O")


def _flatten(value: Any) -> list[Any]:
    data = value.tolist() if hasattr(value, "tolist") else value
    if isinstance(data, list | tuple):
        items: list[Any] = []
        for item in data:
            items.extend(_flatten(item))
        return items
    return [data]


def _is_finite_number(value: Any) -> bool:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number)


def _mat_ref_id(path: str | Path) -> str:
    stem = Path(path).stem or "mat-data"
    safe = "".join(char if char.isalnum() else "-" for char in stem.lower()).strip("-")
    return f"mat-{safe or 'data'}"


def _safe_header(path: Path) -> bytes:
    try:
        return path.read_bytes()[:128]
    except OSError:
        return b""


def _looks_like_v4_header(header: bytes) -> bool:
    if len(header) < 20:
        return False
    # MATLAB v4 files start with small integer fields. This is only a best-effort
    # discriminator used before SciPy performs the real parse.
    return not header.startswith(b"MATLAB") and not header.startswith(_HDF5_SIGNATURE)


def _resolve_scipy_loadmat() -> Callable[..., Mapping[str, Any]] | None:
    try:
        from scipy.io import loadmat
    except ModuleNotFoundError:
        return None
    return loadmat


def _resolve_hdf5storage_loadmat() -> Callable[..., Mapping[str, Any]] | None:
    try:
        from hdf5storage import loadmat
    except ModuleNotFoundError:
        return None
    return loadmat


def _resolve_h5py() -> object | None:
    try:
        import h5py
    except ModuleNotFoundError:
        return None
    return h5py


def _max_int() -> int:
    return 2_147_483_647
