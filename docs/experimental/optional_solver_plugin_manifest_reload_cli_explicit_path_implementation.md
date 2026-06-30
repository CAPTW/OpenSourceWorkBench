# Optional Solver Plugin Manifest Reload CLI Explicit Path Implementation

## 1. Status

Experimental reload CLI explicit-path preview is implemented.

The implemented command is:

```text
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file>
```

It is stdout-first, reader-first, review-only, and non-mutating. It adds no
default reload path, no background reload, no directory scan, no network fetch,
no plugin package import, no GUI file dialog, no runtime reload acceptance, no
ProjectSchema mutation, no discovery/validation/solver execution, no automatic
activation, no trust restoration, no issue/release/tag/asset mutation, no
version bump, and no validation-pass/fail, issue-closure, bundled-solver, or
certification claim.

## 2. Purpose

This gate connects the existing reload CLI review surface to the OSW-EXP-113
library-level reload file reader for one explicit caller-provided local
state-writer UX state file. The CLI renders reader diagnostics first. Only when
the reader returns a `safe_mapping` does the CLI route that mapping through the
OSW-EXP-107 reload view-model review surface.

The command previews reload state. It does not accept reload state as trusted
runtime state.

## 3. Public Command And Options

Implemented command shape:

```text
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file>
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --json
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --max-bytes <n>
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --allow-symlink
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --allow-migration
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --allow-unredacted-paths
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --allow-secret-like-values
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --reader-diagnostics-only
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --viewmodel-preview-only
```

The path-related options are accepted only for `load-preview`. Existing
deterministic in-memory commands and flags remain unchanged.

## 4. Path Policy

`--path` is explicit and caller-supplied. The CLI does not choose a path, keep a
recent path, inspect a project path, expand globs, recurse directories, fetch
URLs, scan plugin directories, or use a default reload path.

The path display uses the reader's redacted target display. Default text and JSON
output do not include raw absolute target paths.

## 5. Reader Invocation Behavior

The CLI calls `OptionalSolverPluginManifestReloadFileReader().read(...)` with an
`OptionalSolverPluginManifestReloadFileReadRequest`. The request carries the
explicit target path, the max-byte limit, explicit allow flags, and a CLI caller
context string.

The CLI does not duplicate reader JSON parsing, file eligibility checks,
redaction checks, schema checks, stale-source checks, conflict checks, unsafe
claim checks, or secret/path scanning. Those policies stay inside the reader.

## 6. Reader Diagnostics Output

Text output renders a reader section before any view-model section. JSON output
contains a separate `reader` object before the `viewmodel` object in the
top-level payload.

Reader output includes status, redacted target display, bytes read, payload hash,
payload kind/schema metadata, diagnostics, blockers, warnings, action states, and
non-action flags. Reader diagnostics remain review diagnostics; they are not
validation success and not validation failure.

## 7. Reader-Blocked Behavior

When the reader reports blockers or does not provide `safe_mapping`, the CLI:

- returns `2`;
- emits reader diagnostics;
- does not construct a reload view-model preview;
- does not synthesize a partial mapping;
- does not call the blocked state validation failure;
- does not mutate files or runtime state.

Blocked reader statuses cover missing files, directories, symlinks unless
explicitly allowed, oversized files, malformed JSON, non-object roots,
payload-kind mismatch, unsupported/migratable schema, unredacted paths,
secret-like values, unsafe claims, stale sources, and conflicts.

## 8. Reader-Success View-Model Preview

When the reader returns `ready_for_viewmodel` and a non-`None` `safe_mapping`, the
CLI builds an `OptionalSolverPluginManifestReloadViewModel` from that safe mapping
and the reader's redacted target display.

The view-model preview remains review-only. It renders summary/readiness,
source/provenance, schema/migration, candidates, acknowledgements, redaction,
stale-source/re-preview, conflict/shared-stack, unsafe claims, evidence/history,
diagnostics, disabled/future action states, and safety guidance.

## 9. Output Modes

Plain text is the default. `--json` emits deterministic JSON with separate
`reader` and `viewmodel` keys, `non_action_flags`, `state_source_policy`,
`reader_request_policy`, `cli_diagnostics`, and `exit_semantics`.

