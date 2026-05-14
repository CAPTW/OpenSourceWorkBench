# Changelog

All notable OpenSolver Workbench changes are summarized here for release
review. OSW follows source-first release evidence; public tags are created only
by a dedicated release/tag gate.

## 0.1.0rc1 - Draft

Release candidate package version: `0.1.0rc1`

Planned release-candidate tag: `v0.1.0-rc1`

No Git tag is created by the release-notes step.

### Highlights

- PySide6 GUI shell with preview-oriented workflows.
- Plugin/add-in architecture for importers, solvers, script workflows,
  post-processing, and reports.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset
  contracts.
- Standard/exported CAD and mesh import policy; no native commercial CAD direct
  import claim.
- meshio, Gmsh, and PyVista pipeline surfaces with optional dependency
  diagnostics.
- CalculiX linear static cantilever demo with input deck generation, optional
  runner diagnostics, result summaries, and validation helper.
- OpenFOAM cavity and duct template demos; no full OpenFOAM UI or broad solver
  coverage claim.
- Cantera and CoolProp basic chemistry/property demos with optional dependency
  diagnostics.
- MATLAB/Octave `.m` and `.mat` preview-first workflow; script execution remains
  explicit and user-triggered.
- FigureDataset, ResultDataset, and HTML report workflow with assumptions,
  warnings, validation notes, and known limitations.
- Validation matrix, golden tests, physical sanity checks, and local QA harness
  for release readiness review.
- Plugin install, manifest validation, and health reporting surfaces designed to
  avoid executing plugin code during manifest validation.

### Known Limitations

- OSW v0.1 is educational and research oriented; it is not industrial
  certified and does not replace expert engineering judgment.
- Simulink, `.slx`, and `.mlapp` workflows are not supported.
- Commercial native CAD direct import is not supported. Use standard/exported
  formats such as STEP, STL, OBJ, IGES, or mesh formats.
- OSW is not a MATLAB clone, ANSYS clone, commercial CAD replacement, process
  simulator, or full OpenFOAM UI.
- OpenFOAM support is limited to bounded cavity and duct templates.
- Optional external solvers and tools such as CalculiX, OpenFOAM tools, Gmsh,
  GNU Octave, and SU2 are not bundled by default.
- Optional Python stacks such as PySide6, meshio, PyVista, Cantera, CoolProp,
  SciPy, and hdf5storage may be absent in base environments and should produce
  diagnostics or skips rather than hidden success.
- The broad default `pytest -q` command has a P2 follow-up for duplicate test
  module basename collection behavior if still present; CI-style split suites
  and importlib-mode collection are the current release evidence path.
- `tools/qa/check_docs_links.py` remains a P2 follow-up if still absent; docs
  link checking is recorded as a placeholder skip.

### QA Evidence Summary

- Pre-merge QA: `python tools/qa/run_pre_merge_qa.py` is part of the release
  evidence path when available.
- Fast QA: `python tools/qa/run_fast_qa.py` checks CLI version, doctor output,
  unit tests, lint, scope, architecture, and artifact scans.
- Unit, integration, golden, and validation suites are documented in
  `docs/10_release_checklist.md`.
- Optional external solver smoke checks remain environment-specific and are not
  required for base release-candidate metadata.

### Release Discipline

- Repository source license: `GPL-3.0-or-later`.
- The `LICENSE` file contains canonical GNU GPL version 3 text; the "or later"
  grant is recorded in project metadata and release documentation.
- Third-party dependency and optional solver notices are tracked in
  `docs/14_third_party_notices.md`.
- Source and wheel artifacts may be prepared only after the dedicated release/tag
  gate passes. External solver binaries are not bundled by default.
