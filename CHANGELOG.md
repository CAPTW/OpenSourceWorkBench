# Changelog

All notable OpenSolver Workbench changes are summarized here for release
review. OSW follows source-first release evidence; public tags are created only
by a dedicated release/tag gate.

## Unreleased

### v0.1.3rc2 Maintenance Development Cycle Opened

Development package version: `0.1.3rc2.dev0`

- Added reusable release asset download smoke automation for Issue `#2`,
  covering `SHA256SUMS.txt`, `release_asset_manifest.json`, safe archive
  checks, and optional full wheel/sdist/portable ZIP smoke.
- Improved Windows portable ZIP user guidance for Issue `#4`, including
  unsigned/no MSI/no code-signing warnings, no bundled external solver wording,
  checksum verification, and future `README_RUN_FIRST.txt` template guidance.
- Added a read-only `Release asset smoke` GitHub Actions workflow for Issue
  `#2`: pull requests and `develop` pushes use offline release asset fixtures,
  while live GitHub release downloads are manual `workflow_dispatch` only.
- Made the offline release asset fixture byte-stable across CI checkouts so
  `release_asset_manifest.json` checksum verification is not changed by Git
  line-ending normalization.
- Recorded a `v0.1.3rc2` maintenance revalidation baseline covering release
  integrity, workflow safety, asset smoke evidence, known warnings, and next
  maintenance choices.
- Opened the `v0.1.3rc2` maintenance development cycle after the public
  `v0.1.3-rc1` prerelease and attached release assets.
- Carried forward the local validation documentation commit with PySide6/Pillow
  evidence and the missing optional solver/science backend matrix.
- Kept `v0.1.3-rc1` as the current public prerelease tag; no `v0.1.3-rc2` tag
  was created by this development-cycle gate.

### Patch v0.1.3rc1 Release Candidate Tag Published

Release-candidate package version: `0.1.3rc1`

Release-candidate tag: `v0.1.3-rc1`

- OSW-RELEASE-003 aligns source package metadata to `0.1.3rc1` after
  OSW-RELEASE-002 preserved historical local tags through `v0.1.2` and repaired
  the default editable import path for this checkout.
- OSW-RELEASE-005 created the local annotated `v0.1.3-rc1` tag, OSW-RELEASE-008
  pushed only that tag to `origin`, and OSW-RELEASE-009 verified that the remote
  tag peels to `a6e8d3a8211e02359841d10e1947e16ab847b132`.
- The existing `v0.1.2` final tag remains historical source-release evidence at
  `c39f21372ef837f096aa0d430cced82adc6f3485` and must not be moved,
  recreated, retargeted, deleted, or reused as the current `develop` line.
- No branch push, all-tags push, force push, GitHub Release, package artifact,
  binary installer, or public announcement was created by the v0.1.3rc1
  tag-only gates.

## 0.1.2 - GitHub Source Release Published

### Patch v0.1.2 Source Release

Final package version: `0.1.2`

Published final tag: `v0.1.2`

- OSW-AUTO-072 prepared final `0.1.2` package metadata after the local
  `v0.1.2-rc1` candidate and OSW-AUTO-071 triage reported no P0/P1 blockers.
- OSW-AUTO-073 created the local annotated `v0.1.2` tag, and OSW-AUTO-077
  pushed only `refs/heads/develop:refs/heads/develop` and
  `refs/tags/v0.1.2:refs/tags/v0.1.2` to GitHub.
- Remote `develop` and `v0.1.2^{}` both resolve to
  `c39f21372ef837f096aa0d430cced82adc6f3485`; the remote annotated tag object
  verified by OSW-AUTO-077 is `353a87897c842ee01aaae18abc4d69f330406e09`.
- Local `v0.1.2-rc1` remains annotated evidence at
  `28b30c1f79d4c62d160629e96fc1fcefa2382ebe` and was not pushed by
  OSW-AUTO-077.
