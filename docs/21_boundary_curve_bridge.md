# Boundary Curve Bridge

`OSW-FUNC-010_BOUNDARY_CURVE_BRIDGE` adds reusable boundary-curve data records
for script, MAT, workspace, CSV, and FigureDataset-derived data. It is a data
normalization layer only. It does not generate CalculiX, OpenFOAM, SU2, or other
solver boundary files, and it does not execute `.m` files, MATLAB, Octave, or
external commands.

## Data Model

The model lives in `osw.core.boundary_curve`:

- `CurveAxis`: axis name, unit, independent/dependent role, description, and
  metadata.
- `BoundaryCurveSource`: source type, source file, run id, dataset id,
  x/y variable names, creation timestamp, and metadata.
- `BoundaryCurve`: curve id, display name, kind, x/y axes, x/y numeric values,
  interpolation, source trace, diagnostics, and metadata.

Supported curve kinds include time series, spatial profile, temperature,
pressure, velocity, heat-flux, and generic x/y curves. Interpolation is metadata
only in this step.

## Validation

Validation reports:

- missing x/y values;
- mismatched x/y lengths;
- fewer than two points for interpolated curves;
- non-finite values;
- missing x/y units;
- duplicate x values;
- non-monotonic x values for time/spatial profiles;
- obvious y-unit mismatches for temperature, pressure, velocity, and heat flux;
- missing source trace.

Warnings keep preview workflows usable while surfacing assumptions. Errors block
creating a curve from invalid numeric data.

## Conversion

Supported conversion helpers:

```powershell
.venv\Scripts\python.exe -m osw.cli curve-from-csv tests\fixtures\curves\time_temperature.csv --x-column time_s --y-column temperature_C --x-unit s --y-unit degC --out artifacts\curves\time_temperature_curve.json
.venv\Scripts\python.exe -m osw.cli curve-inspect artifacts\curves\time_temperature_curve.json
.venv\Scripts\python.exe -m osw.cli curve-export-csv artifacts\curves\time_temperature_curve.json --out artifacts\curves\time_temperature_curve.csv
```

`curve-from-mat` uses the MAT reader and only works when the requested MAT
variables are available as already-loaded numeric values. If SciPy is missing,
the command reports the existing friendly MAT dependency diagnostic. Summary-only
MAT metadata reports that full values are unavailable for boundary-curve
conversion.

## ProjectSchema Binding

ProjectSchema stores curves under `boundary_curves`. Boundary conditions can
reference a curve with:

- `curve_id`
- `curve_role`

Existing static boundary values remain valid, and the HeatSink_Flow demo rows
are unchanged. Project validation warns when a boundary condition references a
missing curve or when the boundary type appears inconsistent with the referenced
curve kind.

## GUI Binding

The GUI adds a compact preview-only curve surface:

- `BoundaryCurveDialog`
- `BoundaryCurvePanel`

The panel shows name, kind, units, interpolation, x/y preview rows, and
validation diagnostics. The project tree only shows a Boundary Curves group when
the active project contains curves. The properties panel can display selected
curve summaries and boundary-condition curve references.

The GUI does not run solvers, scripts, MATLAB, Octave, or subprocesses.

## Plugin Metadata

The built-in M-Script preview manifest now advertises data-only curve bridge
capabilities:

- `boundary_curve_export`
- `mat_variable_to_boundary_curve`
- `workspace_variable_to_boundary_curve`
- `csv_to_boundary_curve`

These are conversion capabilities, not solver-adapter capabilities.

## Known Limitations

- No solver-specific boundary file generation.
- No curve fitting or unit conversion engine.
- MAT conversion requires actual numeric values, not summary-only metadata.
- FigureDataset conversion requires workspace variable summaries that carry
  numeric values in metadata.
- Interpolation is stored as policy metadata; evaluation is deferred.

## Next Step

Next functional step: `OSW-FUNC-011_REPORT_GENERATOR_BINDING`.
