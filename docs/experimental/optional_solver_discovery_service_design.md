# Optional solver discovery service design

## Status

`design-only`

- No discovery implementation.
- No solver execution.
- No dependency installation.
- No CLI command implementation.
- No GUI panel implementation.
- No plugin loading implementation.
- No external command execution.

## Current baseline

- Current public release: `v0.1.5-rc1`
- Release state: public prerelease, not draft
- Optional solver manifest schema/model exists:
  [Optional solver manifest schema model](optional_solver_manifest_schema_model.md)
- Optional solver manifest UX design exists:
  [Optional solver manifest UX design](optional_solver_manifest_ux_design.md)
- Issues `#6` through `#11` remain open.
- OSW-VALID-005 classified all `#6` through `#11` targets as
  `skipped-missing` on the current machine.
- External solvers are not bundled.
- Live optional validation remains environment-dependent.

## Relationship to manifest schema

The future discovery service consumes `OptionalSolverManifest` records from the
schema/model layer. It uses declarative requirements, environment hints,
documentation refs, safety notes, and probe declarations as input metadata.

The service maps evidence to the manifest health states, but it must never mutate manifests during discovery.
Manifest records remain declarative source data; discovery results are separate
evidence records.

Probe declarations in a manifest are not permission to execute commands. They
are future validation metadata that only an explicitly authorized validation
gate or acknowledged mode may use.

## Discovery modes

Future discovery design separates these modes:

- Passive metadata inspection.
- Path or executable presence check, future implementation only.
- Python package presence check, future implementation only.
- Active smoke validation reserved for explicit validation gates.
- No install mode.

Passive metadata inspection can read built-in manifests, plugin manifest
metadata after validation, and existing tracked validation docs. It should not
run commands, import optional solver packages, probe the system, or write
runtime artifacts.

Presence checks, when implemented in a later source gate, should identify
whether configured executable names or Python package names appear available.
That still is not a smoke pass. It is only discovery evidence.

## Passive versus active boundary

- Passive discovery may classify likely presence or absence.
- Active validation may run commands only in explicit validation gates.
- CLI and GUI doctor surfaces must not run solvers by default.
- There must be no hidden solver execution.
- There must be no automatic package import probes in passive paths.
- Health states from passive discovery must not be presented as validation
  success.

The first implementation slice should default to metadata-only or presence-only
behavior. Any command execution, solver execution, or smoke validation requires
a separate gate, explicit timeout policy, artifact policy, and issue policy.

## Discovery result concept

A future discovery result record should contain:

- stack id
- manifest version or manifest reference
- discovered executables
- discovered Python packages
- environment hints considered
- health state
- diagnostics
- confidence
- privacy redactions
- timestamp
- source of evidence

The result should be serializable for future JSON output and GUI handoff. It
should distinguish evidence from assumptions and should make stale or partial
evidence obvious.

## Diagnostics

Discovery diagnostics should include:

- missing executable
- missing Python package
- partial stack
- unsupported platform
- blocked probe
- unsafe probe skipped
- stale cache
- manifest error
- permission or path issue

Diagnostics should include a code, severity, message, field or source path
where applicable, and a suggested next action. They should be actionable
without suggesting automatic installation.

## Health-state mapping

The discovery service should use the manifest health-state vocabulary:

- unknown
- missing
- partially installed
- discovered
- smoke passed
- smoke failed
- blocked no safe case
- unsupported platform
- skipped by user

Mapping rules:

- No evidence maps to `unknown`.
- Required components absent map to `missing`.
- Some required components present and others absent map to
  `partially installed`.
- Required components found by presence checks map to `discovered`.
- `smoke passed` and `smoke failed` require explicit validation-gate evidence.
- Available commands without a safe validation case map to
  `blocked no safe case`.
- Platform-incompatible manifests map to `unsupported platform`.
- User-declined checks map to `skipped by user`.

## Privacy/security

- No telemetry.
- Do not expose the full `PATH` by default.
- Redact user paths in exported reports unless explicitly requested.
- Do not collect secrets.
- Do not store credentials.
- Do not run installer commands.
- Do not download solvers.
- Do not import optional solver packages in passive discovery.
- Do not execute manifest probe commands in passive discovery.
- Treat plugin-provided manifests as untrusted metadata until validated.

