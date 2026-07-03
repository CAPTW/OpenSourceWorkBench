# Optional Solver Prepared-Machine Validation Command Implementation

## Status

The optional solver prepared-machine validation command is implemented for
`OSW-EXP-140_OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND_IMPLEMENTATION`.

The command is local-only. It separates preflight, plan, and run behavior. It
performs no dependency installation, no solver installation, no solver
execution, no arbitrary user project workload execution, no ProjectSchema
mutation, no ProjectSchema evidence creation, no issue/release/tag/asset
mutation, no version bump, no validation-pass overclaim, no validation-fail
overclaim, no issue closure claim, no bundled solver support claim, and no
certification claim.

## Purpose

The command gives maintainers a safe runnable surface for the next
prepared-machine validation retry. It checks whether the local environment has
the optional solver/package prerequisites documented by the parked
prepared-machine validation gate and classifies missing prerequisites as
`parked`/`skipped-missing`.

The command is setup/readiness evidence only. It does not prove solver
correctness, does not close issues `#6` through `#11`, and does not alter
release state.

## Public Command/Module Names

Command family:

```text
python -m osw.cli optional-solver-prepared-machine-validation ...
```

Implementation module:

```text
osw.cli.optional_solver_prepared_machine_validation
```

Dispatcher registration:

```text
src/osw/cli/main.py
```

## Subcommands

The command registers these subcommands:

- `explain`
- `prerequisites`
- `preflight`
- `plan`
- `run`
- `diagnostics`
- `evidence`
- `safety`

`explain`, `plan`, `diagnostics`, `evidence`, and `safety` are rendering
surfaces. `preflight` and `run` evaluate prerequisites safely. `run` requires
explicit prepared-machine, optional-validation acknowledgement, and local-only
confirmation flags.

## Prerequisite Catalog

The catalog is deterministic and ordered:

| Identifier | Requirement | Detection policy |
| --- | --- | --- |
| `gmsh_executable` | `gmsh` executable | `shutil.which("gmsh")` |
| `python_gmsh` | Python `gmsh` module | `importlib.util.find_spec("gmsh")` |
| `octave_executable` | `octave` or `octave-cli` executable | `shutil.which(...)` only |
| `ccx_executable` | `ccx` executable | `shutil.which("ccx")` |
| `openfoam_commands` | `foamVersion`, `blockMesh`, `simpleFoam` | `shutil.which(...)` only |
| `python_meshio` | Python `meshio` module | `importlib.util.find_spec("meshio")` |
| `python_pyvista` | Python `pyvista` module | `importlib.util.find_spec("pyvista")` |
| `python_vtk` | Python `vtk` module | `importlib.util.find_spec("vtk")` |
| `python_coolprop` | Python `CoolProp` module | `importlib.util.find_spec("CoolProp")` |
| `python_cantera` | Python `cantera` module | `importlib.util.find_spec("cantera")` |

## Detection Policy

Executable checks use `shutil.which` only. Python package checks use
`importlib.util.find_spec` only. The command does not import optional packages,
run executable version commands, invoke shell commands, call subprocesses, scan
arbitrary directories, fetch network manifests, or install anything.

OpenFOAM readiness is a small command-presence group check for
`foamVersion`, `blockMesh`, and `simpleFoam`. Partial availability is reported
as partial/missing setup state, not as validation failure.

## Preflight Behavior

`preflight` evaluates the prerequisite catalog safely. It returns:

- `0` when all required prerequisite checks are present;
- `2` when any required prerequisite is missing or partially available;
- `1` only for internal command errors.

Missing prerequisites classify the command status as `parked` and populate
`missing_prerequisites` and `skipped_missing` separately. Preflight output is
not solver validation evidence and is not a certification claim.

## Plan Behavior

`plan` returns `0` and writes no evidence. It lists the local run envelope:
explain workflow, check prerequisites, classify readiness, write local evidence
only when explicitly requested, and preserve ProjectSchema/issue/release/tag/
asset/version boundaries.

Plan output is review text. It is not a validation pass, validation failure,
issue closure, release mutation, or solver support claim.

## Run Behavior

`run` requires all of:

```text
--prepared-machine
--acknowledge-optional-solver-validation
--confirm-local-only
```

If any acknowledgement is missing, `run` returns `2` and writes no evidence.
With acknowledgements present, it evaluates prerequisites. Missing
prerequisites return `2` with `parked` status. Present prerequisites return
`0` for completion of the local preflight/manifest-state validation envelope
only.

`run` does not execute solvers, run arbitrary projects, mutate ProjectSchema,
mutate issues/releases/tags/assets, bump versions, or claim certification.

## Evidence Behavior

Evidence writing is off by default. Evidence is written only when both
`--write-evidence` and `--evidence-dir <path>` are supplied to a subcommand
that allows evidence writes (`preflight`, `run`, or `evidence`).

