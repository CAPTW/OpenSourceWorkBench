# Next experimental line selection

## Status

`completed`

This planning-only gate selects the next experimental line after the
`v0.1.5-rc1` release flow, post-public audits, release-body cleanup,
maintenance hardening, and prepared-machine optional validation discovery.
It does not implement the selected line.

## Current baseline

- Current public release: `v0.1.5-rc1`
- Release state: public prerelease, not draft
- Release URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.5-rc1
- Release flow: closed
- Fresh post-public audit: passed
- Release body note: corrected
- Maintenance hardening: complete
- Live optional validation: `skipped-missing` in OSW-VALID-005 on this
  machine because the target optional solver and science stacks were absent.

## Open validation

- `#6` Gmsh validation remains open.
- `#7` GNU Octave validation remains open.
- `#8` CalculiX `ccx` validation remains open.
- `#9` OpenFOAM validation remains open.
- `#10` CoolProp / Cantera validation remains open.
- `#11` PyVista / meshio validation remains open.
- OSW-VALID-005 classified all `#6` through `#11` targets as
  `skipped-missing`.

## Candidate lines

- Prepared-machine validation retry planning
- FEASpec / VFEA workflow expansion
- ResultDataset parser extension planning
- ProjectSchema integration hardening
- Plugin ecosystem / optional solver manifest UX
- Maintenance / monitoring continuation
- Pause active experimental work

## Decision

Selected line: `Plugin ecosystem / optional solver manifest UX`

## Rationale

The release flow is closed, the fresh public asset audit passed, and release
body wording has been corrected. The latest prepared-machine validation pass
did not find any target optional solver or science stack, so another immediate
validation retry on the same environment would only repeat `skipped-missing`
evidence.

The selected line addresses the clearest product gap exposed by that evidence:
users and maintainers need better optional dependency discovery, plugin
manifest guidance, health status, and installation hint design. This work can
improve diagnostics and prepared-machine readiness while preserving the OSW
rule that external solvers remain optional, unbundled, and never installed by
default.

Skipped-missing live validation does not block this planning line because the
selected work is about manifest and health UX design, not claiming installed
solver capability. It also does not provide issue-closure evidence for issues
`#6` through `#11`.

## Non-actions

- No source implementation was performed.
- No release edit was performed.
- No issue mutation was performed.
- No solver execution was performed.
- No dependency install was performed.
- No version bump was performed.

## Next recommended gate

`OSW-EXP-055_OPTIONAL_SOLVER_MANIFEST_UX_DESIGN`

The next gate should remain design-scoped: define optional solver/plugin
manifest fields, health statuses, missing-dependency explanations, and UX
guardrails without installing dependencies, bundling solvers, executing
solvers, editing releases, or closing validation issues.

## Design follow-up

The follow-up
[optional solver manifest UX design](../experimental/optional_solver_manifest_ux_design.md)
defines the initial design-only contract for stack manifests, health states,
future CLI/GUI surfaces, plugin-provided manifest trust boundaries, validation
relationships, and safety/privacy limits. It keeps implementation split into
later gates for manifest schema models, discovery service design, CLI doctor
preview, and GUI health panel design.

The next follow-up
[optional solver manifest schema model](../experimental/optional_solver_manifest_schema_model.md)
implements only the typed declarative schema/model layer, JSON helpers,
structural diagnostics, and built-in manifest records. It still does not
implement discovery, CLI commands, GUI panels, health-check execution, solver
execution, dependency installation, issue mutation, or release mutation.

The discovery design follow-up
[optional solver discovery service design](../experimental/optional_solver_discovery_service_design.md)
defines how a future service can consume declarative manifests, separate
passive discovery from active validation, map health states, redact environment
details, hand off to CLI/GUI surfaces, and preserve plugin trust boundaries.
It remains design-only and does not implement discovery, execute external
commands, import optional solver packages, mutate issues, or claim validation
success.

The passive discovery implementation follow-up
[optional solver discovery service implementation](../experimental/optional_solver_discovery_service_implementation.md)
adds a source-level service for passive presence checks, injected resolvers,
redacted reports, health-state mapping, diagnostics, and built-in manifest
evaluation. It still does not add CLI commands, GUI panels, active smoke
validation, external command execution, solver execution, dependency
installation, issue mutation, or validation-pass claims.

The CLI preview follow-up
[optional solver CLI doctor preview](../experimental/optional_solver_cli_doctor_preview.md)
adds `optional-solver-list`, `optional-solver-doctor`, and
`optional-solver-explain` as passive text/JSON surfaces over the manifest and
discovery layers. It redacts paths by default, does not expose environment
values, treats missing optional stacks as setup evidence, and still does not
add GUI behavior, plugin loading, active smoke validation, solver execution,
dependency installation, issue mutation, release mutation, or issue-closure
claims.

The GUI health panel design follow-up
[optional solver GUI health panel design](../experimental/optional_solver_gui_health_panel_design.md)
defines the future GUI-facing health surface over the same manifest and
passive discovery concepts. It covers entry points, summary layout, stack
cards, details, diagnostics, guidance, validation history, privacy/redaction,
user actions, accessibility, plugin trust labels, and a pure view-model
boundary. It remains design-only and adds no GUI source, view-model source, CLI
behavior change, plugin loading, active smoke validation, external solver
command execution, solver execution, dependency installation, issue mutation,
release mutation, validation-pass claim, issue-closure claim, bundled-solver
claim, or certification claim.

