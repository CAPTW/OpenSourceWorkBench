# OpenSolver Workbench

OpenSolver Workbench (OSW) is an open-source educational and research
Engineering Solver and Script Workbench. The v0.1 goal is a safe, inspectable
desktop workbench for demonstrating solver workflows, data exchange,
validation, result review, and HTML report generation.

OSW v0.1 is not a MATLAB, ANSYS, Simulink, SolidWorks, CATIA, NX, Creo,
industrial-certified CAE, or commercial CAD replacement. It does not support
native commercial CAD direct import, Simulink, `.slx`, `.mlapp`, full OpenFOAM
coverage, full MATLAB toolbox compatibility, or GUI direct solver subprocess
execution.

## Release Status

Current package metadata is `0.1.3rc1`. OSW-AUTO-077 published the historical
`develop` branch state and annotated `v0.1.2` tag to GitHub at commit
`c39f21372ef837f096aa0d430cced82adc6f3485`. OSW-RELEASE-008 later pushed only
the annotated `v0.1.3-rc1` tag to `origin`, and OSW-RELEASE-009 verified that
the remote tag peels to
`a6e8d3a8211e02359841d10e1947e16ab847b132`. Current local `develop` is newer
than both tag targets because it includes post-push release docs and handoff
status. Do not move or recreate historical tags. Branch push, GitHub Release
page, package artifacts, installers, and public announcement text remain
separate maintainer-controlled gates. Optional external solvers remain
user-installed local tools. See the [Changelog](CHANGELOG.md) for the recorded
source-release and tag-only release-candidate evidence.

The v0.1 functional release gate passed with warnings on 2026-06-02. Optional
live dependencies were missing locally, duplicate desktop `* (1)` files were
quarantined during post-freeze hygiene, and a stale duplicate editable `.pth`
in the local venv was repaired during release-line reconciliation. This is an
internal v0.1 release-candidate handoff, not a final public release announcement
or tag push.

See [v0.1 Release Candidate](docs/release/v0_1_release_candidate.md),
[v0.1 Freeze Handoff](docs/release/v0_1_freeze_handoff.md),
[v0.1 Release Notes](docs/release/v0_1_release_notes.md),
[Release Checklist](docs/10_release_checklist.md), and
[Validation Matrix](docs/04_validation_matrix.md).

## Install Quickstart

Base install keeps heavy optional dependencies out of the bootstrap path.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m osw.cli --help
python -m osw.cli doctor
```

GUI install:

```powershell
python -m pip install -e ".[gui]"
python -m osw.cli gui
```

Developer install:

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/unit -q
python -m pytest tests/integration -q -m "not external_solver"
python -m pytest tests/integration -q -m external_solver
ruff check src tests
```

Run the `external_solver` command only on machines where the relevant optional
tools are intentionally installed and configured.

Research/dev install with optional Python stacks:

```powershell
python -m pip install -e ".[gui,viz,mesh,mscript,chm]"
```

External executables such as Gmsh, GNU Octave, CalculiX `ccx`, and OpenFOAM are
not bundled and are never required for base CLI smoke or unit tests.

## CLI Smoke Examples

```powershell
python -m osw.cli project-demo-json --out artifacts\release\demo_project.json
python -m osw.cli project-validate artifacts\release\demo_project.json
python -m osw.cli plugins-health
python -m osw.cli report-export artifacts\release\demo_project.json --out artifacts\release\demo_report.html
python -m osw.cli result-catalog-inspect tests\fixtures\results\mixed_result_catalog.json
python -m osw.cli field-dataset-inspect tests\fixtures\fields\scalar_field_dataset.json
```

Generated outputs under `artifacts/*` are local runtime artifacts and should not
be committed.

## Documentation

- [Packaging and Release Docs](docs/32_packaging_release_docs.md)
- [v0.1 Freeze Handoff](docs/release/v0_1_freeze_handoff.md)
- [v0.1 Release Notes](docs/release/v0_1_release_notes.md)
- [v0.1 Handoff Manifest](docs/release/v0_1_handoff_manifest.md)
- [Windows Install](docs/install/windows.md)
- [Linux Install](docs/install/linux.md)
- [Source and Development Install](docs/install/source_install.md)
- [Optional Dependencies](docs/install/optional_dependencies.md)
- [Known Limitations](docs/release/known_limitations_v0_1.md)
- [Plugin Install Hardening](docs/33_plugin_install_hardening.md)
- [Tutorials](docs/tutorials.md)
- [Demo Smoke Checklist](docs/demo_smoke_checklist.md)
- [Architecture](docs/02_architecture.md)
- [Plugin Contract](docs/03_plugin_contract.md)

## v0.1 Feature Coverage

The v0.1 candidate covers the frozen PySide6 GUI shell, ProjectSchema,
manifest-first Plugin Manager, runner diagnostics, mesh bridge, Gmsh primitive
`.geo` generation, M-Script preview, optional Octave runner, FigureDataset, MAT
reader, BoundaryCurve, report generator, CalculiX deck/runner/parser,
OpenFOAM templates/residual parser, CHM CoolProp/Cantera adapters,
ResultViewer, and FieldViewer metadata paths.

Missing optional dependencies should produce friendly diagnostics or skips. A
missing optional dependency is not a base install failure.

## License

OpenSolver Workbench source is licensed under
[GPL-3.0-or-later](LICENSE). External solver binaries and optional tools are
user-installed local dependencies and are not bundled by OSW v0.1.
