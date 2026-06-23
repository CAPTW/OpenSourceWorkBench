# Optional solver CLI doctor preview

## Status

Experimental CLI preview implemented.

This gate is passive discovery only:

- no solver execution
- no external solver command execution
- no active smoke validation
- no dependency installation
- no solver installation
- no GUI panel
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

- `OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
