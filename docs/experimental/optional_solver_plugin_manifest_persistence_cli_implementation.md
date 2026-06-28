# Optional Solver Plugin Manifest Persistence CLI Implementation

## 1. Status

Experimental persistence/state-writer CLI is implemented for review, dry-run,
and explicit local state writes. It is dry-run/review-first. Actual write
requires an explicit caller-supplied target path, explicit write mode, explicit
caller acknowledgement, and successful state-writer preflight.

The CLI has no default path, no GUI behavior, no reload behavior, no
ProjectSchema mutation, no discovery execution, no validation execution, no
dependency install/uninstall, no solver execution, and no issue, release, tag,
or asset mutation.

## 2. Purpose

The CLI provides command-line review, dry-run, and explicit write access to the
existing OSW-EXP-102 state-writer library. It is a thin wrapper over the
OSW-EXP-101 state-writer view-model and the OSW-EXP-102 writer preflight/write
API.

## 3. Public command names

The repository uses a flat CLI command namespace. This gate adds:

```text
python -m osw.cli optional-solver-plugin-manifest-persistence explain
python -m osw.cli optional-solver-plugin-manifest-persistence plan
python -m osw.cli optional-solver-plugin-manifest-persistence schema
python -m osw.cli optional-solver-plugin-manifest-persistence acknowledgements
python -m osw.cli optional-solver-plugin-manifest-persistence diagnostics
python -m osw.cli optional-solver-plugin-manifest-persistence actions
python -m osw.cli optional-solver-plugin-manifest-persistence write --sample-state --output <path>
python -m osw.cli optional-solver-plugin-manifest-persistence write --sample-state --output <path> --write --acknowledge-state-write
```

Supported state-source flags are `--sample-state`, `--empty-state`, and
`--unavailable-state`. Supported output formats are `--format text` and
`--format json`.

## 4. State source policy

This gate uses deterministic in-memory state only:

- `--sample-state` builds a deterministic ready in-memory sample view-model.
- `--empty-state` builds a deterministic empty/unavailable in-memory state.
- `--unavailable-state` is the default and documents that live source
  integration remains future-gated.

The CLI does not scan plugin folders, import plugin packages, fetch network
manifests, run passive discovery, run validation, execute solvers, reload
existing state files as authority, or infer a default state source.

## 5. Dry-run behavior

`write` defaults to dry-run. Dry-run calls the state-writer library with
`dry_run=True`, prints deterministic writer diagnostics such as
`OSPMG_STATE_WRITER_WRITE_PLANNED`, reports the redacted target display, and
does not write a file.

## 6. Actual write behavior

Actual write is available only through:

```text
--write --acknowledge-state-write --output <path>
```

The CLI passes the request to `OptionalSolverPluginManifestStateWriter`; it does
not reimplement file writing or bypass writer preflight. Successful actual
writes surface `OSPMG_STATE_WRITER_WRITE_COMPLETED`.

## 7. Target path and acknowledgement policy

The target path is caller-supplied only. There is no default target path and no
parent directory creation. Existing targets are refused unless
`--allow-replace` is present. Directory targets and symlink targets are blocked
by writer preflight. Actual writes require `--acknowledge-state-write`.

## 8. Output modes

Text output is stable, line-oriented, and review-focused. JSON output is
deterministic, sorted, and includes the command, selected subcommand, state
source policy, redacted target display, view-model mapping, writer result
mapping, non-actions, and future-gate flags.

JSON output is not a reloadable bundle, not ProjectSchema state, not validation
evidence, and not a report/export artifact.

## 9. Diagnostics

The CLI surfaces state-writer view-model diagnostics and writer diagnostics,
including:

- `OSPMG_STATE_WRITER_WRITE_PLANNED`
- `OSPMG_STATE_WRITER_WRITE_COMPLETED`
- `OSPMG_STATE_WRITER_WRITE_BLOCKED` or a blocked writer status for blocked
  writes
- path, acknowledgement, schema, readiness, redaction, stale-source, conflict,
  unsafe-claim, non-action, future-gate, and safety diagnostics

Diagnostics are not validation-pass or validation-fail evidence.

## 10. Redaction/privacy behavior

