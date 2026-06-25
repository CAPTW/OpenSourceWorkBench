# Optional solver GUI health panel design

## Status

Design-only.

This gate adds no runtime behavior:

- no GUI implementation
- no view-model implementation
- no CLI behavior change
- no solver execution
- no external solver command execution
- no active smoke validation
- no dependency installation
- no solver installation
- no plugin loading
- no issue mutation
- no release mutation

## Current baseline

- `v0.1.5-rc1` is a public prerelease.
- The optional solver manifest schema/model exists.
- The passive discovery service exists.
- The CLI doctor preview exists.
- Issues `#6` through `#11` are open and `skipped-missing` after
  OSW-VALID-005.
- External solvers are not bundled.

## Relationship to CLI doctor

The future GUI consumes the same manifest and passive discovery concepts as the
CLI doctor preview. It should align health states, diagnostics, redaction, and issue references with `optional-solver-list`, `optional-solver-doctor`, and
`optional-solver-explain`.

The GUI should not show different pass/fail semantics. Passive discovery can
show missing, partial, discovered, unknown, blocked, or unsupported setup
states, but it is not validation-pass evidence and cannot imply issue closure.

## Entry points

Future entry points may include:

- a future menu item
- a future validation dashboard link
- a future project settings link
- a future release/first-run guidance link

Each entry point opens the same health panel contract and starts from redacted
passive discovery evidence.

## Panel layout

The future panel should use a quiet operational layout:

- summary header
- stack filter/search
- per-stack cards
- details panel
- diagnostics panel
- guidance panel
- validation history panel
- safety/privacy footer

The summary header should aggregate counts by health state and make clear that
optional missing stacks are expected on many machines.

## Stack cards

Each stack card should show:

- stack id
- display name
- issue reference
- health state
- missing requirements count
- partial/discovered indicators
- support status
- non-bundled disclaimer

Cards should avoid alarming wording for missing optional stacks. A missing card
means the local machine is not prepared for that optional workflow, not that the
base application is broken.

## Details panel

The details panel should show manifest metadata and passive discovery evidence:

- capabilities
- executable requirements
- Python package requirements
- environment hints, redacted
- version/help probe declarations, not executed
- prepared-machine notes

Probe declarations remain explanatory. The GUI must not execute version, help,
or smoke-test commands from this panel.

## Diagnostics display

The diagnostics panel should render passive diagnostics with concise text:

- missing executable
- missing Python package
- partial stack
- unsupported platform
- manifest error
- path redaction notice
- passive-discovery-only notice

Diagnostics should be grouped by stack and severity. Blocking language is
reserved for future explicit validation gates, not ordinary missing optional
dependencies.

## Privacy and redaction

- Paths are redacted by default.
- Environment values are hidden.
- No telemetry is collected.
- Export requires explicit user action in future.
- Full path display requires explicit opt-in in future.

The default panel should be safe to screenshot for support without exposing
user home paths, environment values, credentials, or provider secrets.

## User actions

Initial future actions should remain passive and explicit:

- refresh passive discovery
- copy summary in future, no OS clipboard in this design
- open docs/internal guidance in future
- no install button in initial scope
- no run-smoke button in initial scope
- validation run links must go through explicit validation gates

The panel must not offer automatic solver installation, dependency
installation, or hidden command execution.

## Validation history

The panel may show the last OSW-VALID result if available:

- skipped-missing is not pass
- passed-installed still requires closure review before issue closure
- issue closure not available from panel

Validation history should separate passive setup evidence from installed-only
validation evidence and should keep issues `#6` through `#11` open unless a
separate closure-review gate changes them.

## Future view-model boundary

The future view-model should be pure and UI-agnostic:

- pure view-model consumes discovery report objects
- GUI widgets do not perform discovery directly
- discovery refresh is explicit
- no solver command execution from view-model

This keeps PySide6 UI code separated from passive discovery source and from any
future explicit validation runner.

## Plugin ecosystem

- Built-in stacks come first.
- Future plugin manifests can appear with trust labels.
- Untrusted manifests cannot execute code.
- Schema validation required.

