# Release Checklist

Release gate date: 2026-05-14

This checklist records v0.1 release readiness evidence for the educational and
research OpenSolver Workbench prototype. It confirms documentation coverage,
demo smoke status, QA evidence, optional dependency behavior, and known
limitations. It does not claim industrial certification, production CAE
validation, external solver availability, native commercial CAD direct import,
or full solver parity.

## Status Legend

| Status | Meaning |
| --- | --- |
| `PASS` | Evidence is present and aligned with v0.1 scope. |
| `SKIP` | Not applicable in the current local environment; skip reason is recorded. |
| `P0 BLOCKED` | Safety, secrets, destructive Git, or forbidden-scope blocker. |
| `P1 BLOCKED` | Required before a public v0.1 release tag or announcement. |
| `P2 FOLLOW-UP` | Small PR-sized cleanup that should be tracked but does not block the documentation release gate. |

## Gate Decision

| Item | Status | Evidence / decision |
| --- | --- | --- |
| Release gate result | `P1 BLOCKED` | Documentation, demo smoke, CI-local QA, validation, and scope checks are ready for review. Public v0.1 release/tag remains blocked until the final license decision is made. |
| Scope discipline | `PASS` | README, [Known Limitations](known_limitations.md), tutorials, and this checklist describe OSW v0.1 as an educational/research prototype. |
| External solver expectation | `PASS` | External solver executable checks are optional and local-environment dependent. Base install, CLI smoke, and unit tests do not require external solvers. |
| Release version plan | `P1 BLOCKED` | Current package version is `0.1.0a0`. No `v0.1*` tag is present. Create the release tag only after P1 blockers are resolved. |
| License plan | `P1 BLOCKED` | `pyproject.toml` and `LICENSE` still describe GPL-3.0-or-later as recommended/final decision pending. Final license decision is required before public release. |
| Broad pytest command | `P2 FOLLOW-UP` | `pytest -q` currently hits an import mismatch from duplicate `test_plugin_manager_dialog.py` basenames. CI-style split suites and `pytest -q --import-mode=importlib` pass. |
| Docs link checker | `SKIP` | `tools/qa/check_docs_links.py` is not present. Targeted local markdown link checks were used in recent docs steps. |

## Blocker Register

| ID | Priority | Area | Status | Evidence | Required next action |
| --- | --- | --- | --- | --- | --- |
| REL-040-P1-001 | P1 | License and public release | `P1 BLOCKED` | `LICENSE` is a placeholder and `pyproject.toml` says the final license is pending. | Decide and record the project license, update metadata/notices, and rerun release QA. |
| REL-040-P1-002 | P1 | Version/tag plan | `P1 BLOCKED` | Package version is `0.1.0a0`; no `v0.1*` Git tag exists locally. | After license approval, choose `v0.1.0a0`, `v0.1.0-rc1`, or final `v0.1.0` tag plan and document release notes. |
| REL-040-P2-001 | P2 | Broad pytest collection | `P2 FOLLOW-UP` | `pytest -q` fails during collection because `tests/gui/test_plugin_manager_dialog.py` and `tests/unit/test_plugin_manager_dialog.py` share a module basename. | Add pytest importlib configuration or rename one test module in a focused test-only PR. |
| REL-040-P2-002 | P2 | Docs link automation | `P2 FOLLOW-UP` | `tools/qa/check_docs_links.py` is absent and CI records it as a placeholder skip. | Add a lightweight docs link checker or keep the skip recorded until one exists. |
| REL-040-P2-003 | P2 | External executable smoke | `P2 FOLLOW-UP` | Local `doctor` reports core optional stacks missing; external solver smoke was not attempted. | Keep optional executable smoke as environment-specific evidence; do not make it mandatory for v0.1 base release. |

## Release Scope Confirmation

| Item | Status | Evidence / notes |
| --- | --- | --- |
| Release notes describe OSW v0.1 as an educational/research prototype. | `PASS` | README, north star, tutorials, known limitations, and install docs use educational/research prototype language. |
| README scope and non-goals are current. | `PASS` | README lists v0.1 scope, eight demos, non-goals, release checklist, demo smoke checklist, and known limitations. |
| `docs/known_limitations.md` is current and linked from README. | `PASS` | README non-goals section links Known Limitations. |
| Public docs avoid industrial certification and full commercial solver parity claims. | `PASS` | Scope drift check passed; docs state no certification or production accuracy claims. |
| Public docs avoid native commercial CAD direct import support claims. | `PASS` | README, known limitations, tutorials, and demo smoke checklist say standard/exported formats only. |
| `.m` workflows remain preview-first and execution is user-triggered. | `PASS` | README, tutorials, demo smoke checklist, and known limitations state `.m` import does not auto-run scripts. |
| No out-of-scope release requirement is introduced. | `PASS` | This gate does not require Simulink, `.mlapp`, native CAD direct import, full OpenFOAM UI, industrial certification, or GUI direct solver execution. |

