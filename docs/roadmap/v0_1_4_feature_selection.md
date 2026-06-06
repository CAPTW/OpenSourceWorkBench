# v0.1.4 feature selection planning

Date: 2026-06-05

Repo HEAD reviewed: `f87f1120d7075765ae713b6fe976b9422d8dc8d2`

## Base State

- Public release: `v0.1.3-rc1`
- Active development version: `0.1.3rc2.dev0`
- Maintenance cleanup completed: release-operation cleanup, onboarding
  tutorials, release-trust strategy, issue closure triage, and remaining issue
  triage are documented.

OpenSolver Workbench remains educational/research software. It is not a stable
production CAE platform, an industrial-certified solver product, a MATLAB,
Simulink, ANSYS, Abaqus, or commercial CAD clone, or a bundled-solver
distribution.

## Closed Maintenance Items

- #1 Clean remaining local duplicate-file hygiene records
- #2 Automate release asset download smoke
- #3 Add post-public release checklist
- #4 Review Windows portable ZIP user experience
- #5 Prepare v0.1.3rc2 maintenance revalidation gate
- #13 Improve onboarding examples and tutorials
- #16 Evaluate code signing and installer strategy

## Remaining Open Issues

| Issue | Title | Labels | Milestone | Category | Effort | Risk | Dependency | Recommendation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| #6 | Run live Gmsh validation | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation` | live optional validation | medium | environment | `gmsh` executable, not available locally | Defer until a suitable validation machine is available. |
| #7 | Run live GNU Octave validation | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation` | live optional validation | medium | environment and script safety | `octave` executable, not available locally | Defer; keep `.m` workflows preview-first. |
| #8 | Run live CalculiX ccx validation | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation` | live optional validation | medium | environment | `ccx` executable, not available locally | Defer; fake timeout and fixture checks remain the default. |
| #9 | Run live OpenFOAM validation | `validation`, `optional-dependency`, `live-solver` | `live-optional-validation` | live optional validation | high | environment | OpenFOAM environment, not available locally | Defer; keep template/parser evidence fixture-backed. |
| #10 | Run live CoolProp and Cantera validation | `validation`, `optional-dependency` | `live-optional-validation` | live optional validation | medium | optional package | `CoolProp` and `cantera`, not importable locally | Defer until packages are installed. |
| #11 | Run live PyVista and meshio validation | `validation`, `optional-dependency` | `live-optional-validation` | live optional validation | medium | optional package and visualization | `pyvista` and `meshio`, not importable locally | Defer until packages are installed. |
| #12 | Plan v0.1.4 development cycle | `roadmap` | `v0.1.4` | planning | small | scope control | maintainer decision | Current gate; keep open until maintainer accepts the selected sequence. |
| #14 | Enhance ResultViewer and FieldViewer workflow | `gui`, `solver` | `v0.1.4` | GUI/result feature | medium-high | product behavior and optional visualization | PySide6 tests; heavy visualization stays optional | Second implementation candidate after scope lock. |
| #15 | Improve Plugin Manager UX and install receipts | `plugin`, `gui` | `v0.1.4` | plugin manager feature | medium | low-to-medium | PySide6 tests; no external solver required | First implementation candidate. |
| #17 | Define VFEA experimental plugin scope | `roadmap`, `validation` | `v0.1.4` | experimental planning | medium | scope and claims | maintainer decision, validation framing | Strategic planning item after scope lock. |

## v0.1.4 Theme Options

### Plugin Manager UX And Receipts

Improve local plugin install clarity, rejection messages, receipt/export
evidence, trust wording, and follow-up diagnostics for folder/ZIP installs.
This builds on released functionality, needs no live solver environment, and can
be tested with existing plugin-manager and install-security fixtures.

### ResultViewer / FieldViewer Workflow Polish

Improve ResultDataset and FieldDataset navigation, summary-first displays,
field metadata, missing optional dependency diagnostics, and report handoff.
This has high visible user value but touches more GUI/result workflow behavior
than Plugin Manager UX.