The GUI health panel view-model follow-up
[optional solver GUI health panel view-model](../experimental/optional_solver_gui_health_panel_viewmodel.md)
implements only the pure UI-agnostic data layer for that future surface. It
builds deterministic summary, card, details, diagnostics, guidance,
validation-history, and action-state records from supplied manifests and
passive discovery reports. It adds no PySide import, Qt import, GUI widget,
CLI behavior change, discovery execution, active smoke validation, external
solver command execution, solver execution, dependency installation, issue
mutation, release mutation, validation-pass claim, issue-closure claim,
bundled-solver claim, or certification claim.

The GUI health panel implementation follow-up
[optional solver GUI health panel implementation](../experimental/optional_solver_gui_health_panel_implementation.md)
adds the PySide display component over that already-built view-model. It keeps
refresh, validation, install, close-issue, copy, and open-docs actions as
disabled/display-only placeholders and adds no GUI-initiated discovery, active
smoke validation, external solver command execution, solver execution,
dependency installation, issue mutation, release mutation, validation-pass
claim, issue-closure claim, bundled-solver claim, or certification claim.

The GUI export summary design follow-up
[optional solver GUI export summary design](../experimental/optional_solver_gui_export_summary_design.md)
defines a future redacted export workflow for the health panel. It remains
design-only and covers payload scope, JSON/Markdown/plain-text formats,
privacy defaults, explicit save-path and overwrite policy, action-state
behavior, payload-builder boundaries, failure handling, and future tests
without adding exporter source, file dialogs, clipboard integration,
shell/browser actions, discovery execution, solver execution, dependency
installation, issue mutation, release mutation, validation-pass claims,
issue-closure claims, bundled-solver claims, or certification claims.

The GUI export summary view-model follow-up
[optional solver GUI export summary view-model](../experimental/optional_solver_gui_export_summary_viewmodel.md)
implements the pure payload/rendering layer for that future workflow. It
renders redacted JSON, Markdown, and plain text in memory and analyzes save
paths without GUI source changes, file dialogs, file writes, clipboard
integration, shell/browser actions, discovery execution, solver execution,
dependency installation, issue mutation, release mutation, validation-pass
claims, issue-closure claims, bundled-solver claims, or certification claims.

The GUI export summary implementation follow-up
[optional solver GUI export summary implementation](../experimental/optional_solver_gui_export_summary_implementation.md)
adds the redacted GUI export action over that payload layer. It writes exactly
one explicitly selected `.json`, `.md`, or `.txt` file only after save-plan and
overwrite checks, while still avoiding clipboard integration, shell/browser
actions, output-folder opening, discovery refresh, solver execution,
dependency installation, issue mutation, release mutation, validation-pass
claims, issue-closure claims, bundled-solver claims, or certification claims.

The GUI discovery refresh design follow-up
[optional solver GUI discovery refresh design](../experimental/optional_solver_gui_discovery_refresh_design.md)
defines the future explicit passive refresh workflow for the health panel. It
keeps refresh user-initiated, routes work through a future injected runner,
requires atomic view-model replacement, preserves redaction, defines export
interaction, and keeps active validation, solver execution, dependency
installation, issue mutation, release mutation, validation-pass claims,
issue-closure claims, bundled-solver claims, or certification claims out of
scope.

The GUI discovery refresh view-model follow-up
[optional solver GUI discovery refresh view-model](../experimental/optional_solver_gui_discovery_refresh_viewmodel.md)
implements the pure state/apply layer for that workflow. It models request and
result metadata, action states, success/failure/cancel/stale handling,
selection/filter preservation, status/error text, and atomic replacement plans
over supplied passive reports, while still adding no GUI wiring, background
worker, threading, discovery execution, solver execution, dependency
installation, issue mutation, release mutation, validation-pass claims,
issue-closure claims, bundled-solver claims, or certification claims.

The GUI discovery refresh implementation follow-up
[optional solver GUI discovery refresh implementation](../experimental/optional_solver_gui_discovery_refresh_implementation.md)
wires that pure layer into the PySide health panel as an explicit passive
refresh action. It supports injected runners for tests, a default built-in
passive discovery runner, status/error display, atomic accepted view-model
replacement, and export-after-refresh behavior, while still adding no
automatic startup refresh, background worker, active validation, solver
execution, dependency installation, issue mutation, release mutation,
validation-pass claims, issue-closure claims, bundled-solver claims, or
certification claims.

The plugin manifest loading design follow-up
[optional solver plugin manifest loading design](../experimental/optional_solver_plugin_manifest_loading_design.md)
defines how future plugin-provided optional solver manifest metadata can be
sourced, labeled, validated, diagnosed, and displayed without executing plugin
code or trusting third-party manifests by default. It keeps this step
docs/tests-only and adds no loader, plugin scan, network marketplace, solver
execution, dependency installation, issue mutation, release mutation,
validation-pass claims, issue-closure claims, bundled-solver claims, or
certification claims.

The plugin manifest loader model follow-up
[optional solver plugin manifest loader model](../experimental/optional_solver_plugin_manifest_loader_model.md)
implements explicit dict and explicit JSON loading for declarative manifest
data only. It returns accepted/rejected records, source/trust labels,
conflicts, and safety diagnostics while adding no CLI/GUI behavior change,
package import, directory scan, network fetch, solver execution, dependency
installation, issue mutation, release mutation, validation-pass claims,
issue-closure claims, bundled-solver claims, or certification claims.

## Guardrails

- External solvers are not bundled.
- No certification claim is made.
- Live validation remains environment-dependent.
- Optional solver manifest UX must not become solver installation,
  automatic execution, validation pass evidence, or issue closure evidence.