## Demo Smoke Status

| Demo | Status | Evidence / notes |
| --- | --- | --- |
| 01 STEP import preview | `PASS` | [Demo smoke checklist](demo_smoke_checklist.md) and [tutorial](tutorials.md) cover standard/exported geometry preview and avoid proprietary direct-import claims. |
| 02 mesh import preview | `PASS` | Demo smoke and tutorial document mesh preview, optional `meshio`, `MeshInfo`, VTU conversion, and missing dependency diagnostics. |
| 03 Gmsh meshing template | `PASS` | Demo smoke and tutorial document primitive meshing, mesh size control, optional Gmsh/meshio, and scratch artifacts. |
| 04 CalculiX cantilever | `PASS` | Demo smoke and tutorial document linear static input deck generation, optional `ccx`, missing material/BC/load diagnostics, and validation limitations. |
| 05 OpenFOAM cavity/duct template | `PASS` | Demo smoke and tutorial document template generation, patch validation, optional OpenFOAM execution outside OSW, and no full OpenFOAM UI claim. |
| 06 Cantera reactor | `PASS` | Demo smoke and tutorial document bounded 0D reactor workflow, optional Cantera/mechanism diagnostics, species/time table, and plot placeholder. |
| 07 CoolProp property table | `PASS` | Demo smoke and tutorial document property point/sweep workflow, optional CoolProp diagnostics, CSV export, and no process simulator claim. |
| 08 MATLAB/Octave figure preview | `PASS` | Demo smoke and tutorial document preview-first `.m` import, user-triggered Octave execution, FigureDataset output, and Simulink/`.mlapp` exclusion. |

## Packaging Gate

| Item | Status | Evidence / notes |
| --- | --- | --- |
| `pyproject.toml` metadata, package discovery, and `requires-python >=3.11` are current. | `PASS` | Package version is `0.1.0a0`; Python requirement is `>=3.11`. |
| Base install has no mandatory heavy GUI, visualization, mesh, chemistry, or script extras. | `PASS` | `python -m osw.cli doctor` imports and reports optional stack status without failing. |
| Optional extras are declared for `gui`, `viz`, `mesh`, `mscript`, `chm`, and public `thermo` alias. | `PASS` | Install guide and release checklist document optional extras. |
| `environment.yml` installs the editable development package without optional solver stacks. | `PASS` | Installation guide keeps source/conda install separate from optional solver stacks. |
| Installation guide documents conda, pip, uv, Windows, Linux, troubleshooting, and optional external dependency behavior. | `PASS` | [Installation guide](install.md) is linked from README. |
| Release packaging uses source/conda editable install path if PyInstaller or standalone packaging is not release-ready. | `PASS` | Install guide names source/conda as the v0.1 release path. |
| External solver installers are not bundled or required by the base package. | `PASS` | Install guide and known limitations state external solvers are optional local dependencies. |
| `python -m osw.cli --version` reports the intended version. | `PASS` | Command output: `osw 0.1.0a0`. |
| `python -m osw.cli doctor` reports optional stack availability without failing when extras are absent. | `PASS` | Doctor reports PySide6, meshio, gmsh, pyvista, cantera, CoolProp, and hdf5storage missing; matplotlib and scipy available. |
| Final license notice is ready for public release. | `P1 BLOCKED` | License metadata remains a placeholder pending final project decision. |

## Documentation Checklist

