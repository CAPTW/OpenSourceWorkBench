# Optional Solver Prepared-Machine Validation Command Design

## Status

This is design-only documentation for
`OSW-EXP-139_OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND_DESIGN`.

This gate adds no command implementation, no CLI source edits, no source
edits, no dependency installation, no solver installation, no solver
execution, no live discovery, no live validation, no live optional validation, no ProjectSchema
mutation, no ProjectSchema evidence creation, no issue mutation, no release
mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue closure claim, no
bundled solver support claim, and no certification claim.

The names and behaviors below reserve a future local command contract only.
They do not create a runnable command in this gate.

## Purpose

This document defines a future safe runnable command for prepared-machine
optional solver manifest-state validation. The command is needed because
`OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` remains parked:
the latest retry found no safe runnable prepared-machine command and the local
optional solver/package prerequisites were missing or not verified.

The future command must let maintainers retry prepared-machine validation on a
machine that is already prepared, without turning focused regression tests,
docs-only evidence, passive discovery, local persistence records, summary
audit rows, or ProjectSchema boundary output into prepared-machine validation.

## Current Parked Baseline

Parked gate:
`OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`.

Parked status: `Parked`.

Starting SHA: `42d687626955a516f4072ad07b058e0f665fceaf`.

Prerequisites documentation commit:
`1872de79e87340821c4eeb274f7c6406d659c2ff`.

Baseline facts:

- no runnable prepared-machine manifest-state validation command was found;
- required local optional prerequisites were missing or not verified;
- focused regression and QA/static checks are useful continuity evidence but
  are not prepared-machine validation;
- skipped-missing evidence remains separate from pass and failure.

The prerequisite baseline is documented in
[Optional solver prepared-machine manifest-state validation prerequisites](optional_solver_prepared_machine_manifest_state_validation_prerequisites.md).

## Future Command Name And Location

The proposed future command family is:

```text
python -m osw.cli optional-solver-prepared-machine-validation ...
```

Suggested future subcommands:

- `explain`
- `preflight`
- `plan`
- `run`
- `diagnostics`
- `prerequisites`
- `evidence`
- `safety`

These names are reserved by design only. No command exists in this gate. Any
future implementation requires
`OSW-EXP-140_OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND_IMPLEMENTATION`
or another repo-consistent implementation gate.

## Command Source Policy

Future implementation must be explicit, local-only, and operator-invoked. It
must avoid implicit or background validation.

Future implementation must use local-only checks, explicit operator invocation,
deterministic text and JSON output, and local evidence under
`.codex/reports/validation/`.

Future implementation must avoid:

- network/provider/OAuth/MCP behavior;
- issue, release, tag, or asset mutation;
- ProjectSchema mutation;
- ProjectSchema evidence creation;
- dependency or solver installation;
- dependency or solver uninstallation;
- arbitrary user project solver jobs;
- certification claims;
- bundled solver support claims.

## Prerequisite Model

The future command must model each prerequisite as a local setup requirement,
not as something the command installs. Detection commands are examples for a
future implementation contract; they are not run by this design gate.

