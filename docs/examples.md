# Examples

This index mirrors [examples/README.md](../examples/README.md) for readers who
start in the `docs/` tree. Use it with the
[tutorial ladder](tutorials/README.md). Commands use existing fixtures or
generated files under `artifacts/*`; they do not execute external solvers unless
the command name explicitly says it is a runner command.

## Zero-Dependency Examples

These should work from the repository venv without external solver executables.

## Demo Project JSON

```powershell
.\.venv\Scripts\python.exe -m osw.cli project-demo-json --out artifacts\examples\demo_project.json
.\.venv\Scripts\python.exe -m osw.cli project-validate artifacts\examples\demo_project.json
```

Expected result: a HeatSink_Flow demo project and validation output. Demo script
preview warnings are expected until scripts are scanned and accepted.

## Plugin Health

```powershell
.\.venv\Scripts\python.exe -m osw.cli plugins-health
```

Expected result: discovered local plugin manifests or a clear message that none
were found. Plugin health does not import arbitrary plugin code.

## M-Script Preview

```powershell
.\.venv\Scripts\python.exe -m osw.cli mscript-preview tests\fixtures\mscript\simple_plot.m
.\.venv\Scripts\python.exe -m osw.cli mscript-scan tests\fixtures\mscript\dangerous_system.m
```

Expected result: script classification and safety findings. Preview and scan do
not execute MATLAB, Octave, shell commands, or network calls.

## MAT Info

```powershell
.\.venv\Scripts\python.exe -m osw.cli mat-info tests\fixtures\mat\numeric_arrays.mat
```

Expected result: variable metadata if SciPy MAT support is installed, or a
friendly dependency diagnostic if the `.[mscript]` optional extra is missing.

## BoundaryCurve Inspection

```powershell
.\.venv\Scripts\python.exe -m osw.cli curve-inspect tests\fixtures\curves\boundary_curve_valid.json
```

Expected result: curve id, units, point count, and validation messages.

## CalculiX Result Summary Fixture

```powershell
.\.venv\Scripts\python.exe -m osw.cli calculix-results-summary tests\fixtures\calculix\results\simple_success.dat
```

Expected result: parsed summary from an existing fixture. This command does not
run `ccx`.

## OpenFOAM Residual Log Fixture

```powershell
.\.venv\Scripts\python.exe -m osw.cli openfoam-parse-log tests\fixtures\openfoam\residual_simple.log
```

Expected result: residual history parsed from an existing log fixture. This
command does not run OpenFOAM.

## Result Catalog Inspection

```powershell
.\.venv\Scripts\python.exe -m osw.cli result-catalog-inspect tests\fixtures\results\mixed_result_catalog.json
```

Expected result: catalog summary for curated ResultDataset fixtures.

## Field Dataset Inspection

```powershell
.\.venv\Scripts\python.exe -m osw.cli field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
```

Expected result: scalar and vector field metadata for the tiny VTK fixture.

## Report Export

```powershell
.\.venv\Scripts\python.exe -m osw.cli project-demo-json --out artifacts\examples\report_project.json
.\.venv\Scripts\python.exe -m osw.cli report-export artifacts\examples\report_project.json --out artifacts\examples\report.html
```

Expected result: deterministic HTML report output under `artifacts/*`. Report
export is data-only and does not execute solvers or scripts.

## GUI Examples

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[gui]"
.\.venv\Scripts\python.exe -m osw.cli gui
```

Expected result: the optional PySide6 GUI launches on desktop machines. In
headless shells, use the screenshots in
[First GUI Walkthrough](tutorials/first_gui_walkthrough.md) to understand the
layout.

## Optional Solver Examples

These require user-installed external executables and should be run only when
the matching diagnostic passes:

| Workflow | Diagnostic | Safe fixture or preview path |
| --- | --- | --- |
| Gmsh | `gmsh-check` | `gmsh-write-geo` writes `.geo` without running Gmsh. |
| GNU Octave | `octave-check` | `mscript-preview` and `mscript-scan` do not execute `.m` files. |
| CalculiX | `calculix-check` | `calculix-results-summary` parses existing fixtures without running `ccx`. |
| OpenFOAM | `openfoam-check` | `openfoam-parse-log` parses existing log fixtures without running OpenFOAM. |

## Optional Scientific Backend Examples

These require optional Python packages and should report diagnostics when
missing:

| Workflow | Diagnostic | Notes |
| --- | --- | --- |
| MAT files | install `.[mscript]`; run `mat-info` | MAT inspection does not run MATLAB or Octave. |
| CoolProp | `coolprop-check` | Property examples are bounded and non-certifying. |
| Cantera | `cantera-check` | Reactor examples are bounded and non-certifying. |
| PyVista/meshio | install `.[viz,mesh]` | Field rendering and mesh conversion remain optional. |

## Release/Maintenance Examples

- [Release Asset Smoke Walkthrough](tutorials/release_asset_smoke_walkthrough.md)
  verifies release assets without uploading or editing them.
- [Post-Public Release Checklist](release/post_public_release_checklist.md)
  separates tag, branch, asset, issue, and release mutations into explicit
  gates.

## Safety Notes

- Treat `.m` and `.mat` inputs as untrusted until previewed.
- Generated case files and reports under `artifacts/*` are runtime outputs.
- Missing optional dependencies should produce diagnostics, not hidden success.
- OSW v0.1 is not industrial certified and is not a production CAE tool.
