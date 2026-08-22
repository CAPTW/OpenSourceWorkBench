# OpenSolver Workbench Examples

These examples are small source-tree workflows for the current `develop` line. Package metadata is `0.1.5rc3`, and `v0.1.5-rc2` is the current public prerelease. They are intended for inspection and teaching, not production or regulated engineering use.

Run commands from the repository root with the repo venv:

```powershell
.\.venv\Scripts\python.exe -m osw.cli --help
```

## Zero-Dependency Examples

These work from a normal source checkout without Gmsh, Octave, CalculiX,
OpenFOAM, CoolProp, Cantera, PyVista, or meshio.

| Example | Command | Expected result |
| --- | --- | --- |
| Demo project JSON | `project-demo-json --out artifacts\examples\demo_project.json` | Writes a HeatSink_Flow ProjectSchema JSON file. |
| Plugin health | `plugins-health` | Lists local plugin manifests or reports none found. |
| M-Script preview | `mscript-preview tests\fixtures\mscript\simple_plot.m` | Previews `.m` metadata without execution. |
| M-Script safety scan | `mscript-scan tests\fixtures\mscript\dangerous_system.m` | Reports risky shell-command findings. |
| MAT info | `mat-info tests\fixtures\mat\numeric_arrays.mat` | Shows MAT variables, or a friendly missing SciPy/hdf5storage diagnostic. |
| BoundaryCurve inspect | `curve-inspect tests\fixtures\curves\boundary_curve_valid.json` | Shows curve metadata and validation state. |
| CalculiX fixture summary | `calculix-results-summary tests\fixtures\calculix\results\simple_success.dat` | Parses existing `.dat` fixture without running `ccx`. |
| OpenFOAM residual fixture | `openfoam-parse-log tests\fixtures\openfoam\residual_simple.log` | Parses an existing log fixture without running OpenFOAM. |
| Result catalog inspect | `result-catalog-inspect tests\fixtures\results\mixed_result_catalog.json` | Summarizes curated result datasets. |
| Field dataset inspect | `field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json` | Lists scalar/vector field metadata. |
| Report export | `report-export artifacts\examples\demo_project.json --out artifacts\examples\report.html` | Writes a deterministic HTML report. |

## GUI Examples

Install `.[gui]`, then launch:

```powershell
.\.venv\Scripts\python.exe -m osw.cli gui
```

See [First GUI Walkthrough](../docs/tutorials/first_gui_walkthrough.md) for
screenshots and pane descriptions. PySide6 is optional, and headless
environments may skip GUI launch.

## Optional Solver Examples

These examples remain optional and diagnostic-driven:

| Example | Requires | Safe default |
| --- | --- | --- |
| [03 Gmsh Meshing](03_gmsh_meshing/README.md) | Gmsh for real mesh generation | Generate `.geo` first and run `gmsh-check`. |
| [04 CalculiX Cantilever](04_calculix_cantilever/README.md) | CalculiX `ccx` for live solve | Parse fixture results without running `ccx`. |
| [05 OpenFOAM Cavity And Duct Templates](05_openfoam_cavity/README.md) | OpenFOAM for live run | Write template cases or parse fixture logs. |
| [08 MATLAB/Octave Figure Preview](08_mscript_figure/README.md) | GNU Octave only for explicit run | Preview and scan `.m` files without execution. |

## Optional Scientific Backend Examples

| Example | Requires | Missing dependency behavior |
| --- | --- | --- |
| [06 Cantera Reactor](06_cantera_reactor/README.md) | Cantera | Diagnostic, no hidden success. |
| [07 CoolProp Property](07_coolprop_property/README.md) | CoolProp | Diagnostic, no hidden success. |
| MAT and figure inspection | SciPy/hdf5storage/h5py where needed | Friendly MAT support diagnostic. |
| Mesh/field visualization | meshio/PyVista where needed | Metadata inspection remains available. |

## Copy-Paste Smoke

```powershell
.\.venv\Scripts\python.exe -m osw.cli plugins-health
.\.venv\Scripts\python.exe -m osw.cli project-demo-json --out artifacts\examples\demo_project.json
.\.venv\Scripts\python.exe -m osw.cli project-validate artifacts\examples\demo_project.json
.\.venv\Scripts\python.exe -m osw.cli report-summary artifacts\examples\demo_project.json
.\.venv\Scripts\python.exe -m osw.cli mscript-preview tests\fixtures\mscript\simple_plot.m
.\.venv\Scripts\python.exe -m osw.cli result-catalog-inspect tests\fixtures\results\mixed_result_catalog.json
.\.venv\Scripts\python.exe -m osw.cli field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
```

Expected result:

- Demo project and report outputs are written under ignored `artifacts/*`.
- Script preview does not run MATLAB, Octave, shell commands, or network calls.
- Optional dependency gaps are reported as diagnostics.

## Existing Tutorial Folders

- [00 Empty Project](00_empty_project/README.md)
- [01 STEP Import](01_step_import/README.md)
- [02 Mesh Import](02_mesh_import/README.md)
- [03 Gmsh Meshing](03_gmsh_meshing/README.md)
- [04 CalculiX Cantilever](04_calculix_cantilever/README.md)
- [05 OpenFOAM Cavity And Duct Templates](05_openfoam_cavity/README.md)
- [06 Cantera Reactor](06_cantera_reactor/README.md)
- [07 CoolProp Property](07_coolprop_property/README.md)
- [08 MATLAB/Octave Figure Preview](08_mscript_figure/README.md)
- [09 Report Generator](09_report_generator/README.md)

## Safety Notes

- Start with [Tutorials](../docs/tutorials/README.md) for guided onboarding.
- Preview `.m` files before any execution decision.
- Keep generated outputs in `artifacts/*`.
- Do not commit solver runtime directories, logs, generated reports, or caches.
- Missing Gmsh, Octave, CalculiX, OpenFOAM, CoolProp, Cantera, SciPy, or
  hdf5storage is acceptable for workflows that only inspect fixtures.
- OSW is not an industrial-certified solver platform.
