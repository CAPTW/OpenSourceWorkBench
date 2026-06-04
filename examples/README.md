# OpenSolver Workbench Examples

These examples are small, source-tree workflows for the v0.1.3rc1 release
candidate. They are designed for inspection and teaching, not for certified
engineering decisions.

Run commands from the repository root with the repo venv:

```powershell
.\.venv\Scripts\python.exe -m osw.cli --help
```

## Index

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

- Preview `.m` files before any execution decision.
- Keep generated outputs in `artifacts/*`.
- Do not commit solver runtime directories, logs, generated reports, or caches.
- Missing Gmsh, Octave, CalculiX, OpenFOAM, CoolProp, Cantera, SciPy, or
  hdf5storage is acceptable for workflows that only inspect fixtures.
- OSW is not an industrial-certified solver platform.
