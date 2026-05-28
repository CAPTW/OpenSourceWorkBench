# Runner Diagnostics

`OSW-FUNC-003_RUNNER_DIAGNOSTICS` adds the shared backend boundary for future
solver and script execution. It is infrastructure only: no concrete solver
adapter is implemented here, and the GUI remains disconnected from direct
subprocess execution.

## Diagnostic Model

Core diagnostics live in `osw.core.diagnostics`.

`DiagnosticMessage` carries:

- severity: `info`, `warning`, `error`, `critical`
- code
- message
- hint
- source
- field
- path
- command
- return code
- metadata

`DiagnosticReport` collects messages, reports warnings/errors, serializes to
plain dictionaries, and provides a user-readable summary for CLI and future GUI
use.

Stable runner-related codes include:

- `executable-not-found`
- `executable-not-configured`
- `command-timeout`
- `command-failed`
- `command-completed`
- `stdout-captured`
- `stderr-captured`
- `artifact-missing`
- `artifact-collected`
- `invalid-working-directory`
- `unsafe-shell-command`
- `environment-variable-missing`
- `log-warning-detected`
- `log-error-detected`
- `dependency-unavailable`

## Executable Registry

`ExecutablePathRegistry` resolves external tools without running them.

Resolution order:

1. Explicit configured path.
2. Configured environment variable.
3. `PATH` lookup via `shutil.which`.
4. Missing diagnostic.

The registry does not call `--version`, install tools, mutate the environment,
or execute solver binaries.

`OSW-FUNC-004_PLUGIN_MANAGER_DIALOG_BINDING` uses the same resolution semantics
for plugin executable diagnostics. The Plugin Manager can store configured
paths, but GUI health checks still only resolve paths; they do not execute the
target executable.

## External Command Runner

`ExternalCommandRunner` accepts argument lists, not shell strings. It validates
requests, captures stdout/stderr, enforces timeouts, and returns a structured
`RunResult`.

Primary model objects:

- `RunStatus`
- `TimeoutPolicy`
- `RunLog`
- `RunArtifact`
- `RunRequest`
- `RunResult`

The runner writes standard artifacts into the controlled artifact directory:

- `stdout.txt`
- `stderr.txt`
- `run_summary.json`

Optional artifact glob patterns can collect additional files. Missing artifact
patterns produce warnings rather than crashes.

## Run Manager

`RunManager` creates run IDs, creates run directories, delegates to
`ExternalCommandRunner`, and saves/loads JSON run summaries. It is generic and
contains no solver-specific behavior.

## Log Parser

`GenericLogParser` detects common warning, error, residual, and progress lines
without assuming a specific solver format. Solver-specific parsers may compose
or subclass it later.

## CLI

Safe CLI commands:

```powershell
python -m osw.cli runner-check python
python -m osw.cli runner-fake-smoke
```

`runner-check` resolves an executable path only. It does not execute the target.

`runner-fake-smoke` runs a deterministic Python one-liner through the backend
runner and is intended as a local smoke test for the runner service.

## Security Rules

- GUI code must not launch external solver subprocesses directly.
- Commands use `list[str]`; `shell=True` is rejected by diagnostics.
- Working directories are validated before execution.
- Timeouts terminate the child process.
- Environment overrides are explicit.
- Runtime artifacts stay under caller-provided run or artifact directories.
- Tests use a Python fake solver helper, not external solver binaries.

## Known Limitations

- Process-tree termination is intentionally minimal and cross-platform.
- No solver-specific log parser is included in this step.
- No CalculiX, OpenFOAM, SU2, Octave, MATLAB, Cantera, or CoolProp concrete
  runner binding is added by this step.

## CalculiX Runner Binding

`OSW-FUNC-014_CALCULIX_RUNNER_BINDING` adds a bounded CalculiX `ccx` binding on
top of this backend runner. The binding resolves `ccx` through
`ExecutablePathRegistry` without executing it, copies an explicit `.inp` deck
into an isolated case directory by default, runs `ccx jobname` through
`ExternalCommandRunner`, captures stdout/stderr, applies the configured timeout,
and records CalculiX artifacts such as `.dat`, `.frd`, `.sta`, `.cvg`, `.12d`,
`.log`, and the copied `.inp`.

The binding does not parse CalculiX result files or add nonlinear/contact
features. Missing `ccx`, missing decks, timeouts, nonzero return codes, and
missing expected artifacts are surfaced as structured diagnostics.

## Next Step

Next functional step: `OSW-FUNC-015_CALCULIX_RESULT_PARSER`.
