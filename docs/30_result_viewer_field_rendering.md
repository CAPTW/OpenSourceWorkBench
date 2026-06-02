# Result Viewer Field Rendering

`OSW-FUNC-019_RESULT_VIEWER_FIELD_RENDERING` adds optional field-rendering
metadata and scalar visualization hooks to the unified ResultViewer. This is a
visualization binding step, not a solver parser or execution feature.

## Models

Field models live in `osw.post.field_dataset`:

- `FieldArraySummary` describes scalar, vector, or tensor arrays with location,
  components, value count, units, optional scalar range, source, and metadata.
- `FieldArtifactSummary` describes VTK/VTU/JSON field artifacts, mesh metadata,
  discovered arrays, diagnostics, and file existence/size.
- `FieldDatasetSummary` groups field arrays, artifacts, mesh metadata, and
  diagnostics for one dataset.
- `FieldRenderRequest` and `FieldRenderResult` describe optional render attempts
  and outcomes without requiring PyVista at import time.

Field view models live in `osw.post.field_view_model` and normalize:

- ResultDataset metadata with `field_arrays`, `field_artifacts`, and
  `mesh_info`;
- MeshInfo point/cell/field data names;
- MeshModel in-memory point/cell arrays for optional rendering;
- small VTK/VTU-style artifacts inspected read-only.

## Artifact Inspection

`inspect_field_artifact()` and `inspect_field_artifacts()` read local artifacts
only. Legacy ASCII VTK files are scanned for cheap metadata such as point/cell
counts, scalar names, vector names, and scalar ranges. VTU files are inspected
through Python XML metadata. These helpers do not run solvers, import PyVista,
or implement full CalculiX FRD/OpenFOAM field parsing.

## Optional PyVista Rendering

`osw.post.pyvista_scene.render_field_view()` attempts scalar rendering only when:

- PyVista is importable or supplied by tests;
- a scalar field is selected;
- in-memory MeshData geometry is attached through a MeshModel-backed view model.

Missing PyVista returns `dependency_missing`. Metadata-only datasets return a
placeholder result. Vector glyph rendering, streamlines, time animation, and
production post-processing controls are deferred.

## GUI

`FieldViewerPanel` is embedded inside the existing `ResultViewer`. It displays:

- field array metadata;
- field artifact metadata;
- scalar field selector;
- render and screenshot hook buttons;
- render status and diagnostics.

The panel does not run solvers, scripts, MATLAB, Octave, OpenFOAM, CalculiX,
Gmsh, or subprocesses. Rendering is an explicit optional PyVista call and
missing dependencies are shown as friendly diagnostics.

## CLI

Read-only inspection commands:

```powershell
python -m osw.cli field-artifacts-inspect tests\fixtures\fields
python -m osw.cli field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
```

These commands do not require PySide6 or PyVista.

## Report Compatibility

Field datasets can expose a `field_rows` metadata table. `ResultDataset` report
table generation and the report summary path include those rows as ordinary
result tables, so reports can describe field metadata without rendering images
or loading visualization backends.

## Limitations

- Full CalculiX FRD field parsing is deferred.
- Full OpenFOAM field parsing is deferred.
- Vector/tensor rendering is metadata-only in v0.1.
- PyVista, PySide6, matplotlib, and Pillow remain optional.
- Field summaries support review and education; they do not prove physical
  validity.

## Next Step

Next functional step: `OSW-FUNC-020_RELEASE_VALIDATION_GATE`.