Plugin-provided manifests should be displayed as declarative metadata until a
separate plugin-loading gate defines trust, loading, and validation behavior.

## Accessibility and clarity

- Text alternatives for health states.
- Plain-language missing/partial messages.
- No alarming wording for optional missing stacks.
- Clear next-step guidance.

The panel should help users understand which optional workflows need a prepared
environment without implying that optional tools are mandatory for base OSW
usage.

## Non-goals

- no implementation in this gate
- no GUI source
- no view-model source
- no CLI behavior change
- no solver execution
- no install workflow
- no plugin loading
- no issue mutation
- no release mutation

## Future implementation slices

- `OSW-EXP-061_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_VIEWMODEL` - completed as a
  pure UI-agnostic view-model in
  [Optional solver GUI health panel view-model](optional_solver_gui_health_panel_viewmodel.md).
- `OSW-EXP-062_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_IMPLEMENTATION` - completed
  as a PySide display-only component in
  [Optional solver GUI health panel implementation](optional_solver_gui_health_panel_implementation.md).
- `OSW-EXP-063_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_DESIGN` - completed as a
  design-only export workflow contract in
  [Optional solver GUI export summary design](optional_solver_gui_export_summary_design.md).
- `OSW-EXP-064_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_VIEWMODEL` - completed as a
  pure export payload layer in
  [Optional solver GUI export summary view-model](optional_solver_gui_export_summary_viewmodel.md).
- `OSW-EXP-065_OPTIONAL_SOLVER_GUI_EXPORT_SUMMARY_IMPLEMENTATION` - completed
  as redacted GUI export wiring in
  [Optional solver GUI export summary implementation](optional_solver_gui_export_summary_implementation.md).
- `OSW-EXP-066_OPTIONAL_SOLVER_GUI_DISCOVERY_REFRESH_DESIGN`
- `OSW-VALID` prepared-machine validation reuse

## View-model follow-up

The view-model follow-up implements frozen dataclass records and builders that
turn supplied manifests and passive discovery reports into GUI-ready summary,
card, details, diagnostics, guidance, validation-history, and action-state
data. It does not import PySide, import Qt, implement widgets, run discovery,
execute solvers, run external commands, import optional solver packages, install
dependencies, mutate issues, edit releases, claim validation success, claim
closure readiness, bundle solvers, or claim certification.

## GUI implementation follow-up

The GUI implementation follow-up adds the PySide display component over the
already-built view-model. It renders summary, stack cards, details,
diagnostics, guidance, validation history, safety, and action-state sections.
It does not implement discovery refresh, active smoke validation, solver
execution, external command execution, dependency installation, issue mutation,
release mutation, validation-pass claims, issue-closure claims,
bundled-solver claims, or certification claims.

## Export summary design follow-up

The export summary design follow-up defines how a future GUI action can prepare
and save a redacted optional-solver health summary. It keeps the workflow
design-only and covers payload fields, JSON/Markdown/plain-text formats,
privacy defaults, explicit path and overwrite policy, future action states,
failure handling, and implementation tests without adding exporter source, file
dialogs, clipboard integration, shell/browser actions, discovery execution,
solver execution, dependency installation, issue mutation, release mutation, or
validation-pass claims.

## Export summary view-model follow-up

The export summary view-model follow-up implements the pure payload/rendering
layer for that workflow. It consumes the already-built health panel view-model,
renders JSON, Markdown, and plain text in memory, and analyzes future save
paths without changing GUI source, implementing file dialogs, writing files,
using clipboards, opening shells or browsers, executing discovery, executing
solvers, installing dependencies, mutating issues, editing releases, or
claiming validation success.

## Export summary implementation follow-up

The export summary implementation follow-up wires the panel to the pure export
payload layer. It adds an explicit user-selected `.json`, `.md`, or `.txt`
redacted summary write path with missing-parent rejection and overwrite
confirmation. It still does not add clipboard access, shell/browser actions,
output-folder opening, discovery refresh, solver execution, dependency
installation, issue mutation, release mutation, validation-pass claims,
issue-closure claims, bundled-solver claims, or certification claims.