Output displays target basenames only and marks target paths as redacted when a
target is supplied. It does not print raw absolute paths by default. The
underlying writer still blocks unredacted-path and secret-like payload blockers.

## 11. Schema/migration behavior

The CLI displays the view-model schema version and the writer payload schema
version. Actual writes pass the expected writer payload schema version to the
state-writer library. Missing, unsupported, or migration-required schema state
remains a writer/view-model blocker.

## 12. Acknowledgement behavior

The acknowledgement output lists required acknowledgement categories and expiry
rules. Persisted acknowledgements may expire on reload, source fingerprint
change, schema change, unsafe claim change, or trust policy change. Actual
writes also require the caller-level `--acknowledge-state-write` flag.

## 13. Stale-source/re-preview behavior

Stale-source/re-preview rows remain visible. Stale supplied state is blocked by
the view-model/writer readiness path. The CLI does not silently trust old source
state and does not reload a written file.

## 14. Conflict/shared-stack behavior

Conflict/shared-stack rows remain visible. Built-ins remain authoritative by
default. Shared-stack warnings or conflicts remain review blockers when the
view-model marks them that way.

## 15. Unsafe-claim behavior

Unsafe claims remain visible and blocked. Persisted state is not validation
evidence, not issue-closure evidence, and not certification.

## 16. Evidence/history retention behavior

Evidence references and deactivation/reactivation history remain retained as
references when supplied. The CLI does not rewrite evidence into validation
truth and does not erase history.

## 17. Trust/provenance boundary

User/plugin manifests remain untrusted by default. Persisted state is not trust
restoration, not automatic activation, and not dependency installation. A trust
label is not certification.

## 18. Non-actions

This gate adds no GUI behavior, reload behavior, ProjectSchema mutation, live
discovery, passive refresh, plugin package import, directory scan, network
fetch, validation execution, solver execution, dependency installation,
dependency uninstall, solver uninstall, issue mutation, release mutation, tag
mutation, asset mutation, version bump, default write path, background write,
report creation, export creation, clipboard behavior, report attachment,
open-output-folder behavior, validation-pass claim, validation-fail claim,
issue-closure claim, bundled-solver claim, or certification claim.

## 19. Testing strategy

Focused unit tests cover import safety, no GUI/Qt imports, no discovery or
release tooling imports, explain/review commands, dry-run writes, blocked
writes, acknowledgement gating, unavailable-state blockers, missing-parent
blockers, directory/symlink blockers, existing-target replacement policy,
deterministic JSON writes under `tmp_path`, and non-action output flags.

Actual write tests use pytest `tmp_path` only.

## 20. Relationship to OSW-EXP-102 state writer

The CLI uses the OSW-EXP-102 state-writer library for preflight and writing. It
does not choose default paths, create parents, bypass acknowledgements, bypass
readiness checks, or implement file writing independently.

## 21. Relationship to OSW-EXP-101 state-writer view-model

The CLI consumes deterministic OSW-EXP-101 view-model records and surfaces their
summary, schema, acknowledgement, diagnostic, redaction/privacy, stale-source,
conflict, unsafe-claim, evidence/history, non-action flag, and disabled/future
action-state data.

## 22. Relationship to OSW-EXP-096 persistence CLI design

OSW-EXP-096 remains the historical design-only contract. OSW-EXP-103 implements
the bounded CLI slice described by that design while preserving the same
dry-run/review/explain, non-validating, non-reloading, non-mutating, and
issue/release-safe boundaries.

## 23. Relationship to adjacent systems

The CLI does not add GUI controls, file dialogs, save dialogs, clipboard
actions, report actions, open-output-folder actions, ProjectSchema mutation,
export summaries, report generation, reload behavior, live discovery
integration, live validation, issue mutation, release mutation, tag mutation, or
asset mutation.

Live optional validation issues `#6` through `#11` remain open. Package metadata
remains `0.1.5rc1`. The public prerelease remains `v0.1.5-rc1`.

## 24. Future gates

Separate future gates remain required for live state source integration, GUI
writer controls, reload behavior, ProjectSchema integration, report/export CLI,
export-summary CLI, discovery integration, validation, install/uninstall,
solver execution, issue closure, release/tag/asset mutation, trust elevation,
and certification claims.