- The local `v0.1.1` final tag remains historical local-only evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197` and must not be published as
  current after the OSW-AUTO-067 GUI workflow fix.
- GUI workflow evidence remains based on OSW-AUTO-068 and OSW-AUTO-070: import
  creates visible project items, Project Tree and Properties update,
  Run/Generate uses `WorkbenchWorkflowSession`, and table/report state reflects
  imported project data and diagnostics.
- Known limitations remain P2/P3: optional external solver executables and
  live runs are environment-specific, manual desktop CUA depth is limited,
  Cantera 3.2 emits a deprecation warning, external URL freshness is outside the
  local docs checker, and packaging smoke is separate.
- Release artifacts, a GitHub Release page, binary installers, and public
  announcement text were not created by the source publish gate.

### Patch v0.1.2rc1 Release Candidate

- OSW-AUTO-070 prepares package metadata for `0.1.2rc1` and the local
  annotated `v0.1.2-rc1` release-candidate gate after OSW-AUTO-068 verified
  the GUI workflow fix with no P0/P1 blockers.
- The local `v0.1.1` final tag remains historical evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197` and must not be published as
  current after the post-tag GUI workflow fix.
- `v0.1.2-rc1` is local-only unless a later explicit maintainer push gate
  approves it. Final `0.1.2` / `v0.1.2`, release artifacts, public push, and
  announcement remain blocked.

### GUI Workflow Glue

- OSW-AUTO-067 improves the GUI-native Import -> Configure/Inspect ->
  Run/Generate -> Result/Table -> Report path after OSW-AUTO-066 classified the
  interactive GUI workflow as `PASS_WITH_LIMITATIONS`.
- GUI imports can now add visible project items for supported mesh, standard
  geometry, `.m`, and `.mat` preview paths; selection updates the properties
  panel and table/plot/mesh preview state where data is available.
- GUI Run/Generate routes through a workflow service that prepares bounded
  case/template outputs or records optional dependency diagnostics without
  direct GUI solver subprocess execution.
- GUI report export now includes current imported/project state, result tables,
  mesh metadata, figure placeholders, and diagnostics when available.
- The local annotated `v0.1.1` tag remains preserved release evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197`. After this post-release workflow
  fix merges, `develop` is ahead of `v0.1.1`; public publish remains blocked
  pending a new release/version decision.

## 0.1.1 - Final Metadata Prepared

Final package version: `0.1.1`

Planned final local tag: `v0.1.1`

Final v0.1.1 metadata is prepared after the patch RC1 recovery path passed local
QA and source-install validation. The final `v0.1.1` tag is not created by this
release-prep update; it remains pending a dedicated local tag gate. No public tag
push, release artifact build, external solver binary bundle, remote push gate, or
public announcement is created by this update.

### Release Evidence

- Historical local `v0.1.0` evidence remains preserved at
  `da8728adf679314442755ed781c1dd57d1c6ed27` and must not be published as the
  current release.
- Local annotated `v0.1.1-rc1` evidence remains preserved at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`; it was not pushed.
- OSW-AUTO-061A was a docs/readiness cleanup only. The maintainer accepted that
  docs-only post-RC delta for this final-prep path.
- OSW-AUTO-057 fixed the isolated source-run blockers found after the local
  `v0.1.0` tag was created, including Ruff UP042 enum issues and subprocess
  PATH stabilization for QA tests.
- OSW-AUTO-058 verified a fresh source-install retest with no P0/P1 blockers.
- OSW-AUTO-060 verified `0.1.1rc1` source-install validation with ruff,
  default/importlib pytest, fast QA, pre-merge QA, docs link checking, and
  duplicate basename checking.

### Known Limitations

- Optional external solver executables remain environment-specific and are not
  bundled by default.
- GUI live interaction depth remains environment-specific; source-install
  validation records dependency and offscreen/QA evidence, not a full manual GUI
  UAT.
- External URL freshness remains out of scope for the local-only docs checker.
- Public push remains blocked until an explicit maintainer gate.

## 0.1.1rc1 - Patch Release Candidate

Release candidate package version: `0.1.1rc1`

Local release-candidate tag: `v0.1.1-rc1`