| Item | Status | Evidence / notes |
| --- | --- | --- |
| Installation guide is linked from README and separates base install from optional extras and external solver tools. | `PASS` | README Quick Start links [Installation Guide](install.md). |
| Tutorial examples cover examples `01` through `08`. | `PASS` | [Tutorial examples](tutorials.md) links all eight example READMEs. |
| Demo smoke checklist covers examples `01` through `08`. | `PASS` | [Demo smoke checklist](demo_smoke_checklist.md) has a section for each demo. |
| Known limitations cover solver, validation, optional dependency, CAD, and script execution boundaries. | `PASS` | [Known Limitations](known_limitations.md) covers all requested boundaries. |
| Each tutorial has goal, prerequisites, steps, expected output, and troubleshooting. | `PASS` | Tutorials index and example READMEs were added in prior docs steps. |
| Documentation distinguishes tutorial smoke from optional local executable smoke. | `PASS` | Demo smoke checklist separates documentation smoke from optional local executable smoke. |
| Documentation avoids implying documentation-only examples are executable fixtures. | `PASS` | Demo smoke checklist permits documentation-only smoke and optional local executable smoke when dependencies exist. |
| Docs link checker command exists. | `SKIP` | `tools/qa/check_docs_links.py` is absent; local targeted markdown link checks have been used in docs steps. |

## QA Command Checklist

| Item | Status | Evidence / notes |
| --- | --- | --- |
| `.github/workflows/ci.yml` exists and runs local-safe lint, unit, integration smoke, golden, validation, scope, architecture, and solver artifact checks. | `PASS` | CI workflow exists and excludes external solver execution by default. |
| CI excludes optional external solver tests by default with `-m "not external_solver"`. | `PASS` | Workflow uses `pytest tests/integration -q -m "not external_solver"` and sets `OSW_EXTERNAL_SOLVER_TESTS=0`. |
| README documents local CI commands and optional external-solver opt-in command. | `PASS` | README Local CI Commands section documents both paths. |
| `python -m osw.cli --version` reports intended version. | `PASS` | `osw 0.1.0a0`. |
| `python -m osw.cli doctor` reports environment status. | `PASS` | Doctor command passed with optional dependency diagnostics. |
| `python tools/qa/run_pre_merge_qa.py` passes. | `PASS` | Passed on 2026-05-14. |
| `python tools/qa/run_fast_qa.py` passes. | `PASS` | Passed as part of pre-merge QA. |
| `pytest tests/unit -q` passes. | `PASS` | `216 passed, 3 skipped`. |
| `ruff check src tests` passes. | `PASS` | Passed as part of pre-merge QA. |
| `pytest tests/integration -q -m "not external_solver"` passes. | `PASS` | `4 passed, 3 skipped, 3 deselected`. |
| `pytest tests/golden -q` passes. | `PASS` | `10 passed`. |
| `pytest tests/validation -q` passes. | `PASS` | `4 passed`. |
| `pytest -q` passes in default local mode. | `P2 FOLLOW-UP` | Default collection fails due duplicate test module basename import mismatch. `pytest -q --import-mode=importlib` passes with `234 passed, 19 skipped`. |
| `python tools/qa/check_scope_drift.py` passes. | `PASS` | No OSW scope drift found. |
| `python tools/qa/check_architecture_boundaries.py` passes. | `PASS` | Architecture boundaries respected. |
| `python tools/qa/check_no_solver_artifacts_committed.py` passes. | `PASS` | No solver/runtime artifact paths detected. |
| `tools/qa/check_docs_links.py` is run if present; absent skip is recorded. | `SKIP` | Tool is not present. |
| Local markdown link/content check is run if a project command exists. | `SKIP` | No dedicated project command exists; prior docs steps used targeted local markdown checks. |
| Validation matrix reflects implemented workflows. | `PASS` | [Validation matrix](04_validation_matrix.md) maps at least five cases to demos and current QA evidence. |
| No solver runtime artifacts, secrets, or generated report dumps are staged. | `PASS` | Solver artifact scan passed; only docs/reports are expected for this gate. |

## Optional Dependency Checklist

| Item | Status | Evidence / notes |
| --- | --- | --- |
| `python -m osw.cli doctor` output records optional dependency status. | `PASS` | Doctor output records missing PySide6, meshio, gmsh, pyvista, cantera, CoolProp, and hdf5storage. |
| Missing PySide6, meshio, Gmsh, PyVista, Cantera, CoolProp, GNU Octave, or external solver executables are optional unless a smoke entry explicitly requires them. | `PASS` | README, install guide, tutorials, demo smoke checklist, and known limitations state optional behavior. |
| Optional local executable smoke records dependency version or missing diagnostic when available. | `PASS` | Demo smoke checklist requires status recording; release gate used doctor diagnostics. |
| Base CLI smoke and unit tests do not require heavy optional stacks. | `PASS` | CLI doctor and unit suite pass with most optional stacks missing locally. |

