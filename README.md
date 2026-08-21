# OpenSolver Workbench

OpenSolver Workbench (OSW) is an educational/research open-source Engineering
Solver & Script Workbench for inspectable desktop workflows, solver case
preparation, script previews, result review, and report generation.

OSW package metadata is currently `0.1.5rc1`, and the current public GitHub
prerelease is `v0.1.5-rc1`. It is useful for teaching, research prototyping,
and transparent workflow experiments, but it is not an industrial-certified CAE
tool, MATLAB clone, ANSYS clone, Simulink clone, or commercial CAD replacement.

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

## Try It In 10 Minutes

For a guided first run, use the tutorial ladder:

1. [First CLI Walkthrough](docs/tutorials/first_cli_walkthrough.md)
2. [Result Dataset Walkthrough](docs/tutorials/result_dataset_walkthrough.md)
3. [First GUI Walkthrough](docs/tutorials/first_gui_walkthrough.md)
4. [Release Asset Smoke Walkthrough](docs/tutorials/release_asset_smoke_walkthrough.md)

The first two tutorials need only the source checkout and Python environment.
The GUI tutorial needs the `.[gui]` extra. Optional solver and science backends
remain diagnostic-only until you install them separately.

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
[examples index](docs/examples.md). The examples and
[tutorials](docs/tutorials/README.md) use existing fixtures and safe preview
commands:

- Demo project JSON generation and validation.
- Plugin health diagnostics.
- MATLAB/Octave script preview and safety scan.
- MAT-file info with optional dependency diagnostics.
- BoundaryCurve CSV/JSON inspection.
- CalculiX result summary fixtures.
- OpenFOAM residual log parsing fixtures.
- Result catalog and field dataset inspection.
- HTML report export from the demo project.

## 3D Workspace MVP

The local 3D Workspace MVP user journey is:

`Import/Open → Render → Select → NamedSelection → Solver Setup → Diagnostics →
Results → Probe/Deformation → Save View → Capture → Report → Save Project →
Fresh-Process Reopen → Exact Scene Restore → Stale-Mesh Rejection`.

How to open a supported mesh: create or open a Project, then load an in-memory
or already-imported mesh through the existing 3D viewer. The viewer renders
triangle, quad, polygon surface, and linear tetra cells. `tetra10`, hexahedron,
`hexahedron20`, wedge, and pyramid are unsupported.

Camera, representation, and axes controls live on the viewport toolbar.
Point/cell picking creates canonical NamedSelections. Solver setup kinds are
material region, fixed support, prescribed displacement, force, pressure,
temperature, and heat flux. CalculiX prepare-only handoff supports the first
four; the last three stay explicitly unsupported. The GUI does not launch a
solver.

Scaled Jacobian diagnostics cover triangle, quad, and linear tetra. Interactive
results require an exact mesh fingerprint. Project Save persists
`osw.active_scene.v1`. Screenshot capture and report export are explicit.
Reports use persisted images only. Native locality remains `DEFERRED_RETAINED`.

