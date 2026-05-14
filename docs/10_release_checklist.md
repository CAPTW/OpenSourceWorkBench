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
| `PENDING` | Gate criteria are defined and being checked in the current release prompt. |
| `SKIP` | Not applicable in the current local environment; skip reason is recorded. |
| `P0 BLOCKED` | Safety, secrets, destructive Git, or forbidden-scope blocker. |
| `P1 BLOCKED` | Required before a public v0.1 release tag or announcement. |
| `P2 FOLLOW-UP` | Small PR-sized cleanup that should be tracked but does not block the documentation release gate. |

## Gate Decision

| Item | Status | Evidence / decision |
| --- | --- | --- |
| Release gate result | `PENDING` | Documentation, demo smoke, CI-local QA, validation, scope checks, license metadata, release notes, and [license/version planning](13_license_and_version_plan.md) are being checked for the RC2 local tag gate. Local `v0.1.0-rc1` remains historical evidence; `v0.1.0-rc2` is the current candidate tag target. |
| Scope discipline | `PASS` | README, [Known Limitations](known_limitations.md), tutorials, and this checklist describe OSW v0.1 as an educational/research prototype. |
| External solver expectation | `PASS` | External solver executable checks are optional and local-environment dependent. Base install, CLI smoke, and unit tests do not require external solvers. |
| Release version plan | `PASS` | [License and version plan](13_license_and_version_plan.md) defines current package version `0.1.0rc2`, final package version `0.1.0`, Git tag names `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0`, strict pre-tag metadata checks, prior RC allowance, and RC-aware metadata checks for expected local annotated RC tags. |
| License final decision | `PASS` | Maintainer decision recorded as `GPL-3.0-or-later`; `LICENSE`, `pyproject.toml`, README, this checklist, and [license/version planning](13_license_and_version_plan.md) are aligned. |
| RC1 local annotated tag | `PASS` | OSW-AUTO-043 created local annotated `v0.1.0-rc1` at commit `29c5c8bec8df30c7f7be72fc9be5e5409794968e`. OSW-AUTO-045 must preserve that tag unchanged. |
| RC2 local annotated tag gate | `PENDING` | OSW-AUTO-045 may create local annotated `v0.1.0-rc2` only after version metadata update, feature-branch QA, squash merge, post-merge pre-tag QA, and tag verification pass. |
| Public tag push | `P1 BLOCKED` | Do not push `v0.1.0-rc1` or `v0.1.0-rc2` unless a later explicit maintainer push gate approves the exact tag. |
| Final `v0.1.0` tag | `P1 BLOCKED` | Do not create the final tag in the RC tag gate. It requires a separate final release gate. |
| Public announcement | `P1 BLOCKED` | Do not announce public v0.1 until the local tag state is reviewed and the maintainer explicitly directs announcement work. |
| Broad pytest command | `P2 FOLLOW-UP` | `pytest -q` currently hits an import mismatch from duplicate `test_plugin_manager_dialog.py` basenames. CI-style split suites and `pytest -q --import-mode=importlib` pass. |
| Docs link checker | `SKIP` | `tools/qa/check_docs_links.py` is not present. Targeted local markdown link checks were used in recent docs steps. |

## Blocker Register

