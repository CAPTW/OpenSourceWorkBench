# Optional Solver Prepared-Machine Manifest-State Validation Prerequisites

## Status

Prepared-machine validation is currently parked. This document is docs-only
prerequisite evidence for
`OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`.

This gate performs no dependency installation, no solver installation, no
solver execution, no live discovery, no live optional validation, no
ProjectSchema mutation, no ProjectSchema evidence creation, no issue mutation,
no release mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

## Purpose

This document records why the latest prepared-machine manifest-state validation
gate is parked, which local prerequisites are missing, and what must exist
before a retry can produce prepared-machine evidence.

It also records that future prepared-machine validation must remain separate
from runtime reload acceptance, ProjectSchema mutation, ProjectSchema
validation evidence, issue closure, release mutation, asset mutation, tag
mutation, version changes, bundled-solver claims, and certification.

## Current Parked Result

Latest validation gate:
`OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`.

Status: `Parked`.

Starting SHA: `42d687626955a516f4072ad07b058e0f665fceaf`.

Local report path:
`.codex/reports/validation/OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION.md`.

Required focused regression checks passed at the OSW-EXP-138 tip, including the
ProjectSchema boundary, summary audit, CLI write, GUI write, writer,
persistence view-model, reload acceptance view-model, reload acceptance CLI,
reload acceptance panel, and state writer tests.

Required QA/static checks passed, including scope drift, architecture
boundaries, docs links, solver artifact guard, Ruff, and `git diff --check`.

The prepared-machine portion did not run. No current safe runnable
prepared-machine manifest-state validation command was found in the repository,
and the local machine was missing required optional solver/package
prerequisites.

## Missing Runnable Command

No current safe runnable prepared-machine manifest-state validation command was
discovered in `tools/` or repository validation docs. Existing validation docs
describe installed-only policy, prepared-machine requirements, and future
guidance, but not a current command for this gate to run.

A future command requires a separate design/implementation gate or a clear
documented operator command. Focused unit tests, GUI tests, and QA checks do not
prove that the machine is prepared and must not be interpreted as
prepared-machine validation success.

## Missing Local Prerequisites

| Prerequisite | Category | Current observed status | Purpose from repo docs/searches | Suggested non-mutating detection command | Owner/action | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `gmsh` executable | executable | missing | Gmsh meshing/live issue `#6` validation and optional mesh workflow checks | `where gmsh` | Operator preparation, not Codex install | Missing executable is `skipped-missing`, not success or failure. |
| Python `gmsh` | Python package | missing | Gmsh Python API/import path for optional mesh validation | `python -c "import gmsh"` | Operator preparation, not Codex install | Do not install from this gate. |
| `octave` | executable | missing | GNU Octave `.m` execution/live issue `#7` validation | `where octave`; `where octave-cli` | Operator preparation, not Codex install | `.m` workflows remain preview-first and must not run arbitrary user scripts. |
| `ccx` | executable | missing | CalculiX live issue `#8` validation | `where ccx` | Operator preparation, not Codex install | Solver execution requires a future explicit prepared-machine command. |
| OpenFOAM commands | solver stack | missing | OpenFOAM live issue `#9` validation with initialized shell environment | `where foamVersion`; `where blockMesh`; `where icoFoam`; `where simpleFoam`; `where foamRun` | Operator preparation, not Codex install | Full OpenFOAM UI/coverage remains out of scope. |
| Python `meshio` | Python package | missing | Mesh readback/round-trip and PyVista/meshio live issue `#11` validation | `python -c "import meshio"` | Operator preparation, not Codex install | Also supports Gmsh readback when available. |
| Python `pyvista` | Python package | missing | Optional visualization/mesh object validation for live issue `#11` | `python -c "import pyvista"` | Operator preparation, not Codex install | Headless rendering may still be skipped with diagnostics. |
| Python `vtk` | Python package | missing | PyVista support dependency for optional visualization validation | `python -c "import vtk"` | Operator preparation, not Codex install | Presence alone is not validation success. |
| Python `CoolProp` | Python package | missing | CoolProp property live issue `#10` validation | `python -c "import CoolProp"` | Operator preparation, not Codex install | Optional science backend remains user-installed. |
| Python `cantera` | Python package | missing | Cantera reactor/live chemistry validation for issue `#10` | `python -c "import cantera"` | Operator preparation, not Codex install | Optional science backend remains user-installed. |

