# OpenSolver Workbench

OpenSolver Workbench (OSW) is an open-source educational and research
Engineering Solver & Script Workbench. The v0.1 goal is a safe, inspectable
desktop workbench for demonstrating solver workflows, data exchange, validation,
and report generation.

## v0.1 Scope

- PySide6 desktop GUI architecture.
- Plugin/add-in contracts for solvers and importers.
- Project schema, units, material database, result dataset, and figure dataset.
- Standard/exported CAD, CAE, CFD, and chemistry formats.
- `meshio`, Gmsh, PyVista, and Matplotlib based workflows.
- CalculiX linear static demo.
- OpenFOAM cavity/duct template demo.
- Cantera and CoolProp basic demos.
- MATLAB/Octave `.m` and `.mat` preview-first workflow.
- HTML reports, validation matrix, and golden tests.

The eight planned v0.1 demos are empty project, STEP import preview, mesh import
preview, Gmsh meshing template, CalculiX cantilever, OpenFOAM cavity/duct
template, Cantera/CoolProp basics, and MATLAB/Octave figure preview.

The expected workflow is Import -> Configure -> Run or prepare a bounded demo
run -> inspect Result/Figure data -> export an HTML report with validation notes.
For v0.1, "Run" may mean case preparation, fixture-backed result inspection, or
a small bounded demo. It does not mean GUI-triggered broad external solver
execution.

## Non-Goals

OSW v0.1 is not a MATLAB, ANSYS, Simulink, SolidWorks, CATIA, NX, or Creo clone.
It does not claim industrial certification. It does not support native
commercial CAD import, Simulink or `.mlapp`, full OpenFOAM coverage, full MATLAB
toolbox compatibility, nonlinear contact/plasticity demos, industrial
certification claims, or GUI-triggered direct subprocess solver execution.

See [Known Limitations](docs/known_limitations.md) for the full v0.1 boundary
statement, including optional dependency behavior and script execution safety.

Release-readiness review uses the [Release Checklist](docs/10_release_checklist.md)
and [v0.1 Demo Smoke Checklist](docs/demo_smoke_checklist.md). License and
release tag planning is tracked in the
[License and Version Plan](docs/13_license_and_version_plan.md).

## Release Status

The final-prep package version is `0.1.0`. Local rc1, rc2, and rc3 tags remain
historical release evidence. The final `v0.1.0` tag, public tag push, release
artifacts, and release announcement are handled by separate
maintainer-controlled gates. See the [Changelog](CHANGELOG.md) for final v0.1.0
release notes and RC3 UAT evidence.

OSW v0.1 is educational and research oriented. It makes no regulated-use or
production-accuracy claim, does not replace expert engineering judgment, and
does not guarantee that optional external solvers are installed in every local
environment.

## License

OpenSolver Workbench source is licensed under
[GPL-3.0-or-later](LICENSE). This is the recorded maintainer decision for
v0.1; see the [License and Version Plan](docs/13_license_and_version_plan.md)
for the version/tag policy and the [Third-Party Notices Draft](docs/14_third_party_notices.md)
for optional dependency notice review areas.

External solver binaries such as CalculiX, OpenFOAM tools, Gmsh, GNU Octave,
and SU2 are optional local runtime tools and are not bundled in v0.1 release
artifacts by default. See [Known Limitations](docs/known_limitations.md) for
scope, validation, optional dependency, and script safety boundaries.

## Quick Start

For full Windows, Linux, conda, pip, uv, optional dependency, and external tool
notes, see the [Installation Guide](docs/install.md).

```powershell
python -m pip install -e ".[dev]"
python -m osw.cli --version
python -m osw.cli doctor
pytest tests/unit -q
ruff check src tests
```

Optional stacks are grouped as extras:

- Base install supports CLI, docs, validation metadata, and HTML report code
  paths without requiring heavy optional stacks.
- `.[gui]` for PySide6.
- `.[mesh]` for mesh import and Gmsh-facing work.
- `.[viz]` for PyVista and Matplotlib.
- `.[thermo]` for Cantera and CoolProp.
- `.[mscript]` for `.mat` preview support.

External solver binaries are not bundled by default. Optional solver stacks and
executables remain user-installed local tools, and missing dependencies should
produce diagnostics or skips rather than blocking the base CLI workflow.

## Local CI Commands

The GitHub Actions workflow is intentionally local-safe and uses the same
commands below. It installs only the base development extra and does not assume
that external solvers or heavy optional stacks are available:

```powershell
python -m pip install -e ".[dev]"
python -m osw.cli --version
python -m osw.cli doctor
ruff check src tests
pytest tests/unit -q
pytest tests/integration -q -m "not external_solver"
pytest tests/golden -q
pytest tests/validation -q
python tools/qa/run_fast_qa.py
python tools/qa/check_scope_drift.py
python tools/qa/check_architecture_boundaries.py
python tools/qa/check_no_solver_artifacts_committed.py
```

Optional executable smoke checks are opt-in. Run them only on a machine where
the relevant dependency is intentionally installed and configured:

```powershell
pytest tests/integration -q -m external_solver
```

Missing external solvers, GNU Octave, Gmsh, Cantera, CoolProp, PySide6, meshio,
or PyVista are expected in many local and CI environments and should be reported
as skipped or optional rather than release blockers for the base workflow.

## Tutorial Examples

The v0.1 tutorial path is documented in [docs/tutorials.md](docs/tutorials.md).
Each example README includes a goal, prerequisites, steps, expected output, and
troubleshooting notes:

- [01 STEP import preview](examples/01_step_import/README.md)
- [02 mesh import preview](examples/02_mesh_import/README.md)
- [03 Gmsh meshing template](examples/03_gmsh_meshing/README.md)
- [04 CalculiX cantilever](examples/04_calculix_cantilever/README.md)
- [05 OpenFOAM cavity and duct templates](examples/05_openfoam_cavity/README.md)
- [06 Cantera reactor](examples/06_cantera_reactor/README.md)
- [07 CoolProp property table](examples/07_coolprop_property/README.md)
- [08 MATLAB/Octave figure preview](examples/08_mscript_figure/README.md)