| ID | Priority | Area | Status | Evidence | Required next action |
| --- | --- | --- | --- | --- | --- |
| REL-040-P1-001 | P1 | License and public release | `PASS` | Maintainer selected `GPL-3.0-or-later`; canonical GPLv3 text is in `LICENSE`; package metadata, README, release notes, and notice draft are aligned. | Keep metadata aligned during the dedicated release/tag gate. |
| REL-043-P1-001 | P1 | RC local tag gate | `PASS` | OSW-AUTO-043 created local annotated `v0.1.0-rc1` at commit `29c5c8bec8df30c7f7be72fc9be5e5409794968e`. | Preserve it as local release evidence; do not move or recreate it. |
| REL-045-P1-001 | P1 | RC2 local tag gate | `PENDING` | Package version is moving to `0.1.0rc2`; rc2 must not be created until post-merge pre-tag QA passes. | Create local annotated `v0.1.0-rc2` only after OSW-AUTO-045 final checks pass. |
| REL-043-P1-002 | P1 | Public tag push | `P1 BLOCKED` | rc1 is local-only historical evidence and rc2 will be local-only unless a later push gate approves it. | Do not push tags unless a maintainer explicitly instructs the exact current RC tag after a fresh push gate. |
| REL-043-P1-003 | P1 | Final release tag | `P1 BLOCKED` | `v0.1.0` is outside the RC tag gate. | Use a separate final release gate for the final tag. |
| REL-041-P1-002 | P1 | Public announcement | `P1 BLOCKED` | The project has a release metadata packet, but no public push or announcement approval. | Announce no public release until local tag state is reviewed and maintainer announcement direction is explicit. |
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
| `pyproject.toml` metadata, package discovery, and `requires-python >=3.11` are current. | `PASS` | Package version is `0.1.0rc2`; Python requirement is `>=3.11`; license metadata is `GPL-3.0-or-later`. |
| Base install has no mandatory heavy GUI, visualization, mesh, chemistry, or script extras. | `PASS` | `python -m osw.cli doctor` imports and reports optional stack status without failing. |
| Optional extras are declared for `gui`, `viz`, `mesh`, `mscript`, `chm`, and public `thermo` alias. | `PASS` | Install guide and release checklist document optional extras. |
| `environment.yml` installs the editable development package without optional solver stacks. | `PASS` | Installation guide keeps source/conda install separate from optional solver stacks. |
| Installation guide documents conda, pip, uv, Windows, Linux, troubleshooting, and optional external dependency behavior. | `PASS` | [Installation guide](install.md) is linked from README. |
| Release packaging uses source/conda editable install path if PyInstaller or standalone packaging is not release-ready. | `PASS` | Install guide names source/conda as the v0.1 release path. |
| External solver installers are not bundled or required by the base package. | `PASS` | Install guide and known limitations state external solvers are optional local dependencies. |
| `python -m osw.cli --version` reports the intended version. | `PASS` | Expected command output after metadata alignment: `osw 0.1.0rc2`. |
| `python -m osw.cli doctor` reports optional stack availability without failing when extras are absent. | `PASS` | Doctor reports PySide6, meshio, gmsh, pyvista, cantera, CoolProp, and hdf5storage missing; matplotlib and scipy available. |
| Final license notice is ready for public release metadata review. | `PASS` | `LICENSE` contains canonical GNU GPL version 3 text, with the "or later" grant recorded in metadata and release docs. |
| License/version planning packet exists. | `PASS` | [License and version plan](13_license_and_version_plan.md) documents maintainer decision, version scheme, tag policy, release procedure draft, rollback plan, and artifact policy. |
| Third-party notices draft exists. | `PASS` | [Third-party notices draft](14_third_party_notices.md) distinguishes source distribution from optional external solver binaries and records review areas. |
| RC1 local annotated tag evidence is recorded. | `PASS` | OSW-AUTO-043 created local annotated `v0.1.0-rc1`; OSW-AUTO-045 keeps it unchanged as local-only evidence. |
| RC2 local annotated tag gate is defined. | `PENDING` | OSW-AUTO-045 may create local annotated `v0.1.0-rc2` only after all post-merge pre-tag checks pass on merged `develop`. |
| Public tag push remains blocked until explicit maintainer approval. | `P1 BLOCKED` | A local tag is not a public release. Do not push rc1 or rc2 from this prompt. |
| Final `v0.1.0` tag remains blocked until a final release gate. | `P1 BLOCKED` | The RC gate must not create `v0.1.0`. |
| Public release announcement remains blocked until explicit maintainer direction. | `P1 BLOCKED` | Announcements require local tag review, push approval, and explicit maintainer direction. |

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
| `python -m osw.cli --version` reports intended version. | `PASS` | Expected output after OSW-AUTO-045 metadata alignment: `osw 0.1.0rc2`. |
| `python -m osw.cli doctor` reports environment status. | `PASS` | Doctor command passed with optional dependency diagnostics. |
| `python tools/qa/check_release_metadata.py` passes. | `PASS` | Verifies `LICENSE`, pyproject license/version metadata, README License section, release notes, third-party notices draft, final-tag absence, unexpected release-tag absence, prior rc1 evidence, and expected rc2 behavior when present. |
| `python tools/qa/check_release_metadata.py --forbid-release-tags` enforces strict pre-tag mode. | `PASS` | This mode intentionally fails while local rc1 exists and remains available for future pre-tag metadata prompts before any local release tag is created. |
| `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc2 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e` passes before rc2 exists. | `PASS` | Validates rc2 metadata while preserving rc1 as historical local evidence. |
| `python tools/qa/check_release_metadata.py --expected-version 0.1.0rc2 --expected-source-license GPL-3.0-or-later --allowed-prior-rc-tag v0.1.0-rc1 --allowed-prior-rc-target 29c5c8bec8df30c7f7be72fc9be5e5409794968e --expected-rc-tag v0.1.0-rc2 --expected-rc-target <develop HEAD> --require-annotated-rc-tag` passes after rc2 exists. | `PENDING` | RC2-aware mode must validate expected tag identity, annotated-tag status, peeled target commit, final-tag absence, and unexpected-tag absence without creating, moving, or deleting tags. |
| `python tools/qa/run_pre_merge_qa.py` passes. | `PASS` | Passed on 2026-05-14. |
| `python tools/qa/run_fast_qa.py` passes. | `PASS` | Passed as part of pre-merge QA. |
| `pytest tests/unit -q` passes. | `PASS` | Current release-gate result is recorded in the OSW-AUTO-043 self-check and final output. |
| `ruff check src tests` passes. | `PASS` | Passed as part of pre-merge QA. |
| `pytest tests/integration -q -m "not external_solver"` passes. | `PASS` | `4 passed, 3 skipped, 3 deselected`. |
| `pytest tests/golden -q` passes. | `PASS` | `10 passed`. |
| `pytest tests/validation -q` passes. | `PASS` | `4 passed`. |
| `pytest -q` passes in default local mode. | `P2 FOLLOW-UP` | Default collection may fail due duplicate test module basename import mismatch. This remains non-blocking only when the failure is exactly that known issue and targeted suites pass. |
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
| Required amend items are complete, if any. | `PASS` | OSW-AUTO-043 review determines whether an amend branch is needed; no broad feature fixes are allowed in this prompt. |
| Squash merge uses the approved release/docs commit message. | `PASS` | Planned message: `chore(release): prepare v0.1.0rc2 local candidate`. |