### VFEA Experimental Scope Definition

Define what an experimental VFEA plugin could and could not do. This should be
planning-only until the scope, validation story, human review points, and
non-certification wording are accepted. It must not imply automatic full FEA
generation, Abaqus dependency, or production accuracy.

### Optional Live Validation Track

Keep #6 through #11 open for suitable machines. These issues add useful
environment evidence but should not be the first v0.1.4 implementation slice.

### Packaging Prototype Track

Unsigned MSI/MSIX or artifact-attestation experiments can be considered later,
but packaging should remain separate from the first feature slice unless the
maintainer explicitly prioritizes distribution work.

## Selected Recommendation

Primary v0.1.4 planning outcome: move from release-trust cleanup into workflow
and product polish, while keeping optional solver validation and experimental
VFEA scope separate from implementation.

First implementation candidate: #15 Plugin Manager UX and install receipts.

Reason: #15 improves already released functionality, is valuable to public users
trying local plugins, has no live solver dependency, and can be kept to a
bounded set of docs, receipt, rejection-message, and test expectations.

Second implementation candidate: #14 ResultViewer / FieldViewer workflow.

Reason: #14 is more visible product value, but it touches result/field GUI
behavior and should follow a scope lock with explicit test and fixture choices.

Strategic / experimental candidate: #17 VFEA experimental plugin scope.

Reason: #17 can clarify future direction, but it should remain planning-only in
v0.1.4 until safety boundaries and validation expectations are written.

Deferred: #6 through #11 live optional validation and full-smoke workflow
dispatch remain optional and environment-specific.

Scope lock status: [v0.1.4 scope lock](v0_1_4_scope_lock.md) locks #15 as the
first implementation slice, with #14 as the second candidate and #17 deferred as
planning-only unless a later scope gate approves experimental work.

## Proposed Sequence

1. `OSW-PLAN-003_V0_1_4_SCOPE_LOCK`
   - Confirm whether #15 or #14 is the first implementation issue.
   - Confirm whether #17 is planning-only in v0.1.4.
   - Confirm #6 through #11 wait for a live validation machine.
2. `OSW-FEAT-001_PLUGIN_MANAGER_UX_RECEIPTS`
   - Execute if #15 is selected as the first implementation slice.
   - Expected impact: clearer local plugin install receipts, rejection messages,
     trust wording, and tests.
3. `OSW-FEAT-003_RESULT_FIELD_VIEWER_WORKFLOW`
   - Execute after #15 lands and the planning issue closure evidence is
     accepted.
   - Expected impact: clearer ResultDataset / FieldDataset browsing, metadata,
     and optional visualization diagnostics.
4. `OSW-EXP-001_VFEA_SCOPE_DEFINITION`
   - Execute if #17 is approved as planning-only scope definition.
   - Expected impact: documented experimental boundaries, validation needs, and
     non-goals before any implementation.

## Non-Goals

- No stable-production claim.
- No industrial certification claim.
- No MATLAB, ANSYS, Abaqus, or Simulink clone claim.
- No native commercial CAD direct import.
- No default Abaqus dependency.
- No full automatic VFEA execution without human review.
- No mandatory optional solver/science dependencies for base import, CLI smoke,
  or unit tests.
- No GitHub Release edit, release asset upload, tag creation, tag retargeting,
  or version metadata bump in this planning gate.

## Decision Needed From Maintainer

- Choose the first implementation issue: #15 or #14.
- Decide whether #17 is planning-only in v0.1.4.
- Decide whether #6 through #11 wait for a live validation machine.
- Decide whether packaging prototypes stay outside the first v0.1.4 feature
  slice.

## Exit Criteria For v0.1.4 Planning

- Selected feature line documented.
- Selected first implementation issue documented.
- Roadmap points to the selected sequence.
- Issue #12 receives the planning outcome comment.
- No release, tag, asset, or metadata mutation occurs.
