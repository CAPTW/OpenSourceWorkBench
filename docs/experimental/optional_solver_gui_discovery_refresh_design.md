# Optional solver GUI discovery refresh design

## Status

Design-only.

This gate records:

- passive refresh workflow design
- future worker and view-model boundaries
- refresh status and failure states
- privacy and export interaction rules

This gate does not add:

- no refresh implementation
- no background worker implementation
- no solver execution
- no external solver command execution
- no dependency installation
- no solver installation
- no issue mutation
- no release mutation

## Current baseline

- `v0.1.5-rc1` is a public prerelease.
- Passive discovery service implemented.
- CLI doctor preview implemented.
- GUI health panel implemented.
- GUI export summary implemented.
- Issues `#6` through `#11` remain open and `skipped-missing`.
- External solvers are not bundled.

## Purpose

The future refresh workflow should allow users to explicitly refresh passive optional-solver discovery from the GUI.
It should keep GUI state aligned with CLI doctor semantics, avoid hidden solver
execution, and preserve privacy/redaction defaults.

The refresh action is a user-requested setup-state update. It is not a
validation gate and is not evidence that an optional solver workflow passed.

## Passive refresh boundary

Allowed future checks are passive resolver checks only:

- executable presence checks through the passive discovery service
- Python package presence checks without importing optional packages
- environment hint presence checks with values hidden by default
- manifest structural diagnostics

The future refresh workflow must keep these boundaries:

- no active smoke validation
- no solver command execution
- no external command execution
- no dependency install
- no solver install
- no issue mutation
- no release mutation
- no automatic refresh on startup in initial scope

## User flow

1. User opens the optional solver health panel.
2. Panel shows the current supplied view-model.
3. User presses Refresh Passive Discovery.
4. GUI shows progress and status.
5. Passive discovery service runs through a future injected runner.
6. New discovery reports build a new health panel view-model.
7. Widget swaps to the refreshed view-model.
8. User reviews changed cards, diagnostics, and guidance.
9. Export summary can then use the refreshed view-model.

## Worker and threading model

The future implementation should use a worker abstraction rather than calling
discovery directly from widgets. The widget should request refresh through an
injected runner or controller.

Required worker behavior:

- no direct discovery in widgets
- request id assigned to each refresh
- cancellation request supported by the worker contract
- stale result rejection when an older request completes after a newer one
- UI remains responsive while refresh is pending or running
- timeout applies only to worker orchestration, not solver commands
- errors are surfaced as diagnostics and status text

Because the passive service does not run solver commands, worker timeout is a
GUI orchestration guard rather than a solver-execution control.

## View-model update boundary

Refreshed discovery reports enter the existing pure health panel builder. The
widget should not mutate individual card rows in place.

Required update behavior:

- discovery reports enter a pure builder
- widget swaps view-model atomically
- no partial card mutation
- selected stack preserved by stack id when still visible
- filters preserved where safe
- stale refresh result ignored without altering the current view-model

## Status/error display

The future panel should expose deterministic status states:

- idle
- refresh pending
- refresh running
- refresh completed
- refresh failed
- refresh canceled
- stale result ignored

Status text should also expose the last refresh timestamp and source when a
refresh completes or fails. Errors should summarize the failed stack or worker
failure without exposing environment values.

## Privacy/redaction

Privacy behavior follows passive discovery and the health panel view-model:

- redacted paths by default
- environment values hidden
- full paths require explicit future opt-in
- export summary inherits redacted refreshed data
- no telemetry
- no credentials or secrets collected

If the refresh runner detects a privacy/redaction violation, the result should
be rejected and surfaced as a diagnostic.

## Interaction with export summary

- Export before refresh uses the current view-model.
- Export after refresh uses the new view-model.
- Export metadata should state source and timestamp.
- Exported summary is not validation evidence.
- Export must keep redaction defaults after refresh.
- Failed or canceled refresh leaves export bound to the current accepted
  view-model.

## Interaction with validation gates

Refresh results can inform prepared-machine validation prechecks by showing
which optional stacks appear missing, partial, or passively discovered.

Refresh results do not replace validation gates:

- skipped-missing remains not pass evidence
- active smoke validation remains separate
- issue closure remains unavailable from the panel
- prepared-machine validation evidence belongs in explicit OSW-VALID gates

## Failure handling

The future implementation should handle:

- discovery service exception
- malformed manifest
- path permission issue
- canceled refresh
- stale worker result
- privacy/redaction violation
- unexpected health state

Failure handling should keep the previous accepted view-model visible unless a
new complete view-model is built successfully.

## Test plan for future implementation

Future implementation tests should cover:

- injected runner success
- injected runner failure
- no startup refresh
- no solver execution
- selected stack preserved
- filters preserved where safe
- stale result ignored
- canceled refresh leaves current state unchanged
- export after refresh uses refreshed data
- privacy retained
- issue mutation absent
- release mutation absent

## Refresh view-model follow-up

[Optional solver GUI discovery refresh view-model](optional_solver_gui_discovery_refresh_viewmodel.md)
implements the pure state and apply layer for this design. It records refresh
states, request/result metadata, action states, stale-result handling,
success/failure/cancel apply helpers, atomic health panel view-model
replacement planning, selection/filter preservation, and status/error text. It
adds no GUI wiring, background worker, threading implementation, discovery
execution, solver execution, dependency installation, issue mutation, release
mutation, validation-pass claim, issue-closure claim, bundled-solver claim, or
certification claim.

## Non-goals

- no implementation in this gate
- no active smoke
- no install workflow
- no solver execution
- no external command execution
- no issue mutation
- no release mutation
- no plugin loading

## Future gates

- `OSW-EXP-067_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_VIEWMODEL` - completed as
  a pure refresh state/apply layer in
  [Optional solver GUI discovery refresh view-model](optional_solver_gui_discovery_refresh_viewmodel.md).
- `OSW-EXP-068_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_IMPLEMENTATION`
- `OSW-VALID` prepared-machine validation reuse
