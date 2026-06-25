# Optional solver plugin manifest GUI design

## Status

Design-only.

This gate defines the future optional solver plugin manifest GUI preview
workflow.

Status boundaries:

- no GUI implementation
- no view-model implementation
- no file dialog
- no plugin package loading
- no directory scan
- no network fetch
- no solver execution
- no dependency installation

## Current baseline

- `v0.1.5-rc1 public prerelease` is the current public release.
- Plugin manifest loader model exists.
- Plugin manifest CLI preview exists.
- Plugin manifest GUI view-model exists.
- Optional solver health/export/refresh GUI exists.
- `#6~#11 open/skipped-missing`.
- External solvers not bundled.

## Purpose

The future GUI should let users preview explicit plugin manifest files without
turning metadata into trusted runtime behavior.

The purpose is to:

- let users preview explicit plugin manifest files in a future GUI
- show accepted/rejected/conflict status
- show trust labels and source types
- keep plugin metadata separate from validation evidence
- avoid plugin code execution

## Entry points

Potential future entry points:

- future Optional Solver Health Panel action
- future Plugin Manifest Preview dialog
- future project settings entry

There is no automatic plugin manifest loading on startup in the initial scope.

## Explicit file preview flow

The future flow should be:

1. User chooses one or more JSON manifest files.
2. Loader parses data only.
3. GUI displays accepted/rejected/conflicts/diagnostics.
4. User reviews guidance and safety policy.
5. No accepted manifest is persisted or activated in initial scope.
6. No discovery refresh automatically runs from imported plugin manifests in
   initial scope.

The first implementation slice should remain a preview of loader reports, not
a persistence or activation workflow.

## Panel/dialog layout

The future panel or dialog should include:

- summary header
- source/trust overview
- accepted manifests table
- rejected manifests table
- conflict table
- diagnostics panel
- safety/policy panel
- future action footer

The layout should mirror the existing optional solver health panel by using
scannable tables, plain diagnostics, and disabled or unavailable future actions
instead of workflow buttons that imply install, validation, or issue closure.

## Accepted manifest display

Accepted manifest rows should show:

- stack id
- display name
- source type
- trust label
- related issue
- support status
- capabilities summary
- not validation evidence notice

Accepted means the manifest record passed loader policy for preview. It does
not mean the solver, package, plugin, or environment passed validation.

## Rejected manifest display

Rejected manifest rows should show:

- source path/ref
- trust label
- rejection reason
- diagnostics
- suggested fixes
- unsafe claim indicators

Rejected records should stay visible as review evidence and should not be
silently hidden. Unsafe claim indicators should cover installer wording,
executable code references, external-solver bundling claims, and certification
or production-readiness claims.

## Conflict display

Conflict rows should show:

- duplicate stack id
- built-in wins by default
- plugin override disabled by default
- explicit override policy future-only

The initial GUI must not offer an override action. Any override policy needs a
separate trust and activation gate.

## Trust/source labels

The GUI should display the same source and trust vocabulary as the loader and
CLI preview:

- built-in trusted
- reviewed project
- user provided
- third-party plugin
- organization managed
- untrusted
- invalid

Trust label is not certification. Third-party/plugin manifests are not trusted
by default.

## Safety/policy messaging

The safety panel should state:

- no plugin code execution
- no package import
- no directory scan
- no network fetch
- no solver execution
- no install workflow
- no issue mutation
- no release mutation

The GUI should not show install, run-smoke, execute, close-issue, open-market,
or fetch-network actions.

## Privacy

Privacy rules:

- display paths redacted by default
- source file names may be shown
- full paths require future explicit opt-in
- no environment dumping
- no telemetry

The GUI should not display environment variable values, raw PATH values,
credentials, provider secrets, or validation artifacts.

## Relationship to CLI preview

The GUI should use the same accepted/rejected/conflict semantics as
`optional-solver-plugin-manifest-preview`.

The GUI should use the same trust labels.

The JSON/text CLI remains source of automation truth. The GUI is review-focused
and should optimize for readable comparison, diagnostics, and safety warnings.

## Relationship to health panel

Initial GUI preview does not activate manifests.

Future activation would require a separate gate.

Discovery refresh remains built-in unless plugin manifests are explicitly
accepted in a future model.

Export summary may include plugin preview only after explicit future
integration.

## Relationship to validation

Plugin manifest preview is not validation evidence.

- skipped-missing remains not pass
- issue closure unavailable
- prepared-machine validation remains separate

Issues `#6` through `#11` remain open until a separate validation and closure
gate provides sufficient evidence.

## Future view-model boundary

The future view-model should be pure and should consume a loader report.

Rules:

- pure view-model consumes loader report
- GUI widgets do not parse JSON directly
- file dialog passes explicit paths to a future runner
- no solver/discovery side effects from view-model

The view-model should compute summary counts, table rows, selected-row details,
diagnostic rows, safety copy, action availability, and disabled reasons without
touching the filesystem or importing plugin packages.

## View-model implementation follow-up

`OSW-EXP-073_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_VIEWMODEL` implements the
pure view-model slice.

[Optional solver plugin manifest GUI view-model](optional_solver_plugin_manifest_gui_viewmodel.md)
implements the pure report-to-display layer for this design. It consumes
already-built loader reports and produces summary counts, accepted/rejected
rows, conflict rows, diagnostic rows, trust badges, guidance text, filters, and
disabled action states.

The view-model adds no GUI source, file dialog, plugin activation, plugin
package loading, directory scanning, network fetch, discovery execution, solver
execution, dependency installation, issue mutation, release mutation,
validation-pass claim, issue-closure claim, external-solver bundling claim, or
certification claim.

## GUI implementation follow-up

[Optional solver plugin manifest GUI implementation](optional_solver_plugin_manifest_gui_implementation.md)
implements the first PySide display component for the supplied GUI view-model.
It renders the preview records only: summary, accepted/rejected/conflict
tables, diagnostics, trust/source labels, safety policy, and disabled/future
action states.

The implementation remains separate from explicit import and activation. It
adds no file dialog, file loading, plugin activation, plugin package loading,
directory scanning, network fetching, discovery execution, solver execution,
dependency installation, issue mutation, release mutation, validation-pass
claim, issue-closure claim, bundled-solver claim, or certification claim.

## Failure handling

The future GUI should handle:

- invalid JSON
- unsupported schema
- unsafe claim
- duplicate stack id
- untrusted source
- path denied
- user cancel

Failures should preserve the current health panel state and present diagnostics
without running discovery, executing solvers, or mutating project/release/issue
state.

## Non-goals

- no implementation in this gate
- no plugin package loading
- no directory scanning
- no network marketplace
- no plugin activation
- no solver execution
- no issue mutation
- no release mutation

## Future gates

- `OSW-EXP-074_OPTIONAL_SOLVER_PLUGIN_MANIFEST_GUI_IMPLEMENTATION`
- `OSW-EXP-075_OPTIONAL_SOLVER_PLUGIN_MANIFEST_ACTIVATION_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
