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

## Current Limitations

- Full CalculiX FRD field parsing is deferred.
- Full OpenFOAM field parsing is deferred.
- Vector glyphs, streamlines, and time animation are optional future work.
