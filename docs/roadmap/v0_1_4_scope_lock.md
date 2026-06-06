# v0.1.4 scope lock

Date: 2026-06-05

Repo HEAD reviewed: `1a5610c668dcd010e3852ecf84983de0e9786fd0`

## Base State

- Public release: `v0.1.3-rc1`
- Active development version: `0.1.3rc2.dev0`
- Release-trust cleanup completed.
- Onboarding tutorials completed.
- Post-public release checklist completed.
- Remaining issue triage after release trust completed.
- v0.1.4 feature-selection planning completed.

OpenSolver Workbench remains educational/research software. It is not a stable
production CAE platform, an industrial-certified solver product, a MATLAB,
Simulink, ANSYS, Abaqus, or commercial CAD clone, or a bundled-solver
distribution.

## Locked Theme

v0.1.4 starts with workflow and product polish.

The first slice should improve already released workflows, keep optional solver
dependencies guarded, and avoid feature expansion into solver execution,
marketplace distribution, signing, or certification claims.

## Locked First Implementation Slice

First implementation issue: #15 Improve Plugin Manager UX and install receipts.

Completed prompt: `OSW-FEAT-001_PLUGIN_MANAGER_UX_RECEIPTS`

Implementation status: `OSW-FEAT-001_PLUGIN_MANAGER_UX_RECEIPTS` has landed on
`develop`, and issue `#15` has been closed after the dedicated closure evidence
gate. The Plugin Manager now presents managed install receipts,
quarantine/rejection records, safety diagnostics, and managed-root uninstall
eligibility without adding remote plugin store, dependency auto-install, plugin
signing, marketplace behavior, or plugin code execution during install.

## Why #15 First

- Bounded scope compared with broader result/field workflow changes.
- Direct public-user value for local plugin installs.
- No optional solver or science backend requirement.
- Builds on existing local plugin install hardening.
- Improves trust, receipt, quarantine, rejection, and managed-root visibility.
- Can be verified with focused GUI, CLI, install-security, and docs tests.

## First Implementation Boundaries

### In Scope

- Plugin Manager UX polish.
- Install receipt visibility.
- Quarantine and rejection diagnostic summary.
- Local installed plugin list clarity.
- Managed-root and uninstall safety messaging.
- Documentation and tutorial updates for local plugin trust/receipt behavior.
- Focused tests for GUI presentation, CLI consistency, install hardening, and
  public docs.

### Out Of Scope

- Remote plugin store.
- Dependency auto-install.
- Plugin signing.
- Marketplace or catalog behavior.
- Executing plugin code during install.
- External solver execution from GUI.
- Network plugin install.
- Release asset changes.
- Version metadata bump.

## Acceptance Criteria For #15

- GUI shows installed plugin receipts clearly.
- GUI shows quarantine and rejection records clearly.
- GUI communicates managed-root and uninstall safety boundaries.
- CLI installed/quarantine commands remain consistent with GUI records.
- Local plugin install continues to avoid plugin code execution during install.
- No remote or network plugin install behavior is added.
- No dependency auto-install, plugin signing, marketplace, or catalog claim is
  introduced.
- Focused plugin install, plugin install security, Plugin Manager dialog, CLI,
  docs, Ruff, and QA guardrail checks pass.

## Second Implementation Candidate

Second candidate: #14 Enhance ResultViewer and FieldViewer workflow.

Status: `OSW-FEAT-003_RESULT_FIELD_VIEWER_WORKFLOW` has landed on `develop`.
The slice improves catalog summary, dataset details, plot/table/field/report
handoff hints, field artifact summaries, diagnostics, and optional
PyVista/fallback messaging without adding solver/script execution, full
FRD/OpenFOAM field parsing, vector glyphs, streamlines, animation, or mandatory
heavy visualization dependencies.

[ResultViewer / FieldViewer closure evidence](../maintenance/v0_1_4_result_field_viewer_closure.md)
records issue `#14` completion review and keeps the remaining v0.1.4 work
focused on explicit follow-up scope, especially issue `#17` VFEA experimental
scope definition.

[v0.1.4 remaining scope review](v0_1_4_remaining_scope_review.md) selects issue
`#17` as the next planning-only slice after issues `#15` and `#14` closed.

Reason: #14 has strong visible user value, but it is broader GUI/result workflow
work and follows #15 after the smaller product-polish slice established the
v0.1.4 implementation path.

## Experimental / Deferred

Deferred strategic item: #17 Define VFEA experimental plugin scope.

This remains planning-only unless a later scope gate explicitly approves it.
Any VFEA work must preserve human-in-the-loop validation, avoid automatic
certified FEA claims, and avoid default Abaqus or commercial solver
dependencies.

[VFEA experimental scope definition](vfea_experimental_scope.md) records the
issue `#17` planning-only boundary: FEASpec candidate and validator planning,
human review, benchmark requirements, CalculiX-first export planning, optional
and non-default Abaqus export planning only, no VLM API integration, no
automatic unreviewed solver execution, and no topology optimization
implementation.

## Environment-Blocked

The live optional validation issues remain open for suitable machines:

- #6 Gmsh validation
- #7 GNU Octave validation
- #8 CalculiX `ccx` validation
- #9 OpenFOAM validation
- #10 CoolProp and Cantera validation
- #11 PyVista and meshio validation

They are useful evidence, but they are not prerequisites for #15.

## Optional / Deferred

`OSW-MAINT-006B_FULL_SMOKE_WORKFLOW_DISPATCH` remains optional unless a
maintainer explicitly requests stronger live release-download evidence.

## Scope Guardrails

- No stable-production claim.
- No industrial certification claim.
- No MATLAB, ANSYS, Abaqus, or Simulink clone claim.
- No native commercial CAD direct import.
- No full OpenFOAM UI.
- No GUI direct solver subprocess execution.
- No mandatory optional solver/science dependencies for base import, CLI smoke,
  or unit tests.
- No release edit, release asset upload, tag creation, tag retargeting, or
  version metadata bump in this scope-lock gate.

## Issue #12 Closure Policy

Issue `#12` is eligible for closure after the dedicated planning closure gate
verifies that feature selection, scope lock, first implementation, and first
implementation closure evidence are all present on `develop`.

## Issue #15 Closure Policy

Issue `#15` is closed after the dedicated closure gate reviewed the Plugin
Manager receipt/quarantine UX evidence and maintainer acceptance status.

Closure evidence is recorded in
[v0.1.4 Plugin Manager UX closure evidence](../maintenance/v0_1_4_plugin_manager_ux_closure.md).
