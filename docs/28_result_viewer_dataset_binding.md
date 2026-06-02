# Result Viewer Dataset Binding

`OSW-FUNC-017_RESULT_VIEWER_DATASET_BINDING` adds a unified, summary-first
result catalog and viewer binding for existing OSW datasets. It does not run
solvers, scripts, MATLAB, Octave, CalculiX, Gmsh, OpenFOAM, or visualization
backends.

## Model

Core result catalog records live in `osw.core.result_dataset`:

- `ResultDatasetKind`
- `ResultScalar`
- `ResultSeries`
- `ResultTable`
- `ResultArtifactRef`
- `ResultDatasetSummary`
- `ResultCatalog`

The existing `ResultDataset`, `ResultField`, `ResultRow`, and
`ResultSummaryValue` contracts remain backward-compatible.

## View Model

`osw.post.result_view_model` converts existing summaries into viewer-ready
records:

- CalculiX parsed summaries become scalar result datasets.
- OpenFOAM residual summaries become scalar and residual-series datasets.
- FigureDataset records become figure, workspace-variable, and artifact tables.
- MAT summaries become workspace-variable tables.
- BoundaryCurve records become xy series and preview tables.
- MeshInfo records become mesh-count scalar summaries and cell-type tables.

Missing artifacts are reported as diagnostics. Empty datasets produce a friendly
empty state.

## GUI

`ResultViewer` now accepts `ResultCatalog` and `ResultDataset` objects. It
displays a dataset selector, scalar summaries, residual/series previews, a table
viewer, artifact list, diagnostics, and a placeholder-only PyVista contour hook.

Stable object names include:

- `oswResultViewer`
- `oswResultDatasetSelector`
- `oswResultSummaryPanel`
- `oswResultScalarCards`
- `oswResultSeriesPanel`
- `oswResultTableViewer`
- `oswResultArtifactsPanel`
- `oswResultDiagnosticsList`
- `oswResultEmptyState`

The existing central QPainter viewport remains the default shell view.

## CLI

Read-only inspection commands:

```powershell
python -m osw.cli result-dataset-inspect tests\fixtures\results\calculix_summary_result.json
python -m osw.cli result-catalog-inspect tests\fixtures\results\mixed_result_catalog.json
python -m osw.cli result-catalog-from-project project.json --out artifacts\results\catalog.json
python -m osw.cli result-dataset-export-json input.json --out artifacts\results\result.json
```

These commands do not require PySide6 or optional visualization dependencies.

## Limitations

- Full CalculiX FRD contour parsing is deferred.
- OpenFOAM velocity/pressure field parsing is deferred.
- PyVista rendering remains optional and placeholder-only in this step.
- Viewer summaries are evidence for review, not proof of physical validity.

## Field Rendering Extension

`OSW-FUNC-019_RESULT_VIEWER_FIELD_RENDERING` extends this viewer with a
field-specific metadata panel. FieldArraySummary and FieldArtifactSummary records
can be attached through ResultDataset metadata, MeshInfo/MeshModel summaries, or
read-only VTK/VTU artifact inspection. Scalar rendering is attempted only
through the optional PyVista bridge when in-memory mesh geometry is available;
missing PyVista and metadata-only datasets produce friendly placeholder
diagnostics. Vector/tensor rendering is listed as metadata and deferred.

## Next Step

Next functional step: `OSW-FUNC-020_RELEASE_VALIDATION_GATE`.