## Non-Mutating Preflight Checklist

Before retrying prepared-machine validation, an operator may run local-only
preflight checks that install nothing and execute no solver workload:

- executable presence checks such as `where gmsh`, `where octave`,
  `where octave-cli`, `where ccx`, `where foamVersion`, `where blockMesh`,
  `where icoFoam`, `where simpleFoam`, and `where foamRun`;
- Python import checks such as `python -c "import gmsh"`,
  `python -c "import meshio"`, `python -c "import pyvista"`,
  `python -c "import vtk"`, `python -c "import CoolProp"`, and
  `python -c "import cantera"`;
- version checks where safe, local, and documented;
- environment path checks for an initialized OpenFOAM shell;
- confirmation that the validation gate will perform no network fetch and no
  dependency install.

These preflight checks are not prepared-machine validation by themselves. They
only establish whether a later explicit validation command might be runnable.

## Future Prepared-Machine Validation Command Requirements

A future prepared-machine validation command must:

- be explicit and documented;
- identify exact optional solver/package checks;
- run local-only;
- avoid network fetches unless a later gate explicitly documents a local-safe
  exception;
- not mutate ProjectSchema;
- not create ProjectSchema validation evidence unless a separate ProjectSchema
  gate authorizes it;
- not mutate issues, releases, tags, or assets;
- not bump versions;
- not claim certification;
- separate `skipped-missing` from success and from failure;
- produce local evidence under `.codex/reports/validation/`;
- report whether solver discovery occurred;
- report whether solver execution occurred;
- require explicit prepared-machine status before any live optional validation
  is claimed.

## Evidence Policy

Local evidence may be untracked under `.codex/reports/validation/`. Evidence
from this prerequisite documentation is not a release asset, not issue closure,
not certification, and not a bundled-solver claim.

Evidence is not ProjectSchema evidence unless a separate ProjectSchema gate
defines that meaning, its inputs, and its mutation/evidence boundaries.

## Boundary With Completed Persistence Chain

OSW-EXP-124 through OSW-EXP-138 completed local review, persistence, audit, and
ProjectSchema-boundary surfaces for optional solver plugin manifest reload
acceptance persistence.

That chain is not live optional validation and is not prepared-machine
validation. Persistence records remain non-authoritative local review records.
The summary audit remains non-authoritative and supplied-record-only. The
ProjectSchema boundary remains non-mutating and supplied-record-only.

## Issue And Release Boundary

Issues `#6` through `#11` remain open. This gate performs no issue mutation, no
release mutation, no tag mutation, no asset mutation, and no version bump.

This gate makes no validation-pass claim, no validation-fail claim, no issue
closure claim, no bundled-solver claim, and no certification claim.

## Retry Criteria

Before rerunning
`OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`:

- a safe command exists or the operator provides an exact documented command;
- required prerequisites are present;
- no dependency installation is needed during the validation gate;
- local environment details are documented;
- expected artifacts and evidence paths are known;
- non-actions are accepted, including no ProjectSchema mutation, no
  issue/release/tag/asset mutation, no version bump, no certification claim,
  and no issue closure.

## Future Gates

Suggested future gates:

- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION`, retry after
  machine preparation;
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_RESULTS_REVIEW_AND_ISSUE_TRIAGE`, only
  if validation completes;
- `OSW-EXP-139_OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND_DESIGN`, if
  the repository needs a dedicated runnable command;
- `OSW-EXP-140_OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND_IMPLEMENTATION`,
  if the command design is approved.

## Non-Actions

This documentation gate does not:

- install dependencies;
- install solvers;
- uninstall dependencies;
- uninstall solvers;
- run solver execution;
- run live discovery;
- run live optional validation;
- mutate ProjectSchema;
- create ProjectSchema evidence;
- mutate issues;
- mutate releases;
- mutate tags;
- mutate assets;
- bump versions;
- create GitHub Releases;
- upload release assets;
- close issues;
- claim prepared-machine validation success;
- claim validation success;
- claim validation failure;
- claim issue closure;
- claim bundled solver support;
- claim certification;
- implement a validation command;
- edit runtime source, CLI source, GUI source, optional-solver source, solver
  source, plugin discovery, or ProjectSchema source.
