# Optional Solver Plugin Manifest Reload CLI Implementation

## 1. Status

Experimental reload CLI review is implemented.

The implemented command is stdout-first and review-only. It adds no persisted
state file reader, no file parser, no runtime reload, no default reload path, no
background reload, no ProjectSchema mutation, no GUI behavior, no discovery,
no validation, no solver execution, no automatic activation, no trust
restoration, no issue/release/tag/asset mutation, and no certification claim.

## 2. Purpose

The CLI gives maintainers and tests a headless way to inspect the existing
OSW-EXP-107 reload view-model. It renders deterministic sample, empty, or
unavailable in-memory state and exposes the same review boundaries as the GUI
panel without adding file loading or reload acceptance behavior.

## 3. Public Command Names

The registered command family is:

```text
python -m osw.cli optional-solver-plugin-manifest-reload explain
python -m osw.cli optional-solver-plugin-manifest-reload preview
python -m osw.cli optional-solver-plugin-manifest-reload schema
python -m osw.cli optional-solver-plugin-manifest-reload sources
python -m osw.cli optional-solver-plugin-manifest-reload candidates
python -m osw.cli optional-solver-plugin-manifest-reload acknowledgements
python -m osw.cli optional-solver-plugin-manifest-reload diagnostics
python -m osw.cli optional-solver-plugin-manifest-reload redaction
python -m osw.cli optional-solver-plugin-manifest-reload stale-sources
python -m osw.cli optional-solver-plugin-manifest-reload conflicts
python -m osw.cli optional-solver-plugin-manifest-reload unsafe-claims
python -m osw.cli optional-solver-plugin-manifest-reload evidence
python -m osw.cli optional-solver-plugin-manifest-reload actions
python -m osw.cli optional-solver-plugin-manifest-reload load-preview
```

Supported state/output flags are `--sample-state`, `--empty-state`,
`--unavailable-state`, and `--json`.

## 4. State Source Policy

State is deterministic and in-memory only. `--sample-state` uses the reload
view-model's stable sample. `--empty-state` uses deterministic empty/no-payload
state. `--unavailable-state` is explicit unavailable state and is also the
default when no state flag is supplied.

The CLI accepts no path argument. It does not read state files, parse JSON files
from disk, choose a default reload path, inspect plugin directories, import
plugin packages, fetch network manifests, refresh discovery, validate solvers,
or execute solvers.

## 5. Output Modes

Plain text is the default. `--json` emits deterministic JSON to stdout for
review commands. JSON includes the full view-model mapping, selected section
payload, CLI diagnostics, model diagnostics, acknowledgement requirements,
acknowledgement expiry reasons, and non-action boundaries.

Output remains stdout review data only. It is not a reloadable bundle, export
file, report file, ProjectSchema state, validation evidence, issue closure
evidence, release evidence, or certification evidence.

## 6. Command Behavior

All review subcommands return `0` when the command completed. Completion means
the review text or JSON was rendered; it does not mean validation passed,
validation failed, trust was restored, a candidate was activated, or a reload
was accepted.

`load-preview` is registered to reserve the future vocabulary but is disabled
in this gate. It returns `2`, emits future-gate diagnostics, reads no files,
parses no files, and explicitly says the non-zero exit is not validation
failure.

## 7. Summary/readiness output

`preview` renders reload state, readiness, payload kind, schema version, source
count, candidate count, acknowledgement count, diagnostic count, blocker count,
warning count, redaction rows, stale sources, conflicts, unsafe claims, evidence
rows, and stable view-model text lines.

The output keeps honesty flags visible: reload review is not validation
evidence, not validation failure, not trust restoration, not automatic
activation, not discovery execution, not plugin import, not validation
execution, not solver execution, not ProjectSchema mutation, not issue closure,
not release mutation, and not certification.

## 8. Source/provenance output

`sources` renders source id, source type, trust label, redacted display,
provenance label, and built-in authority state. User/plugin manifests remain
untrusted by default. Built-ins are authoritative by default. Trust labels and
fingerprints are not certification or validation signals.

## 9. Schema/migration output

`schema` renders payload kind, payload schema version, supported schema state,
migration-required state, and blocker state. Schema mismatch is not validation
failure. Reload schema review is separate from ProjectSchema.

Schema migration remains future-gated and is not performed by this CLI.

## 10. Candidate lifecycle output

`candidates` renders candidate id, display name, lifecycle state, reload review
state, future activation review flag, future discovery refresh flag, automatic
activation denial, trust restoration denial, and skipped-missing preservation.

Candidate rows are review records only. They do not activate candidates and do
not restore trust.

## 11. Acknowledgement/expiry output

`acknowledgements` renders all `RELOAD_REQUIRED_ACKS` and expiry reasons:
reload, source fingerprint change, schema version change, unsafe claim
appearance, trust policy change, and future discovery-refresh result.

Satisfied acknowledgements are still review state only. They do not validate,
reload, trust, activate, close issues, mutate releases, or certify anything.

## 12. Redaction/privacy output

`redaction` renders redaction-required state, review-required state, raw path
hiding, unredacted path blockers, and secret-like content blockers. Raw absolute
paths are hidden by default, and fingerprints are not trust signals.

Redaction review precedes any future activation review.

## 13. Stale-source/re-preview output

`stale-sources` renders stale source state, re-preview requirements, old preview
trust boundaries, and the no-source-file-IO boundary.

Stale state is not validation failure and does not trigger background reload.

## 14. Conflict/shared-stack output