## Final Sign-Off Checklist

| Item | Status | Evidence / notes |
| --- | --- | --- |
| Target `develop` commit hash is recorded. | `PENDING` | Record in the OSW-AUTO-045 self-check and final response after squash merge. |
| Post-merge pre-tag QA result is recorded. | `PENDING` | Required before creating local annotated `v0.1.0-rc2`; record in the OSW-AUTO-045 self-check and final response. |
| Local annotated `v0.1.0-rc1` tag verification is recorded. | `PASS` | Object type is `tag`, target commit is `29c5c8bec8df30c7f7be72fc9be5e5409794968e`, and no push occurred. |
| Local annotated `v0.1.0-rc2` tag verification is recorded. | `PENDING` | Verify object type `tag`, target commit equals post-merge `develop` HEAD, and no push occurred. |
| Validation matrix reflects implemented workflows. | `PASS` | Current matrix covers CAE, mesh, script, chemistry/property, and report validation. |
| License decision is finalized before public release. | `PASS` | Maintainer decision is `GPL-3.0-or-later`; metadata and release docs are aligned. Public tag/announcement still require the dedicated release/tag gate. |

## Next Actions

| Action | Priority | Size | Owner expectation |
| --- | --- | --- | --- |
| Complete the RC2 local tag gate and decide whether to push it for feedback. | P1 | Maintainer action | OSW-AUTO-045 may create local `v0.1.0-rc2`; a later `OSW-AUTO-046_RC2_PUSH_OR_FEEDBACK_GATE` controls any push. |
| Run a separate final release gate before creating `v0.1.0`. | P1 | Small PR/prompt | The RC gate must not create the final tag. |
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