| Identifier | Type | Detection command | Safe detection behavior | Failure classification | Missing result | Skipped-missing may be success |
| --- | --- | --- | --- | --- | --- | --- |
| `gmsh_executable` | executable | `where gmsh` | Resolve only on local PATH; version query only if explicitly safe. | missing / unavailable / not verified | parked, not failed validation | no |
| `python_gmsh` | Python import | `python -c "import gmsh"` | Import in a bounded subprocess in a future implementation; capture version only if safe. | missing / unavailable / not verified | parked, not failed validation | no |
| `octave` | executable | `where octave`; `where octave-cli` | Resolve only local executable names; do not run arbitrary `.m` scripts. | missing / unavailable / not verified | parked, not failed validation | no |
| `ccx` | executable | `where ccx` | Resolve only local CalculiX executable path; do not run a user model. | missing / unavailable / not verified | parked, not failed validation | no |
| `openfoam_commands` | solver stack | `where foamVersion`; `where blockMesh`; `where icoFoam`; `where simpleFoam`; `where foamRun` | Check initialized local shell commands only; do not create or run broad OpenFOAM cases. | missing / unavailable / not verified | parked, not failed validation | no |
| `python_meshio` | Python import | `python -c "import meshio"` | Import locally only; do not fetch packages or scan arbitrary directories. | missing / unavailable / not verified | parked, not failed validation | no |
| `python_pyvista` | Python import | `python -c "import pyvista"` | Import locally only; headless rendering remains optional and diagnosable. | missing / unavailable / not verified | parked, not failed validation | no |
| `python_vtk` | Python import | `python -c "import vtk"` | Import locally only; presence alone is not validation evidence. | missing / unavailable / not verified | parked, not failed validation | no |
| `python_coolprop` | Python import | `python -c "import CoolProp"` | Import locally only; no package install or network access. | missing / unavailable / not verified | parked, not failed validation | no |
| `python_cantera` | Python import | `python -c "import cantera"` | Import locally only; no package install or network access. | missing / unavailable / not verified | parked, not failed validation | no |

Missing prerequisites cause the future command to report `skipped-missing` or
parked status for affected targets. Missing prerequisites must not be reported
as pass.

## Preflight Subcommand Design

Future `preflight` must check prerequisites without installing dependencies or
solvers. It may report detected versions when doing so is safe and local.

Preflight must:

- never install dependencies;
- never install solvers;
- never execute solver jobs;
- never run arbitrary user project workloads;
- never mutate ProjectSchema;
- never create ProjectSchema evidence;
- never mutate issues, releases, tags, or assets;
- produce local preflight evidence under `.codex/reports/validation/`;
- distinguish missing prerequisites from validation check failures;
- report `skipped-missing` separately from pass.

Preflight completion is setup evidence only. It is not prepared-machine
validation by itself.

## Plan Subcommand Design

Future `plan` must enumerate exactly what validation would run before any
solver or package validation occurs.

Plan output must identify:

- optional solver families mapped to issues #6 through #11;
- prerequisite checks and their latest preflight state;
- whether local solver discovery would happen;
- whether solver execution would happen;
- expected evidence file names and directories;
- non-actions that remain guaranteed;
- required acknowledgements for `run`;
- cases that would stay `skipped-missing`.

Plan must require explicit operator review before `run`. Plan output is not a
validation-pass claim and not a validation-fail claim.

## Run Subcommand Design

Future `run` must require successful preflight for all required in-scope checks
or report a parked/skipped-missing outcome. It must require explicit flags:

```text
--prepared-machine
--acknowledge-optional-solver-validation
--confirm-local-only
```

Run must:

- write evidence only under `.codex/reports/validation/`;
- avoid ProjectSchema mutation;
- avoid ProjectSchema evidence creation;
- avoid issue, release, tag, or asset mutation;
- avoid certification claims;
- avoid arbitrary user project workloads;
- report skipped-missing separately from pass;
- report failed validation checks separately from missing prerequisites.

The future command may use only tiny, deterministic, documented checks. Solver
execution, if any, must be explicitly acknowledged and limited to the bounded
prepared-machine checks defined by OSW-EXP-140 or a later implementation gate.

## Solver Discovery Boundary

Future discovery is local only. It must not fetch network manifests, use
provider/OAuth/MCP behavior, scrape credentials, or scan arbitrary directories.

The command must not import plugin packages unless a future gate proves that
specific import path is safe and in scope. Missing discovery tools produce
skipped/parked status, not pass. Discovery success is not validation success,
not issue closure, not bundled solver support, and not certification.

## Solver Execution Boundary

The command must not run arbitrary user project workloads. Any future solver
execution must be tiny, deterministic, documented, explicit, and bounded to
prepared-machine validation.

