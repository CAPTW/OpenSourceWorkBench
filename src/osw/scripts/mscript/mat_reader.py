"""Preview-only MATLAB MAT data reader."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from osw.core.diagnostics import DiagnosticReport
from osw.post.table_model import TablePreview

_AUTO = object()
_HDF5_SIGNATURE = b"\x89HDF\r\n\x1a\n"


class MatReaderError(RuntimeError):
    """Raised when a MAT preview variable cannot be accessed."""


@dataclass(frozen=True)
class MatVariableSummary:
    name: str
    shape: tuple[int, ...]
    dtype: str
    is_numeric: bool
    kind: str = "array"

    @property
    def display_shape(self) -> str:
        if not self.shape:
            return "scalar"
        return "x".join(str(item) for item in self.shape)


@dataclass(frozen=True)
class MatFilePreview:
    file_path: Path
    format_version: str
    variables: tuple[MatVariableSummary, ...] = field(default_factory=tuple)
    diagnostics: DiagnosticReport = field(default_factory=DiagnosticReport)
    _values: Mapping[str, Any] = field(default_factory=dict, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "file_path", Path(self.file_path))
        object.__setattr__(self, "variables", tuple(self.variables))

    @property
    def variable_names(self) -> tuple[str, ...]:
        return tuple(variable.name for variable in self.variables)

    def variable(self, name: str) -> MatVariableSummary:
        for variable in self.variables:
            if variable.name == name:
                return variable
        msg = f"MAT variable not found: {name}"
        raise MatReaderError(msg)

    def table_preview(
        self,
        name: str,
        *,
        max_rows: int = 20,
        max_columns: int = 20,
    ) -> TablePreview:
        self.variable(name)
        if name not in self._values:
            msg = f"MAT variable data is unavailable for preview: {name}"
            raise MatReaderError(msg)
        return _table_preview_from_value(
            name,
            self._values[name],
            max_rows=max_rows,
            max_columns=max_columns,
            source=str(self.file_path),
        )


class MatReader:
    """Read `.mat` files into metadata and small preview tables.

    This reader never executes MATLAB/Octave code. SciPy handles MATLAB v4
    through v7.2 files when available. MATLAB v7.3 is HDF5-backed and is routed
    through optional `hdf5storage` when installed, otherwise a friendly warning
    is returned.
    """

    def __init__(
        self,
        *,
        scipy_loadmat: Callable[..., Mapping[str, Any]] | None | object = _AUTO,
        hdf5storage_loadmat: Callable[..., Mapping[str, Any]] | None | object = _AUTO,
    ) -> None:
        self.scipy_loadmat = _resolve_scipy_loadmat() if scipy_loadmat is _AUTO else scipy_loadmat
        self.hdf5storage_loadmat = (
            _resolve_hdf5storage_loadmat()
            if hdf5storage_loadmat is _AUTO
            else hdf5storage_loadmat
        )

    def read(self, path: str | Path) -> MatFilePreview:
        mat_path = Path(path).expanduser().resolve()
        diagnostics = DiagnosticReport()
        if mat_path.suffix.lower() != ".mat":
            diagnostics.add_error(
                "mat.invalid_extension",
                "Only .mat files can be previewed by the MAT reader.",
                path=str(mat_path),
            )
            return MatFilePreview(mat_path, "unknown", diagnostics=diagnostics)
        if not mat_path.exists():
            diagnostics.add_error(
                "mat.missing_file",
                f"MAT file does not exist: {mat_path}",
                path=str(mat_path),
            )
            return MatFilePreview(mat_path, "unknown", diagnostics=diagnostics)

        format_version = _detect_mat_format(mat_path)
        if format_version == "7.3":
            return self._read_v73(mat_path, diagnostics)
        return self._read_scipy(mat_path, diagnostics, format_version)

    def _read_v73(self, path: Path, diagnostics: DiagnosticReport) -> MatFilePreview:
        if self.hdf5storage_loadmat is None:
            diagnostics.add_warning(
                "mat.v73_optional_dependency",
                (
                    "MAT v7.3 files are HDF5-backed. Install optional hdf5storage "
                    "to preview them with OSW."
                ),
                path=str(path),
            )
            return MatFilePreview(path, "7.3", diagnostics=diagnostics)

        try:
            payload = dict(self.hdf5storage_loadmat(str(path)))
        except Exception as exc:  # pragma: no cover - depends on optional backend
            diagnostics.add_error(
                "mat.v73_load_failed",
                f"Could not read MAT v7.3 file with hdf5storage: {exc}",
                path=str(path),
            )
            return MatFilePreview(path, "7.3", diagnostics=diagnostics)
        return _preview_from_payload(path, "7.3", payload, diagnostics)

    def _read_scipy(
        self,
        path: Path,
        diagnostics: DiagnosticReport,
        format_version: str,
    ) -> MatFilePreview:
        if self.scipy_loadmat is None:
            diagnostics.add_error(
                "mat.scipy_missing",
                (
                    "scipy is required to preview MATLAB MAT v4-v7.2 files. "
                    "Install it with `python -m pip install -e .[mscript]`."
                ),
                path=str(path),
            )
            return MatFilePreview(path, format_version, diagnostics=diagnostics)

        try:
            payload = dict(
                self.scipy_loadmat(
                    str(path),
                    squeeze_me=False,
                    struct_as_record=False,
                )
            )
        except Exception as exc:
            diagnostics.add_error(
                "mat.load_failed",
                f"Could not read MAT file: {exc}",
                path=str(path),
            )
            return MatFilePreview(path, format_version, diagnostics=diagnostics)
        return _preview_from_payload(path, format_version, payload, diagnostics)


def read_mat_file(path: str | Path) -> MatFilePreview:
    return MatReader().read(path)


def export_mat_variable_csv(
    preview: MatFilePreview,
    variable_name: str,
    output_path: str | Path,
) -> Path:
    return preview.table_preview(variable_name).export_csv(output_path)


def _preview_from_payload(
    path: Path,
    format_version: str,
    payload: Mapping[str, Any],
    diagnostics: DiagnosticReport,
) -> MatFilePreview:
    public_payload = {
        name: value
        for name, value in payload.items()
        if not name.startswith("__")
    }
    variables = tuple(
        _summarize_variable(name, public_payload[name])
        for name in sorted(public_payload)
    )
    return MatFilePreview(
        path,
        format_version,
        variables=variables,
        diagnostics=diagnostics,
        _values=public_payload,
    )


def _summarize_variable(name: str, value: Any) -> MatVariableSummary:
    shape = _shape_of(value)
    dtype = _dtype_of(value)
    return MatVariableSummary(
        name=name,
        shape=shape,
        dtype=dtype,
        is_numeric=_is_numeric_dtype(dtype, value),
        kind="array" if shape else "scalar",
    )


def _table_preview_from_value(
    name: str,
    value: Any,
    *,
    max_rows: int,
    max_columns: int,
    source: str,
) -> TablePreview:
    rows = _value_to_rows(value, max_rows=max_rows, max_columns=max_columns)
    width = max((len(row) for row in rows), default=1)
    columns = tuple(f"col_{index}" for index in range(width))
    normalized_rows = tuple(
        (*row, *("" for _ in range(width - len(row))))
        for row in rows
    )
    return TablePreview(
        columns=columns,
        rows=normalized_rows,
        title=name,
        source=source,
        notes=("MAT variable preview is truncated for display/export.",),
    )


def _value_to_rows(value: Any, *, max_rows: int, max_columns: int) -> tuple[tuple[str, ...], ...]:
    data = value.tolist() if hasattr(value, "tolist") else value
    if not isinstance(data, list):
        return ((str(data),),)
    if not data:
        return ()
    if not isinstance(data[0], list):
        return tuple((str(item),) for item in data[:max_rows])
    return tuple(
        tuple(str(item) for item in row[:max_columns])
        for row in data[:max_rows]
    )


def _shape_of(value: Any) -> tuple[int, ...]:
    shape = getattr(value, "shape", None)
    if shape is None:
        return ()
    return tuple(int(item) for item in shape)


def _dtype_of(value: Any) -> str:
    dtype = getattr(value, "dtype", None)
    if dtype is None:
        return type(value).__name__
    return str(dtype)


def _is_numeric_dtype(dtype: str, value: Any) -> bool:
    kind = getattr(getattr(value, "dtype", None), "kind", "")
    return bool(kind and kind in "biufc") or dtype in {"int", "float", "complex"}


def _detect_mat_format(path: Path) -> str:
    header = path.read_bytes()[:128]
    if header.startswith(_HDF5_SIGNATURE):
        return "7.3"
    if header.startswith(b"MATLAB 4.0"):
        return "4"
    return "v4-v7.2"


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
