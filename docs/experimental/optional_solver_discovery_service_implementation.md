# Optional solver discovery service implementation

## Status

Experimental passive discovery implemented.

This gate adds:

- passive optional solver discovery source
- discovery result models
- resolver injection
- JSON-compatible report helpers
- built-in manifest discovery

This gate does not add:

- no CLI
- no GUI
- no solver execution
- no external command execution
- no active smoke validation
- no dependency installation
- no solver installation
- no plugin loading
- no issue mutation
- no release mutation

## Relationship to design and manifest schema

The implementation follows
[Optional solver discovery service design](optional_solver_discovery_service_design.md)
and consumes the declarative manifest records from
[Optional solver manifest schema model](optional_solver_manifest_schema_model.md).

Discovery accepts `OptionalSolverManifest` instances, validates their structure,
checks passive presence evidence, and maps the result to manifest health states.
It does not mutate manifests.

## Package path and public API

Package path:

- `src/osw/experimental/optional_solvers/`

Public discovery API:

- `OptionalSolverExecutableDiscovery`
- `OptionalSolverPythonPackageDiscovery`
- `OptionalSolverEnvironmentHintDiscovery`
- `OptionalSolverStackDiscovery`
- `OptionalSolverDiscoveryReport`
- `OptionalSolverDiscoveryDiagnostic`
- `OptionalSolverDiscoveryOptions`
- `OptionalSolverPathRedactionMode`
- `discover_optional_solver_stack`
- `discover_optional_solver_manifests`
- `discover_builtin_optional_solvers`
- `explain_optional_solver_discovery`
- `optional_solver_discovery_report_to_dict`
- `optional_solver_discovery_report_from_dict`

## Passive discovery behavior

Passive discovery checks declared requirements without running solver probes.
For each stack it records:

- executable requirement presence
- Python package requirement presence
- environment-variable hint presence
- structural manifest diagnostics
- passive-only diagnostics
- health state
- confidence string

Passive discovery can classify a stack as missing, partially installed,
discovered, or unknown. It cannot classify a stack as smoke passed or smoke
failed.

## Resolver injection

The service accepts injected resolvers:

- `executable_resolver(name) -> path or None`
- `python_package_resolver(name) -> package info or None`
- `environment_resolver(name) -> value or None`

Tests use injected resolvers so results do not depend on local optional solver
installation.

## Default resolvers

Default resolvers are passive only:

- executable lookup uses `shutil.which`
- Python package lookup uses `importlib.util.find_spec` and
  `importlib.metadata.version`
- environment lookup uses `os.environ.get`

The Python package resolver checks import metadata but does not import optional solver packages.

## Path and environment redaction

Reports redact sensitive local values by default:

- executable paths are reported as redacted names
- environment values are reported as `<redacted>`
- full executable paths require `OptionalSolverPathRedactionMode.FULL`
- environment values require `include_environment_values=True`

Default serialized reports should not expose user paths or environment values.

## Health-state mapping

Passive health mapping is:

- invalid manifest: `unknown`
- no required passive requirements discovered: `missing`
- some required passive requirements discovered: `partially_installed`
- all required passive requirements discovered: `discovered`

Passive discovery does not emit:

- `smoke_passed`
- `smoke_failed`
- issue-closure readiness

## Diagnostics

Discovery diagnostics include:

- `OSD_MISSING_EXECUTABLE`
- `OSD_MISSING_PYTHON_PACKAGE`
- `OSD_MISSING_ENVIRONMENT_HINT`
- `OSD_PARTIAL_STACK`
- `OSD_MANIFEST_ERROR`
- `OSD_PATH_PERMISSION_ISSUE`
- `OSD_PATH_REDACTED`
- `OSD_ENVIRONMENT_VALUE_REDACTED`
- `OSD_PASSIVE_ONLY`

Diagnostics are evidence for setup guidance, not validation pass evidence.

## Built-in manifest discovery

`discover_builtin_optional_solvers` evaluates the six built-in declarative
manifests:

- `gmsh`
- `octave`
- `calculix`
- `openfoam`
- `coolprop_cantera`
- `pyvista_meshio`

Built-in discovery reports local passive presence only. It does not claim those
stacks are installed, bundled, validated, or ready for issue closure.

## Safety boundary

- No subprocess.
- No external command execution.
- No optional package import.
- No solver execution.
- No active smoke validation.
- No install commands.
- No solver download.
- No dependency installation.
- No solver installation.
- No CLI command source.
- No GUI panel source.
- No issue mutation.
- No release mutation.
- No bundled solver claim.
- No certification claim.

## Relationship to #6~#11

Discovery can inform future validation planning for:

- Gmsh: `#6`
- GNU Octave: `#7`
- CalculiX: `#8`
- OpenFOAM: `#9`
- CoolProp / Cantera: `#10`
- PyVista / meshio: `#11`

Missing or skipped discovery evidence is not a pass. Discovered passive
presence is also not a validation pass. Issues remain open until separate
validation and closure-review gates provide appropriate installed-only evidence.

## Future gates

- `OSW-EXP-059_OPTIONAL_SOLVER_CLI_DOCTOR_PREVIEW`
- `OSW-EXP-060_OPTIONAL_SOLVER_GUI_HEALTH_PANEL_DESIGN`
- `OSW-VALID` prepared-machine validation reuse