Any future exported report should prefer summarized evidence, basename-only
executable hints where possible, and explicit redaction markers for sensitive
local paths.

## Future CLI handoff

Future CLI UX can expose:

- `optional-solver list`
- `optional-solver doctor`
- `optional-solver explain`
- JSON output
- explicit `--run-smoke` reserved for a future validation gate or clearly
  acknowledged mode
- no install command in initial scope

Default list, doctor, and explain commands should be read-only, diagnostic, and
non-executing. They may summarize manifests and passive discovery evidence but
must not run solvers by default.

## Future GUI handoff

Future GUI UX can expose:

- optional solver health panel
- per-stack cards
- missing, partial, and discovered states
- issue links
- prepared-machine guidance
- validation history summary
- no install buttons in initial scope

The GUI should explain what is missing and where validation evidence lives. It
should not execute solvers directly, install dependencies, or mutate issues.

## Plugin ecosystem

The discovery service should begin with core built-in manifests. Future plugins may provide manifests after schema validation.

Plugin manifests are a trust boundary:

- schema validation is required
- untrusted plugin manifests cannot execute code
- plugin import must avoid side effects
- plugin manifests must not carry credentials or provider secrets
- plugin manifests must not install dependencies
- plugin manifests must not bypass OSW validation policy

Future plugin fields should remain aligned with the OSW plugin contract:
stable id, display name, version, type, entry point, capabilities, optional
extras, preview or validation requirements, validation messages, and
limitations.

## Validation relationship

OSW-VALID gates can use discovery results as precheck evidence later. Discovery
results can identify what should be validated, what is missing, and what
prepared-environment guidance applies.

Policy boundaries:

- `skipped-missing` remains neither pass nor failure.
- Plain policy wording: skipped-missing remains neither pass nor failure.
- Issue closure requires `passed-installed` evidence plus a separate closure
  review gate.
- Passive discovery alone cannot close issues.
- Smoke states require explicit validation evidence.
- Issues `#6` through `#11` remain open after this design gate.

## Caching and freshness

A future cache is optional. If added, it must show:

- timestamp
- source of evidence
- manifest reference
- OSW version
- redaction policy used

Stale cache data cannot justify issue closure. Users must be able to refresh
the evidence, and future CLI/GUI surfaces should show when cached evidence is
old or incomplete.

## Non-goals

- No implementation in this gate.
- No solver execution.
- No package import probes.
- No dependency install.
- No solver download.
- No issue mutation.
- No release mutation.
- No CLI command source.
- No GUI panel source.
- No discovery service source.
- No health probe execution.
- No bundled solver claim.
- No certification claim.

## Future implementation slices

- `OSW-EXP-058_OPTIONAL_SOLVER_DISCOVERY_SERVICE_IMPLEMENTATION` - completed as
  the passive discovery source layer in
  [Optional solver discovery service implementation](optional_solver_discovery_service_implementation.md).
- `OSW-EXP-059_OPTIONAL_SOLVER_CLI_DOCTOR_PREVIEW` - completed as a passive
  text/JSON CLI preview in
  [Optional solver CLI doctor preview](optional_solver_cli_doctor_preview.md).
- `OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN`
- `OSW-VALID` prepared-machine validation reuse

## Implementation follow-up

The implementation follow-up adds passive discovery models, injectable
resolvers, default passive resolvers, redacted report serialization, health
mapping, diagnostics, built-in manifest discovery, and explanation helpers. It
still adds no CLI command source, GUI panel source, plugin loading, active smoke
validation, solver execution, external command execution, dependency
installation, issue mutation, release mutation, bundled-solver claim, or
certification claim.

## CLI preview follow-up

The CLI preview follow-up adds passive `optional-solver-list`,
`optional-solver-doctor`, and `optional-solver-explain` surfaces over the
manifest and discovery layers. It provides text and JSON output with default
redaction, no environment-value exposure, no install command, no active smoke
mode, no solver command execution, no issue mutation, no release mutation, and
no validation-pass or issue-closure claim.