Execution must:

- require explicit operator acknowledgement;
- use only local installed tools;
- write local evidence under `.codex/reports/validation/`;
- avoid ProjectSchema mutation;
- avoid issue/release/tag/asset mutation;
- report failures without mutating GitHub state.

Execution success is not industrial certification, not production support, not
bundled solver support, and not issue closure.

## Manifest-State Validation Boundary

Prepared-machine validation must keep manifest-state review separate from
ProjectSchema state and release/issue state.

- Persistence records are local review state only.
- Summary audit output is local review state only.
- ProjectSchema boundary output is non-mutating review output.
- Prepared-machine validation does not mutate ProjectSchema.
- Prepared-machine validation does not create ProjectSchema evidence.
- Prepared-machine validation does not close issues.
- Prepared-machine validation does not mutate releases, tags, or assets.
- Prepared-machine validation does not certify solvers.

## Evidence Policy

Future evidence must be local, untracked by default, and written only under
`.codex/reports/validation/`.

Evidence must include:

- command line;
- timestamp;
- git SHA;
- environment summary;
- prerequisite table;
- planned checks;
- run results;
- skipped-missing entries;
- diagnostics;
- non-actions;
- limitations;
- evidence file paths.

Evidence is not a release asset, not ProjectSchema evidence, not certification
evidence, not bundled solver support evidence, and not issue closure evidence.

## Exit-Code Policy

Future command exit codes should be:

| Code | Meaning |
| --- | --- |
| 0 | Command completed and all required in-scope checks completed without required check failures. |
| 1 | Internal error. |
| 2 | Prerequisites missing / parked. |
| 3 | Validation checks failed. |
| 4 | Unsafe request or forbidden mutation attempt. |
| 5 | Ambiguous configuration. |

Exit code 0 is not certification, not issue closure, not release mutation, and
not bundled solver support. Exit code 0 must still distinguish
skipped-missing from pass when optional targets are outside the required
in-scope set.

## Output Policy

Future output must be deterministic in both text and JSON:

- text summary;
- JSON machine-readable result;
- prerequisite table;
- evidence paths;
- diagnostics;
- non-actions;
- limitations.

JSON keys should be stable, sorted where practical, and friendly to review
diffs. Text output should be concise and must not hide skipped-missing entries.

Output must redact:

- raw secrets;
- credential paths;
- tokens;
- API keys;
- full file content;
- plugin code;
- raw local paths unless a future gate explicitly permits a redacted display.

## ProjectSchema Boundary

The future command must perform no ProjectSchema mutation, no ProjectSchema
evidence creation, no ProjectSchema field addition, no ProjectSchema
migration, and no ProjectSchema import of persistence records.

Future ProjectSchema integration requires a separate design and implementation
gate. Prepared-machine validation evidence must remain outside ProjectSchema
unless a later gate defines a reviewed, non-ambiguous ProjectSchema evidence
contract.

## Issue/Release Boundary

The future command must perform no issue mutation, no issue closure, no release
mutation, no tag mutation, no asset upload, and no version bump.

Results may inform a later issue triage or release review gate only. They must
not automatically close issues #6 through #11, update GitHub Releases, move or
create tags, upload release assets, or alter package metadata.

## Certification Boundary

The future command must make no certification claim, no industrial solver
support claim, no bundled solver claim, and no production support claim.

Prepared-machine validation is local prepared-machine evidence only. It is not
an industrial accuracy, compliance, support, or safety-critical assurance
program.

## Relationship To Completed OSW-EXP Chain

OSW-EXP-124 through OSW-EXP-138 completed local optional solver plugin manifest
reload acceptance persistence, writer, CLI write, GUI write, summary audit, and
ProjectSchema boundary work.

Those gates provide review-record and boundary confidence. They are not
prepared-machine validation by themselves because they do not prove that Gmsh,
GNU Octave, CalculiX, OpenFOAM, CoolProp, Cantera, PyVista, meshio, VTK, or
other optional stacks are locally runnable on a prepared machine.

