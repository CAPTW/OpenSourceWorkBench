# Optional solver CLI doctor preview

## Status

Experimental CLI preview implemented.

This gate is passive discovery only:

- no solver execution
- no external solver command execution
- no active smoke validation
- no dependency installation
- no solver installation
- no GUI implementation
- no plugin loading
- no issue mutation
- no release mutation

## Command names and examples

Commands:

- `optional-solver-list`
- `optional-solver-doctor`
- `optional-solver-explain`

Examples:

```powershell
python -m osw.cli optional-solver-list
python -m osw.cli optional-solver-list --format json --include-requirements
python -m osw.cli optional-solver-doctor --all
python -m osw.cli optional-solver-doctor --stack calculix --format json
python -m osw.cli optional-solver-doctor --all --show-full-paths
python -m osw.cli optional-solver-explain --stack calculix
python -m osw.cli optional-solver-explain --stack calculix --format json
```

## Relationship to manifest schema and discovery service

The CLI preview uses the built-in declarative manifests from
[Optional solver manifest schema model](optional_solver_manifest_schema_model.md)
and the passive discovery report API from
[Optional solver discovery service implementation](optional_solver_discovery_service_implementation.md).

`optional-solver-list` reads manifest metadata only.
`optional-solver-doctor` runs passive discovery only.
`optional-solver-explain` reads one manifest and prints guidance.

## Text output behavior

Text output is intended for users:

- stack id
- display name
- related issue
- support status
- health state for doctor output
- missing, partial, or discovered status
- safety notes

Missing optional stacks are valid doctor results and return exit code `0`.
Unknown stack ids return nonzero.

## JSON output behavior

JSON output is parseable and intended for future automation or GUI handoff:

- list output returns manifest summaries
- doctor output returns passive discovery report dictionaries
- explain output returns one manifest dictionary plus passive-only safety flags

JSON output does not mean validation passed. It is setup evidence only.

## Redaction and privacy

- Paths are redacted by default.
- `--show-full-paths` is the only opt-in for full executable paths.
- Environment values are not exposed in this gate.
- JSON output uses the same redaction policy as text output.
- No telemetry is collected.
- No credentials or provider secrets are collected.

## Missing, partial, and discovered states

Passive doctor output can report:

- `missing`
- `partially_installed`
- `discovered`
- `unknown`

It does not report active validation states such as `smoke_passed` or
`smoke_failed`.

## Safety boundary

- No install command.
- No active smoke execution.
- No solver command execution.
- No issue mutation.
- No bundled solvers.
- No dependency installation.
- No solver installation.
- No release mutation.
- No certification claim.

The CLI does not provide `--install`, `--run-smoke`, or `--execute` options for
optional solver stacks.

## Relationship to #6~#11

The CLI helps explain skipped-missing evidence for:

- Gmsh: `#6`
- GNU Octave: `#7`
- CalculiX: `#8`
- OpenFOAM: `#9`
- CoolProp / Cantera: `#10`
- PyVista / meshio: `#11`

Issue closure remains separate. Passive discovery cannot close issues and does
not replace prepared-machine validation.

## Future gates

- `OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN` - completed as a
  design-only GUI health panel contract in
  [Optional solver GUI health panel design](optional_solver_gui_health_panel_design.md).
- `OSW-EXP-061_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_VIEWMODEL` - completed as a
  pure UI-agnostic view-model in
  [Optional solver GUI health panel view-model](optional_solver_gui_health_panel_viewmodel.md).
- `OSW-EXP-062_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_IMPLEMENTATION` - completed
  as a PySide display-only panel in
  [Optional solver GUI health panel implementation](optional_solver_gui_health_panel_implementation.md).
- `OSW-VALID` prepared-machine validation reuse

## GUI health panel design follow-up

The GUI health panel design follow-up defines future entry points, stack cards,
details and diagnostics panels, guidance, validation history, privacy/redaction
behavior, user actions, a view-model boundary, accessibility expectations, and
plugin trust labels for the optional solver health surface. It consumes the
same manifest and passive discovery semantics as the CLI preview, but it adds
no GUI source, view-model source, CLI behavior change, plugin loading, active
smoke validation, external solver command execution, solver execution,
dependency installation, issue mutation, release mutation, validation-pass
claim, issue-closure claim, bundled-solver claim, or certification claim.

## GUI health view-model follow-up

The GUI health view-model follow-up consumes the same manifest and supplied
passive discovery report records as the CLI preview and produces deterministic
GUI-ready summary, card, details, diagnostics, guidance, validation-history,
and action-state records. It adds no PySide import, Qt import, GUI widget,
CLI behavior change, discovery execution, active smoke validation, external
solver command execution, solver execution, dependency installation, issue
mutation, release mutation, validation-pass claim, issue-closure claim,
bundled-solver claim, or certification claim.

## GUI health panel implementation follow-up

The GUI health panel implementation follow-up renders an already-built
view-model in PySide. It does not call the CLI, perform discovery refresh,
execute active smoke validation, run external solver commands, install
dependencies, mutate issues, edit releases, claim validation success, claim
issue closure readiness, bundle solvers, or claim certification.