Renderer-neutral acceptance:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/test_3d_workspace_mvp_end_to_end.py -q
```

Prepared visible native acceptance, each stage in a fresh process:

```powershell
$env:OSW_RUN_PREPARED_INTERACTIVE='1'
$env:OSW_E2E_WORKSPACE_ROOT='C:\temp\osw-mvp-e2e'
$env:OSW_E2E_STAGE='AUTHOR'
python -m pytest tests/gui/test_3d_workspace_mvp_end_to_end_prepared_gui.py -q
$env:OSW_E2E_STAGE='RESTORE'
python -m pytest tests/gui/test_3d_workspace_mvp_end_to_end_prepared_gui.py -q
$env:OSW_E2E_STAGE='STALE'
python -m pytest tests/gui/test_3d_workspace_mvp_end_to_end_prepared_gui.py -q
```

With only `OSW_RUN_PREPARED_INTERACTIVE=1` set, the prepared module orchestrates
AUTHOR, process exit, RESTORE, process exit, and STALE. Historical offscreen
PyVistaQt aggregates may crash on Windows; do not replace this visible path
with offscreen mode. This MVP is for integration review with documented
limitations. It is not production-ready or industrially certified.

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
- **Native report-asset availability resolution is unsupported (`DEFERRED_RETAINED`).** Without an authorized resolver, the manager and report bridge continue to represent typed `external_absolute` and `project_relative` references as `unresolved_no_resolver` placeholders. “Relink selected screenshot…” performs point-in-time selected-file and suffix checks and, only after explicit confirmation plus post-confirmation file and stale-target revalidation, replaces one in-memory Project screenshot record: `external_absolute` remains `external_absolute`, while `project_relative` becomes `external_absolute`. Relink does not perform typed native resolution; the runtime descriptor still has no `effective_path`, the report bridge supplies no usable `image_path`, and the placeholder remains. Saving the Project is separate and explicit. These compatibility checks add no durable claim of existence, readability, locality, containment, link safety, provider silence, sandboxing, race-free consumption, authenticity, malware safety, or production readiness, and make no negative finding about the target. Legacy or unmarked compatibility behavior is separate, may perform filesystem checks, and is not certified provider-silent.
- The GitHub Release for `v0.1.5-rc1` is a public prerelease with assets; it is
  not a stable production release, certification milestone, or bundled-solver
  distribution.

See [Known Limitations For v0.1](docs/release/known_limitations_v0_1.md) for
the full public scope note and [Report Asset Runtime Path Native
Deferral](docs/experimental/report_asset_runtime_path_native_deferral.md) for
the canonical report-asset claim boundary.

## Release Status

- Current `develop` package metadata: `0.1.5rc1`.
- Current public prerelease tag: `v0.1.5-rc1`.
- `develop` may be ahead of the `v0.1.5-rc1` release tag.
- A public GitHub Release prerelease exists for `v0.1.5-rc1`.
- Release assets are attached: wheel, sdist, Windows portable ZIP, checksums,
  and manifest; local validation artifacts are not release assets.
- OpenFOAM v12 template compatibility issues #18 and #19 are closed with
  WSL-scoped evidence. Optional validation issues #6 through #11 are also
  closed after separate bounded evidence and closure gates; each closure remains
  scoped to its issue and is not certification, production-readiness evidence,
  release-readiness evidence, bundled-solver support, or native-Windows
  validation where the evidence was WSL-scoped.
- Future maintenance and feature work are tracked in the
  [post-public-release roadmap](docs/roadmap/README.md).
- Package publication, installer/signing work, and public announcement text
  require separate maintainer-approved gates.

Useful release docs:

- [v0.1.3rc1 Release Summary](docs/release/v0_1_3rc1_release_summary.md)
- [v0.1.4-rc1 Candidate Metadata Alignment](docs/release/v0_1_4_rc1_candidate.md)
- [v0.1.5-rc1 Candidate Metadata Alignment](docs/release/v0_1_5_rc1_candidate.md)
- [v0.1 Release Notes](docs/release/v0_1_release_notes.md)
- [Release Checklist](docs/10_release_checklist.md)
- [Post-Public Release Checklist](docs/release/post_public_release_checklist.md)
- [Validation Matrix](docs/04_validation_matrix.md)
- [Tutorials](docs/tutorials/README.md)
- [Post-Public-Release Roadmap](docs/roadmap/README.md)
- [Windows Portable ZIP](docs/release/windows_portable_zip.md)
- [Code Signing And Installer Strategy](docs/release/code_signing_installer_strategy.md)
- [Optional Dependencies](docs/install/optional_dependencies.md)

## License

OpenSolver Workbench source is licensed under
[GPL-3.0-or-later](LICENSE). External solver binaries and optional tools are
user-installed local dependencies and are not bundled by OSW v0.1.