This patch release candidate follows the source-install recovery path selected
in OSW-AUTO-059. The existing local annotated `v0.1.0` tag remains historical
local-only evidence at `da8728adf679314442755ed781c1dd57d1c6ed27` and must not
be published as the current release. `v0.1.1-rc1` is local-only unless a later
explicit maintainer push gate approves the exact tag.

No final `v0.1.1` tag, public tag push, release artifact build, external solver
binary bundle, remote push gate, or public announcement is created by this
release-candidate prep.

### Fixed Blocker Summary

- OSW-AUTO-057 fixed the isolated source-run blockers found after the local
  `v0.1.0` tag was created, including Ruff UP042 enum issues and subprocess
  PATH stabilization for QA tests.
- OSW-AUTO-058 verified a fresh source-install retest with ruff, default
  pytest, importlib pytest, fast QA, pre-merge QA, docs link checking, duplicate
  basename checking, and GUI offscreen launch passing with no P0/P1 blockers.
- OSW-AUTO-060 updates package metadata and release checks for the
  `0.1.1rc1` patch candidate without moving or publishing historical tags.

### Known Limitations

- Optional external solver executables remain environment-specific and are not
  bundled by default.
- GUI live interaction depth remains environment-specific even though offscreen
  launch smoke passed in source-install retest.
- External URL freshness remains out of scope for the local-only docs checker.
- Final `v0.1.1` remains blocked until a later final release gate.
- Public push remains blocked until an explicit maintainer gate.

## 0.1.0 - Final Metadata Prepared

Final package version: `0.1.0`

Planned final local tag: `v0.1.0`

Final v0.1.0 metadata is prepared after local RC3 UAT passed with no P0 or P1
blockers. The final `v0.1.0` tag is not created by this release-prep update; it
remains pending a dedicated local tag gate. No public tag push, release artifact
build, external solver binary bundle, remote push gate, or public announcement is
created by this update.

Local annotated `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` remain historical
local release evidence. RC3 points to
`dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`, the last release-candidate commit
before this final metadata-prep change.

### Highlights

- PySide6 desktop GUI shell architecture remains optional behind the `gui`
  extra, with CLI diagnostics when PySide6 is unavailable.
- Plugin/add-in architecture covers importers, solvers, scripts,
  post-processing, and reports without executing plugin code during manifest
  validation.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset define
  the core v0.1 data contracts.
- Standard/exported CAD and mesh import policy remains explicit; commercial
  native CAD direct import is out of scope.
- meshio, Gmsh, PyVista, and Matplotlib workflows are optional integration
  surfaces with missing-dependency diagnostics.
- CalculiX linear static demo coverage includes input deck generation, optional
  runner diagnostics, result parsing, golden fixtures, and validation helpers.
- OpenFOAM cavity and duct template demos remain bounded educational templates,
  not a full OpenFOAM UI.
- Cantera and CoolProp basic demos cover small chemistry/property workflows with
  explicit SI-unit data and optional dependency behavior.
- MATLAB/Octave `.m` and `.mat` workflows remain preview-first; importing a
  script does not auto-run code.
- FigureDataset, ResultDataset, and HTML report workflows include assumptions,
  warnings, validation notes, figures, result tables, and known limitations.
- Validation, golden tests, docs link checking, duplicate test basename
  prevention, scope checks, architecture checks, and solver artifact scans are
  part of the release QA harness.

### RC3 Local UAT Summary

- OSW-AUTO-052 local UAT passed with no P0 or P1 blockers.
- Automated QA passed: release metadata, docs link checker, duplicate basename
  checker, scope drift, architecture boundaries, solver artifact scan, fast QA,
  pre-merge QA, ruff, required pytest suites, and default `pytest -q`.
- Demo smoke results: CAD import and HTML report passed; mesh import, Gmsh,
  CalculiX, OpenFOAM, Cantera/CoolProp, and MATLAB/Octave workflows passed with
  optional dependency missing where local optional stacks were unavailable.
- PySide6 was missing in the local UAT environment, so GUI help and friendly
  missing-extra diagnostics passed, but live GUI interaction was skipped.
