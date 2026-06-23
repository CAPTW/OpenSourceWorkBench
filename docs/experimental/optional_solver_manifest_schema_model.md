# Optional solver manifest schema model

## Status

`experimental schema/model implemented`

- No discovery implementation.
- No solver execution.
- No dependency installation.
- No CLI command implementation.
- No GUI panel implementation.

## Relationship to UX design

This gate implements the schema/model layer described by
[Optional solver manifest UX design](optional_solver_manifest_ux_design.md).
The model is declarative metadata for future optional solver UX. It does not
discover installed tools, import optional packages, run health checks, or
install dependencies.

## Package path and public API

Package path:

`src/osw/experimental/optional_solvers/`

Public API:

- `OptionalSolverManifest`
- `OptionalSolverRequirement`
- `OptionalSolverCapability`
- `OptionalSolverProbe`
- `OptionalSolverStackId`
- `OptionalSolverHealthState`
- `OptionalSolverSupportStatus`
- `OptionalSolverManifestDiagnostic`
- `OptionalSolverManifestValidationReport`
- `parse_optional_solver_manifest_dict`
- `validate_optional_solver_manifest`
- `load_optional_solver_manifest_json`
- `dump_optional_solver_manifest_json`
- `builtin_optional_solver_manifests`
- `get_builtin_optional_solver_manifest`
- `explain_optional_solver_manifest`

## Manifest fields

The schema model supports:

- `stack_id`
- `display_name`
- `related_issue`
- `capabilities`
- `executable_requirements`
- `python_package_requirements`
- `environment_variable_hints`
- `version_probe`
- `help_probe`
- `smoke_test_description`
- `prepared_machine_notes`
- `platform_notes`
- `documentation_refs`
- `support_status`
- `non_bundled_disclaimer`
- `safety_notes`

Probe fields are declarative command tokens only. The model stores them so a
later explicitly authorized validation gate can decide how to use them.

## Built-in stack manifests

Built-in manifests are provided for:

- `gmsh` for issue `#6`
- `octave` for issue `#7`
- `calculix` for issue `#8`
- `openfoam` for issue `#9`
- `coolprop_cantera` for issue `#10`
- `pyvista_meshio` for issue `#11`

The built-ins describe requirements, capabilities, safe smoke-test intent,
prepared-machine notes, platform notes, documentation references, support
status, safety notes, and non-bundled disclaimers. They do not claim any
optional stack is installed.

## Health states

The model defines these future UX health states:

- `unknown`
- `missing`
- `partially_installed`
- `discovered`
- `smoke_passed`
- `smoke_failed`
- `blocked_no_safe_case`
- `unsupported_platform`
- `skipped_by_user`

Health states are names for future UX and JSON output. They are not issue
closure evidence.

## Validation diagnostics

Structural validation returns `OptionalSolverManifestValidationReport` with
diagnostics containing:

- code
- severity
- message
- path
- suggested fix

Severity values are:

- `info`
- `warning`
- `error`
- `blocker`

Validation checks required fields, stable nonempty stack ids, display names,
issue mapping for built-ins, capability presence, requirement identifiers,
declarative probe shape, non-bundled disclaimers, safety boundaries, and string
documentation references.

## JSON IO helpers

The schema model includes helpers to parse manifest dictionaries and to load or
dump JSON manifest files:

- `parse_optional_solver_manifest_dict`
- `load_optional_solver_manifest_json`
- `dump_optional_solver_manifest_json`

The helpers read and write JSON only. They do not create parent directories
implicitly and do not execute probe declarations.

## Safety boundary

- Declarative only.
- No solver execution.
- No package import probes.
- No install commands.
- No bundled solver claim.
- No dependency installation.
- No solver installation.
- No release mutation.
- No issue mutation.
- No ProjectSchema mutation.
- No VLM provider or credential handling.
- No certification claim.

## Relationship to #6~#11

The manifests guide future validation and optional solver UX. Issues `#6`
through `#11` remain open after this gate.

The built-in manifest issue mapping is:

- Gmsh: `#6`
- GNU Octave: `#7`
- CalculiX: `#8`
- OpenFOAM: `#9`
- CoolProp / Cantera: `#10`
- PyVista / meshio: `#11`

Closure requires separate issue-specific validation and closure-review gates.
Skipped-missing evidence is not a pass and not a failure.

## Future gates

- `OSW-EXP-057_OPTIONAL_SOLVER_DISCOVERY_SERVICE_DESIGN` - completed as a
  design-only service contract in
  [Optional solver discovery service design](optional_solver_discovery_service_design.md).
- `OSW-EXP-058_OPTIONAL_SOLVER_DISCOVERY_SERVICE_IMPLEMENTATION` - completed as
  the passive discovery source layer in
  [Optional solver discovery service implementation](optional_solver_discovery_service_implementation.md).
- `OSW-EXP-059_OPTIONAL_SOLVER_CLI_DOCTOR_PREVIEW`
- `OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN`

## Discovery service design follow-up

The discovery service design defines how future gates can consume
`OptionalSolverManifest` records, map evidence to health states, report
diagnostics, redact local environment details, and hand off to CLI/GUI surfaces.
It does not add discovery service source, command execution, optional package
imports, CLI commands, GUI panels, issue mutation, release mutation, dependency
installation, solver execution, bundled-solver claims, or certification claims.

## Discovery service implementation follow-up

The discovery service implementation adds passive presence checks, injected
resolver seams, default passive resolvers, redacted report serialization,
health-state mapping, diagnostics, and built-in manifest discovery. It does not
add CLI commands, GUI panels, active smoke validation, external command
execution, optional solver package imports, dependency installation, solver
execution, issue mutation, release mutation, bundled-solver claims, or
certification claims.
