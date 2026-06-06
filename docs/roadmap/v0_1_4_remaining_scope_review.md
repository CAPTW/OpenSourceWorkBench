# v0.1.4 remaining scope review

Date: 2026-06-06

Repo HEAD reviewed: `28bc1fcc55e263c39b316d5a1516885fd5742004`

## Base State

- Public release: `v0.1.3-rc1`
- Active development version: `0.1.3rc2.dev0`
- Public release state: prerelease, not draft
- Release tag target: `a6e8d3a8211e02359841d10e1947e16ab847b132`

OpenSolver Workbench remains educational/research software. It is not a stable
production CAE platform, an industrial-certified solver product, a MATLAB,
Simulink, ANSYS, Abaqus, or commercial CAD clone, or a bundled-solver
distribution. External solvers remain optional and user-installed.

## Completed v0.1.4 Planning And Product-Polish Items

- Issue `#12` Plan v0.1.4 development cycle: closed.
- Issue `#15` Improve Plugin Manager UX and install receipts: closed.
- Issue `#14` Enhance ResultViewer and FieldViewer workflow: closed.

The completed v0.1.4 theme is workflow and product polish. The implemented
slices improved local plugin trust/receipt UX and summary-first result/field
viewer workflows without adding solver execution, script execution, heavy
mandatory visualization dependencies, release asset changes, or version metadata
changes.

## Remaining Open Issues

| Issue | Title | Milestone | Labels | Category | Environment requirement | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| `#6` | Run live Gmsh validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | live optional validation | local Gmsh executable and suitable fixtures | Defer to a separate `OSW-VALID` gate on a machine with Gmsh installed. |
| `#7` | Run live GNU Octave validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | live optional validation | local GNU Octave executable | Defer to a separate `.m`/Octave validation gate; keep script workflows preview-first. |
| `#8` | Run live CalculiX ccx validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | live optional validation | local `ccx` executable | Defer to a separate CalculiX validation gate; fixture and fake-runner tests remain default. |
| `#9` | Run live OpenFOAM validation | `live-optional-validation` | `validation`, `optional-dependency`, `live-solver` | live optional validation | configured OpenFOAM environment | Defer to a separate validation gate; keep v0.1 coverage template and fixture backed. |
| `#10` | Run live CoolProp and Cantera validation | `live-optional-validation` | `validation`, `optional-dependency` | live optional validation | CoolProp and Cantera Python packages | Defer until those optional science packages are installed intentionally. |
| `#11` | Run live PyVista and meshio validation | `live-optional-validation` | `validation`, `optional-dependency` | live optional validation | PyVista and meshio Python packages, plus suitable display/off-screen setup | Defer until those optional visualization/mesh packages are available. |
| `#17` | Define VFEA experimental plugin scope | `v0.1.4` | `roadmap`, `validation` | experimental planning | maintainer review of scope and validation boundaries | Select as the next planning slice: `OSW-EXP-001_VFEA_SCOPE_DEFINITION`. |

## Live Optional Validation

Issues `#6` through `#11` are valuable release evidence, but they are
environment-dependent. They require local solver executables, optional science
packages, or visualization packages that must be installed deliberately by a
maintainer or validation machine owner.

They should remain open and be handled through separate validation gates. This
remaining-scope review does not run live optional validation, does not dispatch a
workflow, and does not make any optional solver or package mandatory.

Recommended future gates:

- `OSW-VALID-GMSH-*` for issue `#6`.
- `OSW-VALID-OCTAVE-*` for issue `#7`.
- `OSW-VALID-CALCULIX-CCX-*` for issue `#8`.
- `OSW-VALID-OPENFOAM-*` for issue `#9`.
- `OSW-VALID-CHM-LIVE-*` for issue `#10`.
- `OSW-VALID-VIZ-MESH-*` for issue `#11`.

## VFEA Experimental Scope

Issue `#17` is the remaining v0.1.4 planning item. It should be handled next as
scope definition only, before any implementation work. The goal is to define
what a future experimental Vision-to-FEA line may mean in OSW and what it must
not claim.

Reasons to select `#17` next:

- The two selected workflow/product-polish slices are complete and closed.
- Live optional validation remains environment-blocked.
- VFEA needs strict terminology, validation, and human-review boundaries before
  any code or plugin work.
- Scope definition can reduce future risk without adding dependencies,
  executables, release assets, or product behavior.

The next planning slice must require human-in-the-loop review. Image or VLM
output must be treated as untrusted draft input that a user reviews before any
solver preparation, export, or execution is considered.

## Recommended Next Action

Primary next action: `OSW-EXP-001_VFEA_SCOPE_DEFINITION` for issue `#17`.

The next prompt should define:

- VFEA scope document.
- FEASpec IR planning.
- Vision-to-FEA plugin architecture planning.
- Human-in-the-loop review flow planning.
- Synthetic benchmark plan.
- CalculiX-first export path planning.
- Abaqus export as optional and non-default planning only.
- Topology optimization as future/deferred planning only.

## Deferred Actions

- Live optional validation for issues `#6` through `#11`.
- `OSW-MAINT-006B_FULL_SMOKE_WORKFLOW_DISPATCH` unless a maintainer explicitly
  requests stronger live release-download evidence.
- `v0.1.3rc2` metadata, tag, or release prep.
- Any release asset rebuild, upload, overwrite, or GitHub Release edit.

## Non-Goals

- No VFEA implementation in this review.
- No FEASpec schema implementation in this review.
- No VLM provider implementation.
- No API keys or secrets.
- No automatic solver execution from image or VLM output.
- No mandatory Abaqus dependency.
- No Abaqus exporter implementation.
- No topology optimization implementation.
- No industrial certification or accuracy claim.
- No commercial CAD native import.
- No MATLAB, ANSYS, or Simulink clone claim.
- No `v0.1.4` release claim.

## Next Prompt Outline

`OSW-EXP-001_VFEA_SCOPE_DEFINITION` should:

- review issue `#17` and the v0.1.4 roadmap;
- create a planning-only VFEA scope document;
- define FEASpec IR goals and non-goals;
- define the human review checkpoints before any mutation or solver
  preparation;
- define a synthetic benchmark and validation evidence plan;
- keep CalculiX-first export as planning only;
- keep Abaqus optional, non-default, and planning only;
- defer topology optimization implementation;
- forbid automatic unreviewed solver execution;
- run docs, scope, architecture, and public-docs QA before any commit.
