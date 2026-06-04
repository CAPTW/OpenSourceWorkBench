# Live Optional Solver Environment Validation

Date: 2026-06-04

Public prerelease: `v0.1.3-rc1`

Repository HEAD validated: `fe1ba9228570ced230d0998242a981fe1e51e8f1`

Release tag target:
`a6e8d3a8211e02359841d10e1947e16ab847b132`

This page records one local live optional validation pass. It is environment
evidence only. OpenSolver Workbench is educational/research software, not an
industrial-certified solver platform, and users must validate engineering
results independently. External solvers and optional science packages are not
bundled with OSW.

## Environment Summary

| Item | Value |
| --- | --- |
| OSW import path | `D:\dev\repos\Workbench\src\osw\__init__.py` |
| OSW version | `0.1.3rc1` |
| Python executable | `D:\dev\repos\Workbench\.venv\Scripts\python.exe` |
| Evidence root | `artifacts/validation/live_optional/OSW-VALID-001/` |
| Summary JSON | `artifacts/validation/live_optional/OSW-VALID-001/live_optional_validation_summary.json` |

## Installed / Missing Matrix

| Target | Status | Evidence |
| --- | --- | --- |
| PySide6 | installed, pass | Version `6.11.1`; dark and light offscreen GUI screenshots captured under ignored artifacts. |
| Pillow | installed | Version `12.2.0`; available in the local venv. |
| PyVista | missing | Import discovery reported `ModuleNotFoundError`. |
| meshio | missing | Import discovery reported `ModuleNotFoundError`. |
| SciPy | missing | Import discovery reported `ModuleNotFoundError`. |
| hdf5storage | missing | Import discovery reported `ModuleNotFoundError`. |
| h5py | missing | Import discovery reported `ModuleNotFoundError`. |
| CoolProp | missing | `coolprop-check` reported missing package. |
| Cantera | missing | `cantera-check` reported missing package. |
| Gmsh executable | missing | `gmsh-check` reported executable not found. |
| GNU Octave | missing | `octave-check` reported executable not found. |
| CalculiX `ccx` | missing | `calculix-check` reported executable not found. |
| OpenFOAM executables | missing | `openfoam-check` reported `blockMesh`, `icoFoam`, and `simpleFoam` not found. |

## Backend Results

| Backend | Status | Notes |
| --- | --- | --- |
| PySide6 GUI capture | pass | `tools/ui/capture_main_window.py` captured dark and light themes offscreen at 1600 x 900. |
| PyVista | skipped-missing | Optional package was not installed; no render smoke was run. |
| meshio | skipped-missing | Optional package was not installed; no mesh conversion smoke was run. |
| Gmsh | skipped-missing | Executable was not found; no `.geo` or `.msh` live run was attempted. |
| GNU Octave | skipped-missing | Executable was not found; no `.m` script was run. |
| CalculiX `ccx` | skipped-missing | Executable was not found; no solver run was attempted. |
| OpenFOAM | skipped-missing | Required executables were not found; no case run was attempted. |
| MAT/SciPy | skipped-missing | SciPy and v7.3 MAT optional packages were not installed; no MAT file was fabricated. |
| CoolProp | skipped-missing | Optional package was not installed; no property calculation was run. |
| Cantera | skipped-missing | Optional package was not installed; no reactor calculation was run. |

## Artifact Paths

Runtime artifacts are intentionally ignored and must not be committed:

- `artifacts/validation/live_optional/OSW-VALID-001/discovery/python_packages.json`
- `artifacts/validation/live_optional/OSW-VALID-001/discovery/executables.json`
- `artifacts/validation/live_optional/OSW-VALID-001/discovery/cli_checks.json`
- `artifacts/validation/live_optional/OSW-VALID-001/gui/dark.png`
- `artifacts/validation/live_optional/OSW-VALID-001/gui/light.png`
- `artifacts/validation/live_optional/OSW-VALID-001/live_optional_validation_summary.json`

## Related Issues

- #6 Run live Gmsh validation
- #7 Run live GNU Octave validation
- #8 Run live CalculiX ccx validation
- #9 Run live OpenFOAM validation
- #10 Run live CoolProp and Cantera validation
- #11 Run live PyVista and meshio validation

## Follow-Up

Use later environment-specific validation runs to fill in the missing optional
backend evidence. Missing optional dependencies are expected on many machines
and do not block base import, CLI smoke, or unit tests.