The future prepared-machine command must consume this history as context only.
It must not reinterpret persistence records, summary audit rows, or
ProjectSchema boundary rows as prepared-machine pass/fail evidence.

## Relationship To Open Issues

Issues #6 through #11 remain open. This command design does not mutate issues
and does not close issues.

Future completed validation may feed a separate review/triage gate. There is
no automatic issue closure, no release mutation, no asset upload, no tag
mutation, and no version bump.

## Security/Privacy Review

Future implementation must preserve a local-only security posture:

- no provider/OAuth/MCP network behavior;
- no credential scraping;
- no token display;
- no arbitrary directory scan;
- no network manifest fetch;
- no plugin import unless explicitly safe and future-gated;
- no unsafe shell or subprocess behavior beyond documented local checks;
- no raw secret, token, API key, credential path, full file content, or plugin
  code output.

Subprocess use, if later implemented for safe local checks, must use argument
lists, timeouts, bounded output capture, and deterministic diagnostics. It must
not use user-provided shell strings.

## Non-Actions

This design gate performs:

- no implementation;
- no command implementation;
- no source edits;
- no CLI source edits;
- no GUI source edits;
- no optional-solver source edits;
- no dependency installation;
- no dependency install;
- no solver installation;
- no solver execution;
- no live discovery;
- no live validation;
- no live optional validation;
- no validation run;
- no ProjectSchema mutation;
- no ProjectSchema evidence creation;
- no issue mutation;
- no release mutation;
- no tag mutation;
- no asset mutation;
- no version bump;
- no validation-pass claim;
- no validation-fail claim;
- no issue closure;
- no bundled solver support claim;
- no certification claim.

## Future Implementation Test Plan

Future `OSW-EXP-140` must test:

- command import and dispatch;
- `explain`, `preflight`, `plan`, `run`, `diagnostics`, `prerequisites`,
  `evidence`, and `safety` output;
- missing prerequisite classification;
- no dependency install calls;
- no solver install calls;
- no ProjectSchema mutation;
- no ProjectSchema evidence creation;
- no issue/release/tag/asset mutation;
- no certification claim;
- evidence path generation under `.codex/reports/validation/`;
- skipped-missing handling;
- JSON determinism;
- exit-code policy;
- forbidden mutation requests blocked;
- source scans for network/provider/OAuth/MCP behavior;
- source scans for credential scraping and token display;
- source scans for unsafe shell/subprocess behavior.

Implementation tests must remain network-free by default and must not require
heavy optional extras or external solver executables unless explicitly marked
as prepared-machine/installed-only validation tests.

## Future Gates

Suggested next gates:

- `OSW-EXP-140_OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` retry
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_RESULTS_REVIEW_AND_ISSUE_TRIAGE`, only
  if validation completes
- `OSW-EXP-141_OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_EVIDENCE_SCHEMA_DESIGN`,
  if a separate evidence schema is needed

Prepared-machine validation remains parked until OSW-EXP-140 or a
repo-consistent implementation gate creates the command and a prepared machine
has the required prerequisites.

## OSW-EXP-140 Implementation Follow-Up

OSW-EXP-140 implements the explicit local command described by this design in
[Optional solver prepared-machine validation command implementation](optional_solver_prepared_machine_validation_command_implementation.md).

The implementation keeps the command local-only and non-installing. It checks
executables with `shutil.which`, checks Python modules with
`importlib.util.find_spec`, writes no evidence by default, requires explicit
prepared-machine/local-only acknowledgements for `run`, and writes local
JSON/Markdown evidence only under a caller-supplied directory. It still runs no
solver execution, mutates no ProjectSchema state, mutates no issues/releases/
tags/assets, bumps no version, and makes no validation, issue-closure,
bundled-solver, or certification claim.