`--reader-diagnostics-only` renders the reader diagnostics and skips the
view-model section after reader success. `--viewmodel-preview-only` still renders
reader diagnostics first, then renders the view-model preview after reader
success; it does not bypass the reader.

## 10. Exit-Code Behavior

Exit codes are non-validating:

- `0`: command completed and rendered reader diagnostics, with view-model preview
  when requested and available;
- `1`: unexpected internal CLI boundary error;
- `2`: missing path/future-only behavior, invalid explicit-path option usage, or
  reader-blocked preview.

No exit code implies validation success, validation failure, issue closure,
release state, activation, trust restoration, or certification.

## 11. Schema And Migration Behavior

The CLI passes `--allow-migration` through the reader request, but migration
remains future-gated by the reader in this gate. A migratable or
migration-required payload blocks the safe mapping and returns reader diagnostics.

Schema review remains separate from ProjectSchema. The CLI creates no schema
files and performs no schema migration.

## 12. Redaction And Privacy Behavior

The CLI relies on the reader's redacted target display and diagnostics. Default
output blocks unredacted absolute paths and secret-like payload values through
the reader. Explicit allow flags are opt-in reader request policy flags, not
trust or validation overrides.

Hashes, fingerprints, trust labels, and source labels are not certification or
validation signals.

## 13. Candidate, Stale-Source, Conflict, Unsafe-Claim, And Evidence Behavior

Candidate lifecycle state remains preview state only. Persisted active or
reactivation states require future activation review. Stale sources require
re-preview when present. Conflicts remain visible and do not override built-ins.
Unsafe claims are blocked as data. Evidence/history is reference-only and not
fresh validation evidence.

Skipped-missing remains skipped-missing.

## 14. Relationships

- Reload file reader: the CLI is a thin caller of the OSW-EXP-113 reader and
  preserves reader diagnostics.
- Reload view-model: only reader `safe_mapping` enters the OSW-EXP-107
  view-model review path.
- Current reload CLI: existing in-memory commands remain stdout-first and
  review-only.
- Reload GUI: unchanged; no GUI source or file dialog behavior is added.
- State writer: this command previews state-writer UX state files but never
  rewrites, repairs, migrates, or deletes them.
- ProjectSchema: not imported, created, persisted, or mutated.
- Live optional validation issues: issues `#6` through `#11` remain open and
  separate from reload preview output.

## 15. Non-Actions

This gate does not add default reload paths, background reload, directory scans,
network fetches, plugin package imports, GUI file dialogs, runtime reload
acceptance, reloadable bundles, export files, report files, clipboard behavior,
report attachments, open-output-folder behavior, ProjectSchema mutation, live
discovery, passive refresh, validation execution, solver execution, dependency
installation, dependency uninstall, solver uninstall, automatic activation, trust
restoration, issue mutation, release mutation, tag mutation, asset mutation,
version bump, validation-pass claim, validation-fail claim, issue-closure claim,
bundled-solver claim, or certification claim.

## 16. Testing Strategy

`tests/unit/test_optional_solver_plugin_manifest_reload_cli_explicit_path.py`
covers valid explicit paths, text and JSON output, no unsafe success/failure
claims, missing path behavior, reader blockers, warning-only diagnostics,
reader-diagnostics-only and view-model-preview-only output, max-byte policy,
conservative path/secret defaults, explicit allow flags, symlink policy when the
platform supports symlinks, migration remaining future-gated, option rejection
outside `load-preview`, no output file creation, and source guardrails against
directory scans, network fetches, GUI imports, ProjectSchema imports, plugin
discovery, solver execution, subprocess use, and file writes.

Adjacent tests cover the existing reload CLI, reload file reader, reload
view-model, CLI explicit-path design docs, state writer, docs links, scope drift,
architecture boundaries, solver-artifact hygiene, Ruff, and diff whitespace.

## 17. Future Gates

Future GUI file-dialog design and implementation remain separate. Runtime reload
acceptance, activation review, discovery refresh, ProjectSchema integration,
validation, issue/release workflows, export/report integration, and certification
remain future-gated.
