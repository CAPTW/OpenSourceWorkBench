# v0.1.3rc2 open issue triage

Date: 2026-06-05

Repo HEAD reviewed: `3026d4e6e3791996e977485c1a45fb9d60003142`

Public release: `v0.1.3-rc1`

Active development version: `0.1.3rc2.dev0`

This triage reviews the remaining open GitHub issues after the v0.1.3rc2
release-operation cleanup. It does not close issues, edit the GitHub Release,
upload release assets, create tags, retarget tags, or change product behavior.

## Recently Closed Issues

- #1 Clean remaining local duplicate-file hygiene records
- #2 Automate release asset download smoke
- #3 Add post-public release checklist
- #4 Review Windows portable ZIP user experience
- #5 Prepare v0.1.3rc2 maintenance revalidation gate

Milestone `v0.1.3rc2` has no open issues after these closures. Remaining open
issues are split between `live-optional-validation` evidence work and the
`v0.1.4` planning/feature line.

## Open Issue Table

| Issue | Title | Milestone | Labels | Category | Recommendation | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| #6 | Run live Gmsh validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation`, `blocked-by-environment` | Defer until a machine with Gmsh is available. | `gmsh` is not installed in this environment; issue explicitly says to run only when installed and keep artifacts ignored. |
| #7 | Run live GNU Octave validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation`, `blocked-by-environment` | Defer until a machine with GNU Octave is available. | `octave` is not installed in this environment; `.m` workflows must remain preview-first and safe-fixture only. |
| #8 | Run live CalculiX ccx validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation`, `blocked-by-environment` | Defer until a machine with `ccx` is available. | `ccx` is not installed in this environment; no live solver certification claim should be made. |
| #9 | Run live OpenFOAM validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation`, `blocked-by-environment` | Defer until a machine with OpenFOAM is available. | `simpleFoam` is not installed in this environment; fixture parser checks remain the safe fallback. |
| #10 | Run live CoolProp and Cantera validation | `live-optional-validation` | `validation`, `optional-dependency` | `live-optional-validation`, `blocked-by-environment` | Defer until the optional packages are installed. | `CoolProp` and `cantera` are not importable in the repo venv; missing diagnostics remain acceptable. |
| #11 | Run live PyVista and meshio validation | `live-optional-validation` | `validation`, `optional-dependency` | `live-optional-validation`, `blocked-by-environment` | Defer until visualization/mesh optional packages are installed. | `pyvista` and `meshio` are not importable in the repo venv; base tests must not require them. |
| #12 | Plan v0.1.4 development cycle | `v0.1.4` | `roadmap` | `v0.1.4-planning` | Keep open; use after the next public usability or release-trust slice. | Planning is needed before broad features, but #13 is a smaller immediate improvement and does not require unavailable optional solvers. |
| #13 | Improve onboarding examples and tutorials | `v0.1.4` | `docs`, `help-wanted`, `examples` | `docs-examples`, `maintenance-small` | Primary next issue. | Best next practical slice: improves public repository usability, uses existing safe fixtures, does not require optional solver executables, and supports new users after the public prerelease. |
| #14 | Enhance ResultViewer and FieldViewer workflow | `v0.1.4` | `gui`, `solver` | `v0.1.4-feature`, `plugin/GUI/solver work` | Defer until v0.1.4 feature selection. | Valuable product work, but it changes user-facing GUI/workflow behavior and should follow a feature planning gate with focused tests. |
| #15 | Improve Plugin Manager UX and install receipts | `v0.1.4` | `plugin`, `gui` | `v0.1.4-feature`, `plugin/GUI/solver work` | Keep as a product-UX candidate after #13 or planning. | Useful UX work with existing tests, but it is product behavior rather than release cleanup. |
| #16 | Evaluate code signing and installer strategy | `v0.1.4` | `roadmap`, `packaging` | `packaging-release`, `maintenance-medium` | Fallback issue if release trust is preferred over docs/examples. | Planning-only packaging work can preserve unsigned/no MSI/no code-signing honesty without uploading assets or mutating the release. |
| #17 | Define VFEA experimental plugin scope | `v0.1.4` | `roadmap`, `validation` | `v0.1.4-planning`, `should-defer` | Defer until v0.1.4 planning approves scope. | Experimental scope should not precede v0.1.4 feature selection and must retain human-in-the-loop and no-certification guardrails. |

## Environment-Dependent Issues

The following issues require optional tools or packages that are not available
in this checkout:

- #6 requires Gmsh (`gmsh` executable).
- #7 requires GNU Octave (`octave` executable).
- #8 requires CalculiX (`ccx` executable).
- #9 requires OpenFOAM (`simpleFoam` or equivalent executable).
- #10 requires optional Python packages `CoolProp` and `cantera`.
- #11 requires optional Python packages `pyvista` and `meshio`.

These issues should remain open and environment-blocked until a maintainer runs
them on a suitable machine. Evidence should be written under ignored
`artifacts/validation/` paths and should not be committed unless curated as
small docs-only summaries.

## Recommended Next Action

Primary issue: #13 Improve onboarding examples and tutorials.

Reason: #13 is the smallest high-value public usability slice. It can improve
the public repository without optional solver executables, release mutation, or
tag changes. It should use existing safe fixtures, expected CLI output, GUI
screenshots already committed where useful, and explicit optional dependency
diagnostics.

Fallback issue: #16 Evaluate code signing and installer strategy.

Reason: #16 is a planning-only release trust slice. It is appropriate if the
maintainer wants to focus on packaging trust before tutorials, but it must not
claim code signing, MSI support, SmartScreen safety, or asset replacement until
those are actually implemented and verified by a later explicit gate.

Deferred option: optional full-smoke workflow dispatch and live optional
validation issues #6 through #11.

Reason: release asset smoke already has offline CI and prior manual
`workflow_dispatch` evidence. A stronger full-smoke run is useful only if
maintainers explicitly want additional asset evidence now. Live optional
validation should wait for machines with the relevant dependencies installed.

## Non-Goals And Scope Guardrails

- No stable-production claim.
- No industrial certification claim.
- No MATLAB, ANSYS, or Simulink clone claim.
- No native commercial CAD direct import claim.
- No broad v0.1.4 implementation work before explicit planning or issue scope.
- No mandatory optional solver/science dependencies for base import, CLI smoke,
  or unit tests.
- No GitHub Release edit, release asset upload, tag creation, tag retargeting,
  tag push, all-tags push, force push, or issue closure in this triage.

## Notes

- `v0.1.3-rc1` remains a public prerelease.
- The Windows portable ZIP remains unsigned.
- No MSI installer is provided.
- No code signing is claimed.
- External solvers are not bundled.
- Public docs on `develop` are newer than the tagged source.
- `OSW-MAINT-006B_FULL_SMOKE_WORKFLOW_DISPATCH` remains optional rather than a
  blocker for selecting the next issue.