The evidence directory must already exist and must be a local filesystem
directory. The command does not create parent directories, does not use a
default path, and does not write checked-in runtime evidence. Evidence consists
only of local JSON and Markdown files:

```text
optional_solver_prepared_machine_validation_evidence.json
optional_solver_prepared_machine_validation_evidence.md
```

Evidence is not a release asset, not ProjectSchema evidence, not issue
closure evidence, not bundled-solver support evidence, and not certification
evidence.

## Output Behavior

Text output is the default. `--json` emits deterministic JSON with sorted keys.
Output includes the command, subcommand, status, exit code, optional caller-
supplied git SHA, prerequisite table, missing prerequisites, skipped-missing
entries, diagnostics, evidence paths when written, non-actions, limitations,
exit semantics, and safety guidance.

Output redacts secret-like supplied strings and does not include tokens, API
keys, OAuth/provider/MCP data, raw plugin code, full file contents, or network
manifest data.

## Exit-Code Policy

The command uses:

| Code | Meaning |
| --- | --- |
| `0` | Command completed; pure rendering command completed or all required local checks are present. |
| `1` | Internal error. |
| `2` | Prerequisites missing, parked, or acknowledgement missing. |
| `3` | Validation checks failed; reserved for future bounded validation checks. |
| `4` | Unsafe request or forbidden mutation attempt. |
| `5` | Ambiguous configuration. |

Exit code `0` is not certification, not issue closure, not release mutation,
not bundled solver support, and not a validation overclaim.

## Skipped-Missing Policy

Every missing or partially available required prerequisite is reported in
`skipped_missing`. Skipped-missing is separate from pass and separate from
validation failure. Missing setup parks the prepared-machine validation retry
instead of producing a pass/fail claim.

## ProjectSchema Boundary

The command imports no ProjectSchema source and mutates no ProjectSchema data.
It creates no ProjectSchema evidence, adds no ProjectSchema fields, performs no
ProjectSchema migration, and does not reinterpret reload acceptance
persistence, summary audit, or boundary output as ProjectSchema state.

## Issue/Release Boundary

The command mutates no GitHub issues, releases, tags, or assets. It does not
close issues `#6` through `#11`, upload evidence as release assets, edit release
body text, create or move tags, or bump package metadata. Results may inform a
later separate review gate only.

## Certification Boundary

The command makes no industrial accuracy, compliance, production readiness,
solver support, bundled solver, or certification claim. It is a local
prepared-machine readiness envelope only.

## Security/Privacy Review

The implementation uses only standard-library metadata checks and local file
writing when explicitly requested. It performs no shell execution, no
subprocess calls, no network requests, no provider/OAuth/MCP behavior, no
credential scraping, no arbitrary directory scan, and no optional package
imports. Secret-like caller-supplied strings are redacted from output.

## Non-Actions

This implementation performs no dependency install/uninstall, no solver
install/uninstall, no solver execution, no arbitrary project workload, no live
directory discovery, no network/provider/OAuth/MCP behavior, no ProjectSchema
mutation/evidence, no issue/release/tag/asset mutation, no version bump, no
validation success/failure overclaim, no issue closure claim, no bundled solver
support claim, and no certification claim.

## Testing Strategy

Focused unit tests cover module import, dispatcher registration, subcommand
output, prerequisite catalog rendering, fake missing/present prerequisite
states, parked classification, deterministic JSON, explicit run
acknowledgements, evidence writing only under `tmp_path`, deterministic local
evidence, skipped-missing separation, source guardrails against installs,
subprocess/network/ProjectSchema/GitHub mutation imports or calls, and
continued docs/boundary tests.

## Relationship To OSW-EXP-139 Design

OSW-EXP-139 reserved the command vocabulary and safety contract in
[Optional solver prepared-machine validation command design](optional_solver_prepared_machine_validation_command_design.md).
This gate implements that local-only command surface while preserving the
designed boundaries.

## Relationship To Parked OSW-VALID

`OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` remains parked
until the command is run on an actual prepared environment and local evidence
is reviewed. This implementation provides the runnable command that the parked
gate lacked, but it does not itself close the validation gate or issues.

## Future Retry Process

A future validation retry should run `preflight`, review `plan`, then run
`run` with explicit acknowledgements and an explicit local evidence directory
on a machine where the required tools/packages are already installed. Missing
items must remain `skipped-missing` and parked. Passing local prerequisite
checks may feed a later review, but issue/release mutation remains separate.

## Future Gates

Suggested next gates:

- `OSW-EXP-140_FAST_FORWARD_MERGE_AND_PUSH`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_RESULTS_REVIEW_AND_ISSUE_TRIAGE`, only
  if validation completes and a separate review approves issue triage
