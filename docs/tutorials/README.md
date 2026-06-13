# Tutorials

Start here if you are new to OpenSolver Workbench. The tutorials are ordered
from no-solver CLI checks to optional GUI and release-maintainer workflows.

OSW v0.1.3rc1 is a public prerelease for educational and research workflows. It
is not a stable production solver, industrial-certified CAE tool, MATLAB clone,
ANSYS clone, Simulink clone, or commercial CAD replacement.

## Tutorial Order

| Tutorial | Path | Dependencies | What you should learn |
| --- | --- | --- | --- |
| First CLI walkthrough | [first_cli_walkthrough.md](first_cli_walkthrough.md) | Python venv only; no external solvers | Run version/help, create a demo project, validate it, and print a report summary. |
| Result dataset walkthrough | [result_dataset_walkthrough.md](result_dataset_walkthrough.md) | Python venv only; no external solvers | Inspect tiny ResultDataset and field metadata fixtures. |
| FEASpec CalculiX export preview | [feaspec_calculix_export_preview.md](feaspec_calculix_export_preview.md) | Python venv only; no external solvers | Preview FEASpec-to-CalculiX no-run export readiness, diagnostics, and planned files without writing bundles or running solvers. |
| First GUI walkthrough | [first_gui_walkthrough.md](first_gui_walkthrough.md) | `.[gui]` / PySide6 | Launch the GUI and understand the main panes. |
| Release asset smoke walkthrough | [release_asset_smoke_walkthrough.md](release_asset_smoke_walkthrough.md) | Python venv; GitHub CLI only for live download mode | Verify release assets without editing releases or uploading files. |

## Dependency Levels

Level 0, read-only overview:
- read [README](../../README.md), [Known Limitations](../release/known_limitations_v0_1.md), and [Examples](../examples.md)
- understand that `v0.1.3-rc1` is a prerelease

Level 1, no optional solver dependencies:
- install from source
- run CLI version/help
- generate and validate a demo project
- inspect result fixtures
- preview FEASpec CalculiX export readiness without writing files or running
  external solvers
- keep generated files under ignored `artifacts/*`

Level 2, GUI path:
- install `.[gui]`
- launch `python -m osw.cli gui`
- use screenshots to understand layout when running headless
- open Plugin Manager to inspect local plugin receipts, quarantine/rejection
  records, and managed-root uninstall safety boundaries

Level 3, optional backend path:
- Gmsh, GNU Octave, CalculiX `ccx`, OpenFOAM, CoolProp, Cantera, PyVista,
  meshio, SciPy, hdf5storage, and h5py are optional
- missing tools should produce diagnostics, not hidden success

Level 4, maintainer path:
- run docs links and public docs QA
- use release asset smoke in offline fixture mode before live download mode
- keep issue, release, asset, and tag mutations behind explicit gates

## Install References

- [Quickstart](../quickstart.md)
- [Source Install](../install/source_install.md)
- [Optional Dependencies](../install/optional_dependencies.md)
- [Examples Index](../examples.md)

Generated files in these tutorials go under `artifacts/tutorials/`, which is an
ignored runtime output path.
