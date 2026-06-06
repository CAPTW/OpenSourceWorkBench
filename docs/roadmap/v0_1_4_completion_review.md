# v0.1.4 completion review

Date: 2026-06-06

Repo HEAD reviewed: `54d2261716546329c746dda5a08edc2089f79228`

Public release: `v0.1.3-rc1`

Active development version: `0.1.3rc2.dev0`

## Base State

OpenSolver Workbench remains educational/research software. It is not a stable
production CAE platform, an industrial-certified solver product, a MATLAB,
Simulink, ANSYS, Abaqus, or commercial CAD clone, or a bundled-solver
distribution.

This review does not release `v0.1.4`, does not bump version metadata, does not
create tags, does not edit the GitHub Release, and does not upload release
assets.

## Completed Scope

The planned v0.1.4 workflow/product-polish and experimental-scope line is
complete:

- Issue `#12`: v0.1.4 planning and scope lock completed and closed.
- Issue `#15`: Plugin Manager UX/install receipts implemented and closed.
- Issue `#14`: ResultViewer / FieldViewer workflow implemented and closed.
- Issue `#17`: VFEA experimental scope definition completed and closed.

The remaining open issues are live optional validation issues, not planned
v0.1.4 workflow/product-polish blockers.

## Evidence Table

| Issue | Final state | Commit evidence | Evidence docs | Tests/checks |
| --- | --- | --- | --- | --- |
| `#12` Plan v0.1.4 development cycle | closed | `1a5610c668dcd010e3852ecf84983de0e9786fd0`, `2e236e245c4066b8e655e0d048c0dcc761d205a6`, `996a05524a351925371b3102e8111d333d2ff2df` | [feature selection](v0_1_4_feature_selection.md), [scope lock](v0_1_4_scope_lock.md), [planning closure](../maintenance/v0_1_4_planning_issue_closure.md) | roadmap/docs checks, issue verification, release/tag guardrails |
| `#15` Plugin Manager UX/install receipts | closed | `25af8dbc165d92663b3c8ac24bd97629ce158fe2`, `0173d5eaa2a0d409780a451990b7e157a9a92418` | [Plugin Manager UX closure](../maintenance/v0_1_4_plugin_manager_ux_closure.md), [Plugin Install Hardening](../33_plugin_install_hardening.md) | plugin install, receipt/quarantine, Plugin Manager GUI, CLI, unit, GUI, Ruff, QA guardrails |
| `#14` ResultViewer / FieldViewer workflow | closed | `1fa84d938dc2280b57543d38a99778f756b3f973`, `28bc1fcc55e263c39b316d5a1516885fd5742004` | [ResultViewer / FieldViewer closure](../maintenance/v0_1_4_result_field_viewer_closure.md), [Result Dataset Walkthrough](../tutorials/result_dataset_walkthrough.md) | result/field view-model tests, viewer GUI tests, CLI surface, unit, GUI, Ruff, QA guardrails |
| `#17` VFEA experimental plugin scope | closed | `3494a6b04478121c83c51ed6998eae5307ed632d`, `54d2261716546329c746dda5a08edc2089f79228` | [VFEA experimental scope](vfea_experimental_scope.md), [VFEA scope closure](../maintenance/v0_1_4_vfea_scope_closure.md) | VFEA docs tests, scope drift, docs links, unit, GUI, Ruff, QA guardrails |

## Remaining Open Issues

| Issue | Title | Milestone | Environment requirement | Why it is not blocking planned scope |
| --- | --- | --- | --- | --- |
| `#6` | Run live Gmsh validation | `live-optional-validation` | local Gmsh executable and suitable fixtures | Useful live evidence, but base tests and planned v0.1.4 work remain solver-free. |
| `#7` | Run live GNU Octave validation | `live-optional-validation` | local GNU Octave executable | Environment-specific `.m` validation; preview-first script safety remains documented and tested without live Octave. |
| `#8` | Run live CalculiX ccx validation | `live-optional-validation` | local `ccx` executable | Live solver evidence is separate; default CalculiX tests use fixtures and fake runners. |
| `#9` | Run live OpenFOAM validation | `live-optional-validation` | configured OpenFOAM environment | OpenFOAM remains template/fixture-backed unless a dedicated validation machine is available. |
| `#10` | Run live CoolProp and Cantera validation | `live-optional-validation` | optional CoolProp and Cantera Python packages | Optional science packages can be validated later without blocking workflow/product polish completion. |
| `#11` | Run live PyVista and meshio validation | `live-optional-validation` | optional PyVista/meshio packages and display/off-screen setup | Optional visualization/mesh evidence remains separate from base import, CLI smoke, and unit tests. |

