# Optional solver GUI discovery refresh view-model

## Status

Experimental pure refresh view-model implemented.

This gate adds:

- refresh state dataclasses and enums
- request/result metadata records
- refresh action-state records
- success, failure, cancel, and stale-result apply helpers
- atomic health panel view-model replacement planning
- selected stack and filter preservation helpers
- status and error text helpers

This gate does not add:

- no GUI wiring
- no background worker
- no threading implementation
- no discovery execution
- no solver execution
- no external solver command execution
- no dependency installation
- no solver installation
- no issue mutation
- no release mutation

## Relationship to refresh design

This implementation follows
[Optional solver GUI discovery refresh design](optional_solver_gui_discovery_refresh_design.md).
It provides the pure state and apply layer for a later GUI refresh action. The
future GUI implementation will provide reports from an injected runner; this
layer only consumes supplied reports and existing view-models.

## Package path and public API

Package path:

- `src/osw/experimental/optional_solvers/gui_discovery_refresh_viewmodel.py`

Public API:

- `OptionalSolverRefreshState`
- `OptionalSolverRefreshAction`
- `OptionalSolverRefreshActionState`
- `OptionalSolverRefreshRequest`
- `OptionalSolverRefreshResult`
- `OptionalSolverRefreshStatusViewModel`
- `OptionalSolverRefreshPlan`
- `OptionalSolverRefreshApplyResult`
- `OptionalSolverRefreshDiagnostic`
- `build_optional_solver_refresh_plan`
- `build_optional_solver_refresh_status_viewmodel`
- `apply_optional_solver_refresh_success`
- `apply_optional_solver_refresh_failure`
- `apply_optional_solver_refresh_canceled`
- `ignore_optional_solver_stale_refresh_result`
- `explain_optional_solver_refresh`

## Refresh states

The view-model records:

- `idle`
- `pending`
- `running`
- `completed`
- `failed`
- `canceled`
- `stale_ignored`

These states are display data and orchestration inputs for a future GUI layer.
They do not start discovery or create workers.

## Action states

Action rows include:

- refresh passive discovery: available for future GUI wiring
- cancel refresh: future display-only state for pending/running requests
- run validation: unavailable
- install solver: unavailable
- close issue: unavailable

Action rows are not command handlers.

## Request/result model

`OptionalSolverRefreshRequest` records caller-owned request metadata:

- request id
- selected stack id
- filter text
- health-state filters
- requested timestamp
- source

`OptionalSolverRefreshResult` records caller-supplied result metadata:

- request id
- result state
- supplied passive discovery reports
- generated timestamp
- source
- status/error text
- diagnostics

Reports are supplied by future orchestration code. This module does not call
the passive discovery service.

## Success/failure/cancel/stale handling

Success builds a new `OptionalSolverHealthPanelViewModel` from supplied
manifests and supplied passive reports.

Failure preserves the previous health panel view-model and returns failed
status/error text.

Cancel preserves the previous health panel view-model and returns canceled
status text.

Stale results are ignored when the result request id does not match the active
request id. The previous health panel view-model remains visible.

## View-model swap behavior

The success helper returns a new health panel view-model. It does not mutate
cards or details in place.

The future GUI layer should swap the accepted view-model atomically only after
the apply result reports `applied=true`.

## Selection/filter preservation

The apply helpers preserve:

- selected stack id when the refreshed visible cards still contain it
- filter text
- health-state filters

If the selected stack is no longer visible after refresh, the underlying health
panel builder chooses the first visible stack or clears selection when no
cards are visible.

## Status and error display

Status text is generated for each refresh state. Error text is preserved for
failed results. Apply results include:

- active request id
- result request id
- selected stack id
- filter text
- health-state filters
- timestamp
- source
- diagnostics
- not-validation-evidence flag

## Safety boundary

- no discovery execution
- no solver execution
- no external solver command execution
- no subprocess
- no background worker
- no threading implementation
- no file write
- no clipboard, shell, or browser action
- no install action
- no issue closure action
- no dependency installation
- no issue mutation
- no release mutation
- no bundled solver claim
- no certification claim

## Relationship to export summary

Export after refresh uses the applied view-model returned by a successful
apply helper. Export before refresh, failed refresh, canceled refresh, or stale
refresh continues to use the current accepted view-model.

Exported summaries remain not validation evidence.

## Relationship to #6~#11

The refresh view-model can carry issue references for optional solver setup
state, but issues `#6` through `#11` remain open. `skipped-missing` remains not
pass evidence.

Skipped-missing remains not pass evidence.

## Future gates

- `OSW-EXP-068_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_IMPLEMENTATION`
- `OSW-VALID` prepared-machine validation reuse
