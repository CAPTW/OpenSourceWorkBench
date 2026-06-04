# OpenSolver Workbench

OpenSolver Workbench (OSW) is an educational/research open-source Engineering
Solver & Script Workbench for inspectable desktop workflows, solver case
preparation, script previews, result review, and report generation.

OSW v0.1.3rc1 is a source release candidate. It is useful for teaching,
research prototyping, and transparent workflow experiments, but it is not an
industrial-certified CAE tool, MATLAB clone, ANSYS clone, Simulink clone, or
commercial CAD replacement.

## What This Is

- A plugin-based desktop workbench built around small, typed project and result
  contracts.
- A PySide6 GUI shell for project navigation, properties, result previews, and
  report status.
- A CLI for standard engineering file workflows, plugin health checks, demo
  projects, result inspection, and report summaries.
- A guarded integration layer for solvers, scripts, result datasets, field
  metadata, and HTML reports.

The core package stays lightweight. GUI, mesh, visualization, script, chemistry,
and external solver integrations are optional and should fail with clear
diagnostics when a dependency is missing.

## What Works In v0.1.3rc1

- GUI baseline with Dark, Light, and System themes.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, FigureDataset, and
  BoundaryCurve contracts.
- HeatSink_Flow demo project generation and validation.
- Plugin contract, manifest discovery, plugin health, manager UI, and local
  folder/ZIP install hardening.
- Runner diagnostics and explicit external-command safety boundaries.
- Mesh metadata bridge, optional meshio path, and bounded Gmsh primitive `.geo`
  generation.
- CalculiX input deck generation, explicit runner path, parser fixtures, and
  summary/validation helpers.
- OpenFOAM cavity/duct template paths and residual parser.
- MATLAB/Octave `.m` preview, GNU Octave runner path, FigureDataset handoff,
  MAT reader, and curve bridges.
- Report generator plus ResultViewer and FieldViewer metadata surfaces.
- CoolProp and Cantera optional CHM adapters with guarded dependency checks.

## Quickstart

Windows source install:

```powershell
git clone https://github.com/CAPTW/OpenSourceWorkBench.git
cd OpenSourceWorkBench
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[gui]"
```

CLI and GUI smoke:

```powershell
.\.venv\Scripts\python.exe -m osw.cli --help
.\.venv\Scripts\python.exe -m osw.cli plugins-health
.\.venv\Scripts\python.exe -m osw.cli gui
```

Demo project and report summary:

```powershell
.\.venv\Scripts\python.exe -m osw.cli project-demo-json --out artifacts\demo_project.json
.\.venv\Scripts\python.exe -m osw.cli project-validate artifacts\demo_project.json
.\.venv\Scripts\python.exe -m osw.cli report-summary artifacts\demo_project.json
```

Generated files under `artifacts/*` are local runtime outputs and should not be
committed. For more commands and troubleshooting, see
[Quickstart](docs/quickstart.md) and the
[post-public-release roadmap](docs/roadmap/README.md).

Developer checks:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -q
.\.venv\Scripts\python.exe -m pytest tests/integration -q -m "not external_solver"
.\.venv\Scripts\python.exe -m pytest tests/integration -q -m external_solver
.\.venv\Scripts\python.exe -m ruff check src tests tools
```

Run the `external_solver` integration subset only on machines where the relevant
optional executable is intentionally installed and configured.

## Screenshots

| Dark theme | Light theme | System theme |
| --- | --- | --- |
| ![OpenSolver Workbench dark theme](docs/assets/screenshots/osw_dark.png) | ![OpenSolver Workbench light theme](docs/assets/screenshots/osw_light.png) | ![OpenSolver Workbench system theme](docs/assets/screenshots/osw_system.png) |

The screenshots are offscreen captures of the v0.1 GUI baseline. They show the
intended layout and preview surfaces; they are not claims of solver accuracy or
production readiness.

## Examples

Start with [Examples](examples/README.md) or the mirrored
[examples index](docs/examples.md). The examples use existing fixtures and safe
preview commands:

- Demo project JSON generation and validation.
- Plugin health diagnostics.
- MATLAB/Octave script preview and safety scan.
- MAT-file info with optional dependency diagnostics.
- BoundaryCurve CSV/JSON inspection.
- CalculiX result summary fixtures.
- OpenFOAM residual log parsing fixtures.
- Result catalog and field dataset inspection.
- HTML report export from the demo project.

## Optional Dependencies

Install only the extras needed for the workflow you are testing:

- `.[gui]`: PySide6 GUI.
- `.[mesh]`: meshio and the Gmsh Python package path.
- `.[viz]`: PyVista and Matplotlib visualization helpers.
- `.[mscript]`: SciPy and hdf5storage for MAT workflows.
- `.[chm]`: CoolProp and Cantera chemistry/thermophysical demos.
- External executables: Gmsh, GNU Octave, CalculiX `ccx`, and OpenFOAM are
  optional user-installed tools.
- PyYAML is optional for YAML project files.

Missing optional dependencies are expected on many machines. OSW should report
diagnostics or skips rather than pretending a workflow succeeded.

## Known Limitations

- No industrial certification or production CAE accuracy claim.
- No native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
- No Simulink, `.slx`, or `.mlapp` compatibility.
- No full OpenFOAM GUI/editor or broad solver coverage.
- No full CalculiX FRD field parser.
- No full OpenFOAM field parser.
- No plugin signing, remote plugin marketplace, or dependency auto-install.
- No MSI installer or code signing yet.
- The GitHub Release for `v0.1.3-rc1` is a public prerelease with assets; it is
  not a stable production release.

See [Known Limitations For v0.1](docs/release/known_limitations_v0_1.md) for
the full public scope note.

## Release Status

- Package metadata: `0.1.3rc1`.
- Candidate tag: `v0.1.3-rc1`.
- Tag target:
  `a6e8d3a8211e02359841d10e1947e16ab847b132`.
- Current `develop` includes post-tag documentation/status updates.
- A public GitHub Release prerelease exists for `v0.1.3-rc1`.
- Release assets are attached: wheel, sdist, Windows portable ZIP, checksums,
  and manifest.
- Future maintenance and feature work are tracked in the
  [post-public-release roadmap](docs/roadmap/README.md).
- Package publication, installer/signing work, and public announcement text
  require separate maintainer-approved gates.

Useful release docs:

- [v0.1.3rc1 Release Summary](docs/release/v0_1_3rc1_release_summary.md)
- [v0.1 Release Notes](docs/release/v0_1_release_notes.md)
- [Release Checklist](docs/10_release_checklist.md)
- [Validation Matrix](docs/04_validation_matrix.md)
- [Post-Public-Release Roadmap](docs/roadmap/README.md)
- [Optional Dependencies](docs/install/optional_dependencies.md)

## License

OpenSolver Workbench source is licensed under
[GPL-3.0-or-later](LICENSE). External solver binaries and optional tools are
user-installed local dependencies and are not bundled by OSW v0.1.