## Known Limitations Checklist

| Item | Status | Evidence / notes |
| --- | --- | --- |
| Release documentation links `docs/known_limitations.md`. | `PASS` | README and release checklist link known limitations. |
| Reports and demo evidence include known limitations or link to the known limitations page. | `PASS` | Demo smoke checklist points reviewers to known limitations. |
| External solver availability is not guaranteed. | `PASS` | README, install guide, known limitations, and demo smoke checklist state external solvers are optional. |
| Results without validation evidence remain marked as preview, template-based, fixture-backed, or educational. | `PASS` | Validation matrix and known limitations use this language. |

## Report Evidence Checklist

| Item | Status | Evidence / notes |
| --- | --- | --- |
| `.codex/reports/self_check/` contains this phase self-check report. | `PASS` | Required for this step before merge. |
| `.codex/reports/review/` contains this phase review report. | `PASS` | Required for this step before merge. |
| Reports record commands run, command results, skipped checks, remaining risks, and merge recommendation. | `PASS` | Required report templates include those sections. |
| Report evidence avoids secrets, generated solver runtime directories, binary outputs, and uncontrolled report exports. | `PASS` | This release gate writes text-only docs and reports. |

## Merge Readiness Checklist

| Item | Status | Evidence / notes |
| --- | --- | --- |
| Feature worktree is clean after checkpoint/review commits. | `PASS` | Required merge-gate condition; final status is recorded in the phase self-check and final response. |
| Target `develop` worktree is clean before merge. | `PASS` | Required merge-gate condition; final status is recorded in the phase self-check and final response. |
| Review score meets the threshold in `docs/06_review_protocol.md`. | `PASS` | Required before merge; score and decision are recorded in the phase review report. |
| Required amend items are complete, if any. | `PASS` | Review required fixes were limited to validation mapping and evidence-status wording; both are addressed in the amend pass. |
| Squash merge uses the approved release/docs commit message. | `PASS` | Planned message: `docs(release): assess v0.1 release readiness`. |

## Final Sign-Off Checklist

| Item | Status | Evidence / notes |
| --- | --- | --- |
| Target `develop` commit hash is recorded. | `SKIP` | Not available inside this pre-merge checklist document; record in the phase final response after squash merge. |
| Post-merge fast QA result is recorded. | `SKIP` | Not available inside this pre-merge checklist document; record in the phase final response after squash merge. |
| Post-merge scope drift, architecture boundary, and solver artifact checks are recorded. | `SKIP` | Not available inside this pre-merge checklist document; record in the phase final response after squash merge. |
| Validation matrix reflects implemented workflows. | `PASS` | Current matrix covers CAE, mesh, script, chemistry/property, and report validation. |
| License decision is finalized before public release. | `P1 BLOCKED` | Final public release/tag remains blocked until license metadata and notices are finalized. |

## Next Actions

| Action | Priority | Size | Owner expectation |
| --- | --- | --- | --- |
| Finalize project license and update `LICENSE`, `pyproject.toml`, README, and release notes. | P1 | Small PR | Maintainer decision plus docs metadata update. |
| Decide release version and tag plan after license update. | P1 | Small PR | Choose alpha/RC/final tag and record in release notes or changelog. |
| Fix broad `pytest -q` collection behavior by configuring importlib mode or renaming duplicate test module. | P2 | Small PR | Test-only change; CI split suites already pass. |
| Add a lightweight docs link checker or keep the CI placeholder skip explicit. | P2 | Small PR | Tools/docs QA improvement. |
| Record optional executable smoke on machines that intentionally install `ccx`, OpenFOAM, Gmsh, Cantera, CoolProp, or GNU Octave. | P2 | Small evidence PR | Environment-specific evidence; do not make base release depend on it. |

## Release Discipline

| Item | Status | Evidence / notes |
| --- | --- | --- |
| Public packages avoid industrial certification and full commercial solver parity claims. | `PASS` | Scope and docs checks passed. |
| Known limitations are included in release notes or linked from release documentation. | `PASS` | README and checklist link known limitations. |
| External solver installers are not bundled into the base package. | `PASS` | Install docs explicitly keep solver installs optional. |
| Generated reports and runtime case outputs are excluded unless curated examples or tests. | `PASS` | Solver artifact scan passed. |
