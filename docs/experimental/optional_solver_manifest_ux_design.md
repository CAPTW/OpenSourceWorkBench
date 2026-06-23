# Optional solver manifest UX design

## Status

`design-only`

- No source implementation.
- No solver execution.
- No dependency installation.
- No manifest schema implementation.
- No discovery implementation.
- No CLI or GUI implementation.

## Current baseline

- Current public release: `v0.1.5-rc1`
- Release state: public prerelease, not draft
- Issues `#6` through `#11` remain open.
- OSW-VALID-005 classified all `#6` through `#11` targets as
  `skipped-missing`.
- External solvers are not bundled.
- Live optional validation remains environment-dependent.

## Problem statement

Users need clear optional solver and dependency discovery guidance before they
attempt live validation or optional workflows. OSW-VALID-005 showed that
missing optional stacks are common and should be actionable rather than opaque.

The project needs a consistent way to describe optional stacks, explain what is
missing, show what evidence exists, and guide prepared-environment validation
without installing dependencies, downloading solvers, or executing solvers in
ordinary UX paths.

## Target optional stacks

- Gmsh
- GNU Octave
- CalculiX
- OpenFOAM
- CoolProp / Cantera
- PyVista / meshio

## Manifest concept

Each optional solver or science stack should have a manifest concept with:

- stable stack id
- display name
- related issue number
- capabilities
- executable requirements
- Python package requirements
- environment variable hints
- version/help probes
- safe smoke-test description
- prepared-machine validation notes
- platform notes
- documentation links or internal guidance refs
- support status
- non-bundled solver disclaimer

The manifest should be descriptive metadata first. Future implementation gates
may turn it into a typed model, but this design does not add schema source or
runtime discovery behavior.

## UX health states

- unknown
- missing
- partially installed
- discovered
- smoke passed
- smoke failed
- blocked no safe case
- unsupported platform
- skipped by user

Health state names should be visible, stable, and safe to serialize in future
CLI JSON output. A state is diagnostic evidence, not issue closure evidence.

## Future CLI UX

Future CLI design can expose:

- optional solver list
- optional solver doctor
- optional solver explain
- JSON output
- no install command in initial scope
- no automatic solver execution unless an explicit validation gate authorizes
  it

The CLI should distinguish discovery from validation. Listing or explaining a
stack should never run solvers. A future validation command would need a
separate prompt, timeout policy, artifact policy, and issue policy.

## Future GUI UX

Future GUI design can expose:

- optional solver health panel
- per-stack status cards
- issue links
- prepared-environment guidance
- validation history summary
- no install buttons in initial scope

The GUI should help users understand why an optional feature is unavailable and
what prepared environment is needed. It should not directly execute solvers or
install software.

## Plugin ecosystem relationship

The first manifest set can be core built-in manifests for the known optional
stacks. Later plugin-provided manifests may extend the set if they pass
manifest validation.

Third-party manifest data is a trust boundary. Plugin manifests should be
treated as metadata, not executable code. They must not carry credentials,
provider secrets, shell commands that run by default, or side effects during
plugin import.

Future plugin-facing fields should align with the OSW plugin contract:

- stable id
- display name
- version
- plugin or stack type
- capabilities
- optional extras
- preview or validation requirements
- validation messages
- limitations

## Validation relationship

OSW-VALID gates may consume discovery and manifest data in later work, but
issue policy remains separate:

- skipped-missing is not failure and not pass
- issue closure remains separate
- validation artifacts remain under ignored artifact directories
- prepared-machine validation requires already installed tools or packages
- manifest health evidence should identify what was discovered and what was not

The open issues `#6` through `#11` remain the live optional validation tracking
issues until a separate issue-specific closure-review gate has appropriate
evidence.

## Safety and privacy

- No solver install.
- No dependency install.
- No bundled solvers.
- No telemetry.
- No leaking full environment details unless the user explicitly exports a
  report.
- No certification claim.
- No credentials or provider secrets.
- No automatic shell execution from manifest data.

## Non-goals

- No implementation in this gate.
- No package manager automation.
- No solver download.
- No solver execution.
- No issue closure.
- No release mutation.
- No manifest schema source.
- No discovery service source.
- No CLI command source.
- No GUI panel source.

## Future implementation slices

- `OSW-EXP-056_OPTIONAL_SOLVER_MANIFEST_SCHEMA_MODEL` - completed as the
  experimental schema/model layer in
  [Optional solver manifest schema model](optional_solver_manifest_schema_model.md).
- `OSW-EXP-057_OPTIONAL_SOLVER_DISCOVERY_SERVICE_DESIGN` - completed as the
  design-only service contract in
  [Optional solver discovery service design](optional_solver_discovery_service_design.md).
- `OSW-EXP-058_OPTIONAL_SOLVER_CLI_DOCTOR_PREVIEW`
- `OSW-EXP-059_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN`

## Schema model follow-up

The schema/model follow-up adds typed Python records, structural diagnostics,
JSON I/O helpers, and built-in declarative manifest fixtures. It does not add
discovery, CLI commands, GUI panels, solver execution, dependency installation,
issue mutation, release mutation, bundled-solver claims, or certification
claims.

## Discovery service design follow-up

The discovery service design defines passive metadata inspection, future
presence-check boundaries, active validation-gate separation, privacy
redaction, diagnostics, cache freshness, CLI/GUI handoff, and plugin manifest
trust boundaries. It still adds no discovery implementation, CLI command, GUI
panel, solver execution, external command execution, dependency installation,
issue mutation, release mutation, bundled-solver claim, or certification claim.
