# MATLAB MAT Data Reader

`OSW-FUNC-009_MAT_READER` adds preview-only MATLAB `.mat` data import. It reads
data files, summarizes variables, and exports simple numeric arrays to CSV. It
does not execute `.m` files, launch MATLAB, launch Octave, use Oct2Py, read
`.fig` files, or support Simulink/App Designer formats.

## Purpose

The MAT reader is a data inspection boundary for workspace artifacts and user
provided MAT files. OSW can list variables, show compact previews, and attach
summary metadata to a project before later workflows decide whether a variable
should become a boundary curve or report input.

## Data Model

The models live under `osw.scripts.mscript.mat_model`:

- `MatFileVersion`: `v4`, `v5`, `v6`, `v7`, `v7.2`, `v7.3`, or `unknown`.
- `MatVariableKind`: numeric, logical, char/string, struct, cell, sparse,
  object, or unknown.
- `MatVariableSummary`: name, kind, type, shape, dtype, numeric/complex/sparse
  flags, preview text, optional min/max/mean, source, and metadata.
- `MatTablePreview`: truncated row/column preview that can export CSV.
- `MatFileSummary`: source path, detected version, variable summaries,
  diagnostics, and metadata.
- `MatReadResult`: status, summary, diagnostics, source path, and optional
  in-memory values for explicit preview/export operations.

The models are JSON-serializable and import without SciPy, hdf5storage, h5py,
MATLAB, Octave, PySide6, matplotlib, Pillow, or pandas.

## Version Detection

`detect_mat_version()` performs a lightweight file check:

- HDF5 signature means MAT v7.3.
- `MATLAB 5.0 MAT-file` header is treated as v7-compatible v5-family data.
- Binary v4-like files are classified as v4 on a best-effort basis.
- Unsupported extensions, missing files, and tiny/corrupt files produce
  structured diagnostics.

## SciPy Load Path

MAT v4 through v7.2 data is read through `scipy.io.loadmat` when SciPy is
available. SciPy is imported lazily. If SciPy is missing, the reader returns a
`dependency_missing` result with an install hint instead of raising an import
error.

Internal MATLAB metadata variables are ignored by default:

- `__header__`
- `__version__`
- `__globals__`

## MAT v7.3 / HDF5

MAT v7.3 is HDF5-based. If `hdf5storage` is available, OSW attempts value
loading through it. If only `h5py` is available, OSW provides a tree summary.
If neither optional dependency is available, OSW returns a friendly diagnostic:
install `hdf5storage` or `h5py` for v7.3 inspection.

v7.3 support is optional and does not make HDF5 packages mandatory for base
imports or unit tests.

## Variable Summaries

The reader summarizes:

- variable names;
- kind/type/dtype;
- shape and size;
- short preview text;
- numeric min/max/mean where safe;
- complex and sparse flags;
- struct/cell/object placeholders without reconstruction.

Large arrays are not embedded in summaries. Sparse arrays are not densified.

## CSV Export

`mat-export-csv` and `export_variable_to_csv()` support real numeric scalar,
1D, and 2D variables. Unsupported types, missing variables, complex arrays, and
sparse arrays return diagnostics instead of partial output. CSV export uses the
standard library and does not require pandas.

## Workspace and FigureDataset Integration

`mat_summary_to_workspace_variables()` converts MAT summaries into
`WorkspaceVariableSummary` records. `mat_file_to_figure_dataset()` can package
MAT variable summaries into a FigureDataset-compatible workspace table for plot
viewer and report surfaces.

`OSW-FUNC-010_BOUNDARY_CURVE_BRIDGE` can convert already-loaded numeric MAT
variables into ProjectSchema `BoundaryCurve` records. Summary-only MAT metadata
remains preview-safe and reports a friendly diagnostic when full values are not
available for curve conversion.

## ProjectSchema Binding

MAT data can be represented as a safe preview `ScriptRef` with:

- `language: matlab_mat`
- `role: data`
- `safe_preview_required: true`
- `metadata.mat_summary`
- `metadata.variable_count`
- `metadata.variables`

Validation warns when a `.mat` reference has no preview/summary metadata.

## GUI Binding

The MAT preview UI consists of:

- `MatPreviewDialog`
- `MatPreviewPanel`

The dialog shows source path, detected version, variable table, selected
variable preview, diagnostics, import action, and CSV export action. There is no
Run button, and the GUI does not launch MATLAB, Octave, subprocesses, or
external tools.

## CLI

Inspect MAT metadata:

```powershell
.venv\Scripts\python.exe -m osw.cli mat-info tests\fixtures\mat\numeric_arrays.mat
```

List variables:

```powershell
.venv\Scripts\python.exe -m osw.cli mat-vars tests\fixtures\mat\numeric_arrays.mat
```

Export a numeric variable:

```powershell
.venv\Scripts\python.exe -m osw.cli mat-export-csv tests\fixtures\mat\numeric_arrays.mat x --out artifacts\mat\x.csv
```

If SciPy is missing, these commands print friendly dependency diagnostics and
return nonzero for commands that require parsing.

## Security Rules

- MAT import never executes `.m` code.
- MAT import does not invoke MATLAB or Octave.
- GUI code does not call subprocess APIs.
- No MATLAB Engine, Oct2Py, `.fig`, Simulink, `.slx`, or `.mlapp` support is
  added.
- Optional dependencies are imported lazily.
- MAT contents are treated as untrusted data until previewed and explicitly
  accepted into a project.

## Known Limitations

- v7.3 value loading depends on optional HDF5 packages.
- MATLAB objects, structs, and cells are summarized conservatively.
- Sparse arrays are summarized without dense conversion.
- CSV export is limited to simple real numeric scalar, 1D, or 2D variables.
- No boundary-curve conversion is implemented in this step.

## Next Step

Next functional step: `OSW-FUNC-011_REPORT_GENERATOR_BINDING`.
