# v0.1.3rc2 remaining issue triage after release trust closure

Date: 2026-06-05

Repo HEAD reviewed: `58ba02dd3b520d9f8ceed8b441340aefc25b22da`

Public release: `v0.1.3-rc1`

Active development version: `0.1.3rc2.dev0`

This triage reviews the remaining open GitHub issues after onboarding
tutorials, release asset smoke automation, portable ZIP UX review, workflow
evidence, and code signing / installer strategy were documented. It does not
close issues, edit the GitHub Release, upload assets, create tags, retarget
tags, or change product behavior.

## Recently Closed Issues

- #1 Clean remaining local duplicate-file hygiene records
- #2 Automate release asset download smoke
- #3 Add post-public release checklist
- #4 Review Windows portable ZIP user experience
- #5 Prepare v0.1.3rc2 maintenance revalidation gate
- #13 Improve onboarding examples and tutorials
- #16 Evaluate code signing and installer strategy

## Open Issue Table

| Issue | Title | Milestone | Labels | Category | Environment requirements | Recommendation | Reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #6 | Run live Gmsh validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation`, `blocked-by-environment` | `gmsh` executable; not found on this machine. | Defer until a machine with Gmsh is available. | Live validation is useful evidence, but it should not block v0.1.4 planning or make Gmsh mandatory for base tests. |
| #7 | Run live GNU Octave validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation`, `blocked-by-environment` | `octave` executable; not found on this machine. | Defer until a machine with GNU Octave is available. | `.m` workflows remain preview-first and should not require Octave in the base environment. |
| #8 | Run live CalculiX ccx validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation`, `blocked-by-environment` | `ccx` executable; not found on this machine. | Defer until a machine with CalculiX is available. | The fake timeout regression is stable, but live `ccx` evidence requires an installed solver. |
| #9 | Run live OpenFOAM validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation`, `blocked-by-environment` | OpenFOAM environment, such as `simpleFoam`; not found on this machine. | Defer until a configured OpenFOAM environment is available. | Fixture parser and template checks remain safe; live OpenFOAM should stay environment-specific. |
| #10 | Run live CoolProp and Cantera validation | `live-optional-validation` | `validation`, `optional-dependency` | `live-optional-validation`, `blocked-by-environment` | `CoolProp` and `cantera` Python packages; not importable in the repo venv. | Defer until the optional packages are installed. | Missing optional science backends are acceptable if diagnostics remain explicit. |
| #11 | Run live PyVista and meshio validation | `live-optional-validation` | `validation`, `optional-dependency` | `live-optional-validation`, `blocked-by-environment` | `pyvista` and `meshio` Python packages; not importable in the repo venv. | Defer until the optional packages are installed. | Heavy visualization and mesh packages should remain optional and guarded. |
| #12 | Plan v0.1.4 development cycle | `v0.1.4` | `roadmap` | `v0.1.4-planning` | Maintainer planning decision; no optional backend required. | Primary next action. | Release-trust and public-onboarding cleanup are complete, while remaining live validation is environment-blocked and feature issues need a planning frame. |
| #14 | Enhance ResultViewer and FieldViewer workflow | `v0.1.4` | `gui`, `solver` | `gui-result-feature` | GUI/product design and focused tests; optional heavy visualization should stay guarded. | Defer until #12 frames v0.1.4 scope. | Valuable user workflow work, but it is feature-scale and should follow planning. |
| #15 | Improve Plugin Manager UX and install receipts | `v0.1.4` | `plugin`, `gui` | `plugin-manager-feature` | GUI/plugin UX scope and focused tests; no external solver required. | Fallback if a concrete maintenance-sized UX slice is preferred. | It can improve trust and install clarity without optional solvers, but still changes product UX and needs clear scope. |
| #17 | Define VFEA experimental plugin scope | `v0.1.4` | `roadmap`, `validation` | `experimental-vfea`, `should-defer` | Maintainer scope decision and validation framing. | Defer until #12 decides whether this belongs in v0.1.4. | Experimental VFEA work should not outrun the v0.1.4 feature-selection gate or make solver accuracy claims. |

## Environment-Blocked Issues

The live optional validation issues remain open because this checkout does not
have the required optional tools or packages:

- #6 requires Gmsh (`gmsh`).
- #7 requires GNU Octave (`octave`).
- #8 requires CalculiX (`ccx`).
- #9 requires OpenFOAM (`simpleFoam` or equivalent configured environment).
- #10 requires `CoolProp` and `cantera`.
- #11 requires `pyvista` and `meshio`.

These should be run only on suitable maintainer machines. Evidence should stay
under ignored runtime artifact paths unless later summarized in a small reviewed
documentation note.

## v0.1.4 Planning Section

Issue #12 is the recommended next gate. It should select the first v0.1.4 slice
and decide how to sequence:

- #14 ResultViewer / FieldViewer workflow improvements
- #15 Plugin Manager UX and install receipts
- #17 VFEA experimental plugin scope
- any future packaging prototype, such as unsigned MSI or MSIX feasibility

Issue #15 is the best fallback if the maintainer wants a concrete UX-oriented
slice before broader planning. Issue #14 and #17 should wait for explicit
feature planning because they can expand scope quickly.

## Recommended Next Action

Primary: #12 Plan v0.1.4 development cycle.

Reason: completed v0.1.3rc2 release-trust cleanup leaves mostly
environment-blocked live validation issues and feature-scale v0.1.4 candidates.
Planning is now the lowest-risk way to choose the next development slice without
overcommitting to GUI, plugin, solver, or experimental VFEA work.

Fallback: #15 Improve Plugin Manager UX and install receipts.

Reason: if the maintainer wants an implementation slice instead of planning,
#15 has practical public-user value and does not require unavailable external
solvers. It still needs tight scope and focused GUI/plugin tests.

Deferred: #6 through #11 live optional validation, #14 ResultViewer /
FieldViewer workflow, #17 VFEA experimental plugin scope, and any full-smoke
workflow dispatch.

Reason: live validation is environment-specific, #14 and #17 are feature-scope
decisions, and the release asset smoke workflow already has offline CI plus
prior manual evidence.

## Full-Smoke Workflow Decision

`OSW-MAINT-006B_FULL_SMOKE_WORKFLOW_DISPATCH` should remain optional unless a
maintainer explicitly wants stronger live release-download evidence now. It is
not required before #12 because release asset smoke automation, offline CI, and
prior workflow evidence are already documented.

## Non-Goals And Scope Guardrails

- No stable-production claim.
- No industrial certification claim.
- No MATLAB, ANSYS, Abaqus, or Simulink clone claim.
- No native commercial CAD direct import claim.
- No mandatory optional solver/science dependencies for base import, CLI smoke,
  or unit tests.
- No GitHub Release edit, release asset upload, tag creation, tag retargeting,
  tag push, all-tags push, force push, or issue closure in this triage.

## Known Warnings

- `v0.1.3-rc1` remains a public prerelease.
- The Windows portable ZIP remains unsigned.
- No MSI installer exists.
- No MSIX installer exists.
- No code signing provider has been selected.
- External solvers are optional local dependencies and are not bundled.
- Optional dependency evidence is environment-specific.
- Public docs on `develop` are newer than the tagged `v0.1.3-rc1` source.

