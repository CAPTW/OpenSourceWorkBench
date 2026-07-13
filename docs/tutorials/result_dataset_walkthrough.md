# Result Dataset Walkthrough

This walkthrough inspects curated tiny fixtures. It does not execute solvers or
require visualization dependencies.

## Commands

```powershell
.venv\Scripts\python.exe -m osw.cli result-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
.venv\Scripts\python.exe -m osw.cli field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
```

Linux/macOS:

```bash
.venv/bin/python -m osw.cli result-dataset-inspect tests/fixtures/fields/scalar_field_dataset.json
.venv/bin/python -m osw.cli field-dataset-inspect tests/fixtures/fields/scalar_field_dataset.json
```

Expected result:
- `result-dataset-inspect` prints summary-first ResultDataset metadata.
- `field-dataset-inspect` prints field-capable metadata and array summaries.
- No external solver, PyVista renderer, or field parser is executed.

## Viewer Philosophy

OSW v0.1 favors summary-first inspection:
- show dataset identity, units, dimensions, and available arrays first
- keep heavy rendering optional
- report missing optional visualization dependencies as diagnostics
- avoid claiming full solver field parsing until parser support exists

## ResultViewer / FieldViewer Workflow

The GUI workflow follows the same summary-first path as the CLI:

1. Open or build a result catalog.
2. Select a dataset in the ResultViewer catalog selector.
3. Read the catalog summary for dataset count, dataset type counts, active
   selection, source summary, and diagnostics count.
4. Read the dataset details for source kind, scalar/series/table/figure/artifact
   counts, field-array count, and diagnostics.
5. Use the handoff labels to see whether the current dataset is shown in the
   Plot Viewer, Table Viewer, Field Viewer, Figure handoff, and report summary
   paths.
6. Use the FieldViewer panel for field array and artifact summaries.

The FieldViewer panel lists scalar and vector field metadata, source artifact
paths, artifact state, and optional PyVista/fallback status. It keeps field
metadata inspectable even when PyVista is missing. The viewer does not execute
solvers, scripts, or external commands.

Report handoff remains data-first: datasets with scalar summaries, series,
tables, figures, or diagnostics are marked as report compatible so the same
information can be summarized by report tooling where already supported.

## Current Limitations

- Full CalculiX FRD field parsing is deferred.
- Full OpenFOAM field parsing is deferred.
- FieldViewer does not render vector glyphs. Mesh Viewer provides bounded
  preview-only glyph controls/state for compatible three-component vectors;
  live PyVista glyph rendering, arbitrary vector visualization, streamlines,
  tensor visualization, and time animation remain future work.
- PyVista is optional and is not required for result or field metadata
  inspection.
- Users should validate engineering results independently.