`conflicts` renders visible conflict rows, shared-stack warnings, built-ins-win
policy, and blocker state. Reload review does not resolve conflicts or override
built-ins.

## 15. Unsafe-claim output

`unsafe-claims` renders unsafe claims as visible and blocked. Unsafe claims are
not reloaded as truth and include validation success/failure, issue closure,
release mutation, bundled solver, solver execution, and certification claims.

## 16. Evidence/history output

`evidence` renders deactivation history, reactivation history, historical
evidence reference state, skipped-missing preservation, and issue-closure
denial.

History is retained for review only. It is not new validation evidence.

## 17. Diagnostics output

`diagnostics` renders `OSPMG_RELOAD_CLI_*` diagnostics and preserves
`OSPMG_RELOAD_*` model diagnostics. Diagnostics are review state and do not
represent validation success or validation failure.

## 18. Action-state output

`actions` renders all disabled/future-only action states, including read reload
file, parse reload file, runtime reload, trust restore, automatic activation,
reloadable bundle creation, export file creation, report file creation,
clipboard behavior, report attachment, open-output-folder behavior, discovery,
validation, solver execution, issue closure, release mutation, validation
claims, and certification claims.

## 19. Exit-code behavior

Review commands return `0` when output rendering completes. That is command
completion only.

`load-preview` returns `2` because file reader/parser behavior is disabled and
future-gated. This is not validation failure, not validation success, and not a
reload attempt.

## 20. Safety guidance

The CLI repeats non-action boundaries in text and JSON output: no file reader,
no file parser, no persisted state file reading/parsing, no runtime reload, no
default reload path, no background reload, no ProjectSchema mutation, no GUI
behavior, no live discovery, no passive refresh, no plugin package import, no
directory scan, no network fetch, no validation, no solver execution, no
dependency install/uninstall, no solver uninstall, no issue/release/tag/asset
mutation, no version bump, no validation-pass/fail claim, no bundled-solver
claim, and no certification claim.

## 21. Relationship to reload view-model

The CLI is a thin renderer over
[optional_solver_plugin_manifest_reload_viewmodel.md](optional_solver_plugin_manifest_reload_viewmodel.md).
It uses `OptionalSolverPluginManifestReloadViewModel.sample_ready_for_review()`,
`empty()`, and `unavailable()` and does not mutate the view-model source.

## 22. Relationship to reload GUI

The CLI mirrors the same review-only concepts as the reload GUI panel but adds
no GUI source and no GUI behavior. The GUI remains a read-only panel over
already-built records, while the CLI is a headless stdout renderer.

## 23. Relationship to persistence CLI/state writer

The persistence CLI/state writer can create local UX state through explicit
caller-supplied paths and acknowledgements. This reload CLI does not consume
those files from disk in this gate. It only renders deterministic in-memory
reload view-model state.

Any future persisted-state file reader/parser must be a separate gate.

## 24. Relationship to export-summary CLI/GUI

Export-summary CLI/GUI surfaces remain separate review/export-summary workflows.
This reload CLI creates no export summary, no export file, no report file, and
no reloadable bundle.

## 25. Relationship to ProjectSchema

The CLI does not import, create, persist, or mutate ProjectSchema. Reload
schema review remains separate from ProjectSchema state and ProjectSchema
integration remains future-gated.

## 26. Relationship to live optional validation issues

Issues `#6` through `#11` remain live optional validation issues. Reload CLI
output is not validation-pass evidence, not validation-fail evidence, not
issue-closure evidence, and not certification.

## 27. Non-actions

This gate does not implement file reader/parser behavior, persisted state file
reading/parsing, runtime reload, reload acceptance, default paths, background
reload, reloadable bundles, export files, report files, clipboard behavior,
report attachment, open-output-folder behavior, GUI behavior, ProjectSchema
mutation, live discovery, passive refresh, plugin package import, directory
scan, network fetch, validation, solver execution, dependency installation,
dependency uninstall, solver uninstall, automatic activation, trust
restoration, issue mutation, release mutation, tag mutation, asset mutation,
version bump, validation claims, issue-closure claims, bundled-solver claims,
or certification claims.

## 28. Testing strategy

Focused tests cover command registration, import without GUI extras, forbidden
integration imports, no file reader/parser source calls, default unavailable
state, sample state text output, section commands, JSON determinism, selected
JSON section payloads, disabled `load-preview`, no file creation, exclusive
state flags, and all safety boundaries.

Adjacent tests cover the reload view-model, reload CLI design docs, reload GUI
design docs, reload design docs, persistence CLI, export-summary CLI, scope
drift, architecture boundaries, docs links, solver artifact hygiene, Ruff, and
diff whitespace.

## 29. Future gates

Future gates may design and implement a real file reader/parser, schema
migration, runtime reload acceptance, activation review, discovery refresh,
ProjectSchema integration, export/report integration, live optional validation,
or issue/release workflows. Each must preserve explicit path policy,
redaction, acknowledgements, tests, and non-overclaiming boundaries.

## Follow-up: reload file reader (OSW-EXP-113)

OSW-EXP-113 implements a library-level explicit-path reload file reader
([optional_solver_plugin_manifest_reload_file_reader_implementation.md](optional_solver_plugin_manifest_reload_file_reader_implementation.md)).
It is **not** wired into this CLI: `load-preview`/`read-file` remain
disabled/future-only until a separate CLI explicit-path gate (OSW-EXP-114/115).
Reader status never implies a validation pass/fail exit.