- Live external solver runs were not performed because local solver executables
  and optional stacks were missing; this is treated as environment-specific and
  non-blocking for the base v0.1 source workflow.

### Known Limitations

- Simulink, `.slx`, and `.mlapp` workflows are not supported.
- Native commercial CAD direct import is not supported; use standard/exported
  formats such as STEP, STL, OBJ, IGES, BREP, or mesh formats.
- OSW is not a MATLAB clone, full ANSYS clone, full OpenFOAM UI, industrial
  certified CAE product, or substitute for expert engineering judgment.
- External solver executables and heavy optional Python stacks are not bundled
  by default and remain local environment responsibilities.
- External URL freshness is intentionally out of scope for the local-only docs
  link checker.

## 0.1.0rc3 - Draft

Release candidate package version: `0.1.0rc3`

Planned local release-candidate tag: `v0.1.0-rc3`

RC3 is the current local release-candidate target for `develop` after the
post-RC2 hardening work in OSW-AUTO-047 and OSW-AUTO-048. Local annotated
`v0.1.0-rc1` remains historical evidence at
`29c5c8bec8df30c7f7be72fc9be5e5409794968e`; local annotated `v0.1.0-rc2`
remains historical evidence at
`684dc6138d4257564bbcdd176a9d5ed311a7316d` and is no longer current
`develop` after OSW-AUTO-047/048. Neither prior RC tag should be pushed as the
current RC.

No public tag push, final `v0.1.0` tag, release artifact build, external solver
binary bundle, remote push gate, or public announcement is created by this
release-notes update.

### Highlights

- Package and CLI version metadata move from `0.1.0rc2` to `0.1.0rc3`.
- Release metadata QA accepts prior local rc1 and rc2 evidence while validating
  an expected annotated rc3 tag after the local tag gate.
- Default `pytest -q` collection remains fixed by OSW-AUTO-047 through unique
  test basenames and duplicate-basename QA.
- Documentation link checking is implemented by OSW-AUTO-048 and remains
  local-only/no-network by default. External URL freshness is intentionally out
  of scope for that checker.

### Known Limitations

- OSW v0.1 remains educational and research oriented, with unchanged
  out-of-scope boundaries recorded in `docs/known_limitations.md`.
- Optional external solvers and tools are not bundled by default.
- Final `v0.1.0`, public tag push, release artifacts, and public announcement
  remain blocked until separate maintainer-controlled gates.

## 0.1.0rc2 - Draft

Release candidate package version: `0.1.0rc2`

Planned release-candidate tag: `v0.1.0-rc2`

RC2 supersedes the local-only rc1 tag as the current `develop` release
candidate. The existing local `v0.1.0-rc1` tag remains historical evidence for
OSW-AUTO-043 and must not be pushed as the current RC after OSW-AUTO-044A/045.

No public tag push, final `v0.1.0` tag, release artifact build, external solver
binary bundle, or public announcement is created by this release-notes update.

### Highlights

- Package and CLI version metadata move from `0.1.0rc1` to `0.1.0rc2`.
- Release metadata QA now supports strict pre-tag checks, prior local RC
  evidence, and current RC tag validation without mutating tags.
- RC2 keeps the v0.1 feature scope from rc1: PySide6 GUI shell,
  plugin/add-in architecture, ProjectSchema / UnitSystem / MaterialDB,
  standard CAD/Mesh import policy, meshio/Gmsh/PyVista surfaces, CalculiX
  linear static demo, OpenFOAM cavity/duct templates, Cantera/CoolProp demos,
  MATLAB/Octave preview-first workflow, FigureDataset / ResultDataset / report
  flow, validation/golden/QA harness.

### Known Limitations

- OSW v0.1 remains educational and research oriented, with unchanged
  out-of-scope boundaries recorded in `docs/known_limitations.md`.
- Optional external solvers and tools are not bundled by default.
- Default `pytest -q` duplicate basename collection behavior remains a P2
  follow-up if still present; split suites and importlib-mode collection remain
  release evidence.
- `tools/qa/check_docs_links.py` remains a P2 follow-up if still absent.

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