## Completion Decision

v0.1.4 planned scope complete: yes.

Rationale:

- The planning issue, two selected workflow/product-polish implementation
  issues, and VFEA experimental scope issue are closed.
- Evidence docs and tests exist for the completed slices.
- The remaining open issues are explicitly live optional validation work that
  requires external tools or optional packages.
- No blocker remains in the planned v0.1.4 workflow/product-polish and VFEA
  scope-definition line.

This decision does not mean `v0.1.4` is released, does not create a release
candidate, and does not imply a VFEA implementation is present.

## Recommended Next Paths

### Path A: FEASpec IR Design

Use `OSW-EXP-002_FEASPEC_IR_DESIGN` if maintainers want to continue the
experimental VFEA line. That should remain a separate design gate and should not
add VLM APIs, credentials, automatic solver execution, mandatory Abaqus, or
topology optimization.

### Path B: Live Optional Validation

Use a dedicated `OSW-VALID` gate when a suitable machine has the required
solver executables or optional Python packages for issues `#6` through `#11`.
These gates should record installed/missing/pass/fail evidence and must not make
optional dependencies mandatory.

### Path C: Release Planning / Revalidation

Use a release metadata/revalidation prep gate if maintainers want an
`0.1.3rc2` or later prerelease candidate. That gate must separately decide
version metadata, tag creation, release assets, and public release edits.

## Non-Goals

- No version bump in this gate.
- No release tag in this gate.
- No GitHub Release edit.
- No release asset build, upload, or overwrite.
- No FEASpec or VFEA implementation.
- No VLM provider implementation.
- No credentials, API keys, or provider configuration files.
- No live solver validation.
- No closing live validation issues.

## Known Limitations

- `v0.1.3-rc1` remains a public prerelease.
- The Windows portable ZIP remains unsigned.
- No MSI, MSIX, or code signing is present.
- External solvers are optional and not bundled.
- VFEA remains unimplemented and planning-only.
- FEASpec remains a planned IR, not a shipped schema.
- Live optional validation remains environment-dependent.
- Public docs on `develop` may be newer than the tagged source.

## Next Prompt Recommendation

Choose one:

- `OSW-EXP-002_FEASPEC_IR_DESIGN` for the next experimental design gate; or
- an `OSW-VALID` live optional validation gate when the environment is
  available; or
- a release planning/revalidation gate if maintainers want to prepare the next
  prerelease boundary.

[v0.1.3rc2 vs v0.1.4-rc1 release boundary decision](../release/v0_1_3rc2_or_v0_1_4_decision.md)
recommends `v0.1.4-rc1` as the cleaner next prerelease boundary if maintainers
choose release prep, because the completed user-visible workflow work and VFEA
scope definition were planned and closed under the v0.1.4 line. A later
metadata-alignment gate is still required because the active version remains
`0.1.3rc2.dev0`.

Follow-up release prep: [v0.1.4-rc1 candidate metadata alignment](../release/v0_1_4_rc1_candidate.md)
aligns package and CLI metadata to `0.1.4rc1` for the next candidate. It does
not create a tag, build or upload assets, or edit the GitHub Release.

## Post-Review Release And Validation Follow-Up

`v0.1.4-rc1` has since been published as a public prerelease with tag target
`f1683b441ab308fd65318ef6de3f1282549946a1` and version `0.1.4rc1`.

[Live optional validation matrix for v0.1.4-rc1](../validation/live_optional_validation_matrix_v0_1_4rc1.md)
records the installed-only `OSW-VALID-002` audit for issues `#6` through `#11`.
All six live optional targets were classified as `skipped-missing` on this
machine because the relevant tools or packages were absent. The completion
decision is unchanged: the planned v0.1.4 scope is complete, while live optional
validation remains environment-dependent and issues `#6` through `#11` remain
open.

[Prepared environment plan for live optional validation](../validation/live_optional_validation_environment_plan.md)
records the required packages/executables, future smoke commands, pass criteria,
and separate closure-gate rule for those open issues.
