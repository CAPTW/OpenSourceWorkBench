# Optional Solver Plugin Manifest Reload CLI Explicit Path Design

## 1. Status

Design-only.

This gate adds no CLI explicit-path implementation, no CLI source edits, no
runtime source edits, no file-reader source edits, no GUI source edits, no path
argument implementation, no runtime behavior, no runtime file reading, no runtime
state parsing, and no runtime reload acceptance.

This gate also adds no default reload path, no background reload, no directory
scan, no network fetch, no plugin package import, no GUI file dialog, no
reloadable bundle creation, no export file creation, no report file creation, no
clipboard behavior, no report attachment, no open-output-folder behavior, no
ProjectSchema mutation, no live discovery, no passive refresh, no validation
execution, no solver execution, no dependency installation, no dependency
uninstall, no solver uninstall, no automatic activation, no trust restoration,
no issue mutation, no release mutation, no tag mutation, no asset mutation, no
version bump, no validation-pass claim, no validation-fail claim, no
issue-closure claim, no bundled-solver claim, and no certification claim.

## 2. Purpose

This document defines future CLI explicit-path semantics for reload preview.

The future implementation may connect the existing stdout-first reload CLI review
surface in
[optional_solver_plugin_manifest_reload_cli_implementation.md](optional_solver_plugin_manifest_reload_cli_implementation.md)
to the existing library-level reload file reader in
[optional_solver_plugin_manifest_reload_file_reader_implementation.md](optional_solver_plugin_manifest_reload_file_reader_implementation.md),
then route a reader-provided safe mapping into the OSW-EXP-107 reload
view-model review path documented in
[optional_solver_plugin_manifest_reload_viewmodel.md](optional_solver_plugin_manifest_reload_viewmodel.md).

This design preserves reload view-model, reader, GUI, ProjectSchema, discovery,
validation, issue/release, and certification boundaries. It is not
implementation authorization.

## 3. Current State Before CLI Explicit Path

- The OSW-EXP-102 state writer exists and writes bounded local UX state files
  only through explicit caller paths.
- The OSW-EXP-106 reload design exists.
- The OSW-EXP-107 reload view-model exists and consumes caller-supplied
  in-memory mappings only.
- The OSW-EXP-111 reload CLI review exists but uses deterministic in-memory
  states; `load-preview` is disabled/future-only.
- The OSW-EXP-113 reload file reader exists as a library-level explicit-path
  reader with diagnostics and safe mappings.
- The OSW-EXP-109 reload GUI review panel exists and consumes already-built
  reload view-model records.
- No CLI explicit-path wiring exists.
- No GUI file dialog exists.
- No runtime reload acceptance exists.
- No default reload path exists.

## 4. Definition Of CLI Explicit-Path Reload Preview

Definition of CLI explicit-path reload preview: a future user/caller-specified
local path passed to a CLI option that invokes the library reader, renders reader
diagnostics, and only if reader success produces a safe mapping, renders reload
view-model review over that safe mapping.

The future CLI explicit-path reload preview may eventually:

- accept `--path <file>` or a repo-consistent equivalent;
- accept `--max-bytes <n>`;
- accept `--allow-symlink`;
- accept `--allow-migration`;
- accept `--allow-unredacted-paths`;
- accept `--allow-secret-like-values`;
- call the OSW-EXP-113 reader;
- render a reader report;
- render the reader safe mapping through the OSW-EXP-107 reload view-model;
- render text or JSON output to stdout;
- return non-validation exit codes.

The future CLI explicit-path reload preview must not:

- choose a path;
- use a default path;
- scan directories;
- fetch URLs;
- import plugin packages;
- accept reload as trusted;
- activate candidates;
- restore trust;
- run discovery, validation, or solver execution;
- mutate ProjectSchema;
- close issues;
- mutate releases, tags, or assets;
- claim certification.

## 5. Non-Meaning Of CLI Explicit-Path Preview

CLI explicit-path preview is not validation success.
CLI explicit-path preview is not validation failure.
CLI explicit-path preview is not trust restoration.
CLI explicit-path preview is not automatic activation.
CLI explicit-path preview is not discovery success.
CLI explicit-path preview is not dependency installation.
CLI explicit-path preview is not solver execution.
CLI explicit-path preview is not ProjectSchema mutation.
CLI explicit-path preview is not issue closure.
CLI explicit-path preview is not release mutation.
CLI explicit-path preview is not certification.
CLI explicit-path preview is not report generation.
CLI explicit-path preview is not reloadable bundle acceptance.

Reader success means only that a bounded local UX state file produced a safe
review mapping. It does not make a user/plugin manifest trusted, active,
validated, failed, installed, discovered, or certified.

## 6. Future Command And Option Vocabulary

Reserved future command shapes:

```text
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file>
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --json
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --reader-diagnostics-only
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --viewmodel-preview-only
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --max-bytes <n>
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --allow-symlink
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --allow-migration
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --allow-unredacted-paths
python -m osw.cli optional-solver-plugin-manifest-reload load-preview --path <state-file> --allow-secret-like-values
```

This vocabulary is design-only. This gate adds no command parser branch, no
argument registration, no command handler, no call to the reader, and no runtime
file reading.

`--reader-diagnostics-only` would render the reader report without feeding a
safe mapping into the view-model. `--viewmodel-preview-only` would suppress
reader-detail sections after a ready reader result and render only the
view-model-derived review. Both options remain future-gated.

## 7. Future User Flow

Future user flow:

1. User explicitly supplies `load-preview --path <state-file>`.
2. CLI performs argument-level checks without guessing any path.
3. CLI must call the library reader with explicit policy options.
4. CLI renders reader diagnostics for every result.
5. If the reader returns blockers, CLI stops at reader diagnostics and does not
   build a view-model.
6. If the reader returns `safe_mapping`, CLI builds a reload view-model using
   the safe mapping and a redacted source label.
7. CLI renders summary, schema, candidates, acknowledgements, redaction, stale
   source, conflict, unsafe-claim, evidence/history, diagnostics, and actions.
8. CLI exits with a non-validation code.

User flow states should stay aligned with the reload view-model vocabulary:

- `target_not_selected`
- `target_missing`
- `source_reference_redacted`
- `schema_review`
- `schema_unsupported`
- `schema_migration_required`
- `payload_kind_mismatch`
- `redaction_review_required`
- `acknowledgement_review_required`
- `stale_source_repreview_required`
- `conflict_review_required`
- `unsafe_claim_blocked`
- `history_evidence_review`
- `reload_preview_ready`
- `reload_blocked`
- `reload_error`
- `future_activation_review_required`
- `future_discovery_refresh_required`

These states describe review readiness only. They do not authorize reload
acceptance, ProjectSchema mutation, activation, discovery refresh, validation,
solver execution, issue mutation, or release mutation.

## 8. Path Option Policy

The future CLI may accept exactly one explicit local state file path from the
caller through `--path <state-file>`.

Path option policy:

- no default reload path;
- no implicit current-project path;
- no saved recent-path fallback;
- no environment-variable expansion without a separate policy;
- no glob expansion;
- no directory recursion;
- no background reload;
- no network URL fetch;
- no plugin directory scan;
- no ProjectSchema path mutation;
- path display redacted to basename/hash/source id unless unredacted display is
  explicitly allowed by future policy.

Missing, blank, directory, symlink-blocked, oversized, empty, malformed, and
unsafe paths are diagnostics, not hidden success. A path option does not make a
state file trusted.

## 9. Reader Invocation Policy

Future CLI implementation may call:

```text
read_optional_solver_plugin_manifest_reload_file(
    target_path=<explicit caller path>,
    max_bytes=<policy value>,
    allow_symlink=<future explicit flag>,
    allow_migration=<future explicit flag>,
    allow_unredacted_paths=<future explicit flag>,
    allow_secret_like_values=<future explicit flag>,
)
```

Reader invocation policy:

- call only the OSW-EXP-113 library reader;
- pass exactly the caller-supplied path;
- preserve reader defaults unless the caller explicitly opts into a policy
  override;
- treat every reader status as review state;
- render reader diagnostics before any view-model output;
- build reload view-model output only from `safe_mapping`;
- never mutate reader results or view-model records;
- never treat `ready_for_viewmodel` as validation success, trust restoration,
  automatic activation, or reload acceptance.

The CLI must not bypass the reader by using ad hoc JSON loading, direct file
open calls, alternate parsers, directory scans, plugin imports, or ProjectSchema
loaders.

## 10. Output Modes

Future output modes:

- stable plain text;
- deterministic JSON to stdout;
- reader-diagnostics-only output;
- viewmodel-preview-only output;
- section-filtered text or JSON consistent with the current reload CLI;
- diagnostics output with redacted context;
- action-state output.

Output modes exclude file output, export file output, report output, reloadable
bundle output, clipboard output, report attachment output, open-output-folder
behavior, validation evidence output, issue-closure evidence output, release
evidence output, and certification output.

JSON remains stdout-only unless a separate writer/export/report gate changes
that boundary.

## 11. Reader Diagnostics Output

Reader diagnostics output should show:

- reader status;
- redacted target display;
- payload kind;
- payload schema version;
- reader version;
- bytes read;
- payload hash display when available;
- blocker count;
- warning count;
- diagnostic count;
- ready-for-viewmodel flag;
- each `OSPMG_RELOAD_READER_*` code with severity, blocker state, redacted
  related context, and suggested fix.

Reader diagnostics are review diagnostics only. They are not validation success
and not validation failure.

Representative reader diagnostics include:

- `OSPMG_RELOAD_READER_FILE_MISSING`
- `OSPMG_RELOAD_READER_NOT_REGULAR_FILE`
- `OSPMG_RELOAD_READER_SYMLINK_BLOCKED`
- `OSPMG_RELOAD_READER_FILE_TOO_LARGE`
- `OSPMG_RELOAD_READER_EMPTY_FILE`
- `OSPMG_RELOAD_READER_ENCODING_ERROR`
- `OSPMG_RELOAD_READER_JSON_PARSE_ERROR`
- `OSPMG_RELOAD_READER_ROOT_NOT_OBJECT`
- `OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED`
- `OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH`
- `OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED`
- `OSPMG_RELOAD_READER_MIGRATION_REQUIRED`
- `OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED`
- `OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED`
- `OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED`
- `OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED`
- `OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED`
- `OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY`
- `OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY`
- `OSPMG_RELOAD_READER_REVIEW_ONLY`
- `OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL`
- `OSPMG_RELOAD_READER_READ_COMPLETED`

## 12. Reload View-Model Output After Reader Success

Reload view-model output after reader success is allowed only when the reader
returns a non-`None` `safe_mapping`.

The future CLI may call
`OptionalSolverPluginManifestReloadViewModel.from_payload_mapping(...)` or the
repo-consistent helper over that `safe_mapping`, then render the existing
view-model sections. The source label passed to the view-model should be the
reader's redacted target display, not a raw absolute path.

If no safe mapping exists, the CLI must not synthesize one, must not partially
load payload fragments, and must not treat the reader blocker as a validation
failure.

## 13. Schema/Migration Output

Schema/migration output should show:

- required payload kind;
- actual payload kind;
- expected payload schema version;
- actual payload schema version;
- writer version;
- migration-required state;
- migration-allowed policy flag;
- unsupported schema blockers;
- ProjectSchema separation.

Schema mismatch is not validation failure. Migration is future-gated. The
persistence schema model remains separate from ProjectSchema. This design gate
creates no schema file and performs no migration.

## 14. Redaction/Privacy Output

Redaction/privacy output should state:

- raw absolute paths are hidden by default;
- target display is redacted;
- unredacted path blockers are visible;
- secret-like value blockers are visible;
- `--allow-unredacted-paths` and `--allow-secret-like-values` are future
  explicit overrides, not defaults;
- fingerprints and hashes are not trust signals;
- redaction review happens before any future activation review.

Diagnostics must not leak raw home directories, environment variables, tokens,
API keys, credentials, private keys, private network paths, solver install
paths, or plugin install paths.

## 15. Acknowledgement/Expiry Output

Acknowledgement/expiry output should include:

- `reload_not_validation`
- `reload_not_trust_restoration`
- `reload_not_automatic_activation`
- `reload_not_discovery_success`
- `reload_not_dependency_install`
- `reload_no_solver_execution`
- `reload_not_issue_closure`
- `reload_not_release_mutation`
- `reload_not_certification`
- `redaction_reviewed`
- `unredacted_paths_blocked`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `activation_review_required_after_reload`
- `no_discovery_execution`
- `no_plugin_package_import`
- `no_validation_execution`
- `no_solver_execution`
- `trust_label_not_certification`
- `persisted_acknowledgements_may_expire`

Expiry reasons include reload, source fingerprint change, schema version change,
unsafe claim appearance, trust policy change, future discovery-refresh result,
and file-reader policy change.

Satisfied or persisted acknowledgements do not validate, reload, trust,
activate, close issues, mutate releases, or certify anything.

## 16. Candidate Lifecycle Output

Candidate lifecycle output should show persisted lifecycle state and reload
review state:

- inactive preview remains review-only;
- persisted active requires future activation review;
- deactivated remains deactivated review state;
- reactivation routes to future activation review;
- discovery-refresh state remains review state;
- skipped-missing remains skipped-missing when represented.

The future CLI explicit-path preview provides no automatic activation and no
trust restoration.

## 17. Stale-Source/Re-Preview Output

Stale-source/re-preview output should show that old preview data is not silently
trusted. Missing, moved, changed, or stale sources require re-preview when that
state is present in the payload.

The future CLI explicit-path path is a path to the persisted UX state file only.
It must not inspect referenced plugin/source paths, repair stale sources, run
passive refresh, run discovery, or turn stale-source state into validation
failure.

## 18. Conflict/Shared-Stack Output

Conflict/shared-stack output should keep conflicts visible:

- built-ins win by default;
- persisted state does not override built-ins;
- shared-stack warnings are visible;
- conflict review remains blocked or warning-only according to the view-model
  and reader diagnostics;
- conflict resolution requires a separate future policy gate.

The CLI does not resolve conflicts and does not elevate user/plugin manifests.

## 19. Unsafe-Claim Output

Unsafe-claim output should show claims as visible and blocked, never as truth.
Unsafe claims are visible and blocked.
Unsafe claims include validation success.
Unsafe claims include validation failure.

Unsafe claims include validation success, validation failure, issue closure,
release mutation, tag mutation, asset mutation, bundled solver support,
dependency installation, dependency uninstall, solver uninstall, solver
execution, trust restoration, automatic activation, industrial certification,
proprietary solver parity, and full commercial replacement claims.

The future CLI must not convert unsafe claims into output that looks like
evidence.

## 20. Evidence/History Output

Evidence/history output should retain deactivation and reactivation history as
reference only. Historical evidence remains reference-only. Skipped-missing
remains skipped-missing.

CLI explicit-path preview is not fresh validation evidence. It performs no
evidence deletion, no evidence rewrite, and implies no issue closure.

## 21. Action-State Output

Action-state output should render disabled/future-only action states for:

- accept reload as trusted;
- activate reloaded candidate;
- refresh discovery;
- validate solver;
- execute solver;
- install dependency;
- uninstall dependency;
- uninstall solver;
- mutate ProjectSchema;
- create export summary;
- create export file;
- create report file;
- create reloadable bundle;
- copy to clipboard;
- attach to report;
- open output folder;
- close issue;
- mutate release;
- push tag;
- upload asset;
- claim validation success;
- claim validation failure;
- claim certification.

The future implementation may mark the reader invocation itself as enabled only
for the explicitly requested `load-preview --path` flow. Runtime reload,
acceptance, activation, discovery, validation, solver execution, ProjectSchema,
issue, release, tag, asset, export, report, clipboard, and certification actions
remain disabled or future-only.

## 22. Exit-Code Policy

Future exit-code policy must stay non-validating:

- `0`: the command rendered reader diagnostics and, when available, view-model
  review without CLI invocation error. This is not validation success.
- `1`: reader or view-model review is blocked, malformed, stale, unacknowledged,
  unredacted, migration-required, conflicted, or unsafe in a future strict mode.
  This is not validation failure.
- `2`: CLI invocation error, mutually exclusive options, disabled/future-only
  action, or missing required explicit path depending on the future parser
  policy. This is not validation failure.
- `>2`: unexpected internal CLI error.

No exit code closes issues, mutates releases, pushes tags, uploads assets,
certifies optional solvers, proves installed-only validation, or claims skipped
optional validation as success.

## 23. Relationship To Reload File Reader

The future CLI explicit-path implementation should be a thin caller of the
OSW-EXP-113 reload file reader. It must not duplicate reader parsing, weaken
reader policy, or bypass reader diagnostics.

The reader remains a library-level explicit-path sanitizer. The CLI remains a
stdout-first review surface. Reader status never implies validation pass/fail
exit semantics.

## 24. Relationship To Reload View-Model

The future CLI consumes OSW-EXP-107 reload view-model records built from the
reader `safe_mapping`. It must not mutate the view-model source, mutate
view-model records, add path IO to the view-model, or make the view-model
responsible for filesystem policy.

CLI and GUI reload surfaces should continue to share semantics through the
reload view-model.

## 25. Relationship To Current Reload CLI

The current reload CLI is stdout-first and review-only. It uses deterministic
in-memory states and keeps `load-preview` disabled/future-only.

The future explicit-path gate may replace the disabled `load-preview` behavior
with a guarded `--path` review path. Until that implementation gate, there is no
path argument implementation and no runtime file reading.

Existing `explain`, `preview`, `schema`, `sources`, `candidates`,
`acknowledgements`, `diagnostics`, `redaction`, `stale-sources`, `conflicts`,
`unsafe-claims`, `evidence`, and `actions` semantics should remain stdout-first,
review-only, and non-mutating.

## 26. Relationship To Reload GUI

The reload GUI remains a read-only/review-only panel over already-built
view-model records. This design adds no GUI source edits, no GUI file dialog, no
save dialog, no clipboard behavior, no report attachment, and no
open-output-folder behavior.

Future GUI file dialog behavior remains a separate design and implementation
gate. Choosing a file in a future GUI must remain review-only and must not imply
trust, activation, validation, or reload acceptance.

## 27. Relationship To State Writer

The state writer creates explicit local UX state files after caller-supplied
path, acknowledgement, and preflight checks. The future CLI explicit-path
preview may read only that bounded payload family through the reader.

Written state is not validation evidence, not trust restoration, and not
automatic activation. The CLI must not repair, rewrite, migrate, replace, or
delete writer-produced files.

## 28. Relationship To ProjectSchema

There is no ProjectSchema mutation. Reloaded state is not ProjectSchema state.
Reloaded state is not project validation evidence.

Future ProjectSchema integration requires a separate gate with preview,
migration, rollback, docs, and focused tests.

## 29. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. CLI explicit-path preview does not close
issues. CLI explicit-path preview output is not live optional validation.
Skipped-missing remains skipped-missing. Prepared-machine validation remains a
separate gate.

The future CLI must not mark issues ready to close, mutate issue state, mutate
release state, edit tags, edit assets, or claim public validation evidence.

## 30. Security And Privacy Review

The future CLI explicit-path flow treats every user-selected state file as
untrusted, potentially hostile data:

- explicit path only;
- bounded file size through the reader;
- no raw path leak;
- no secret leak;
- no remote URL fetch;
- no plugin package import;
- no script execution;
- no solver execution;
- no dynamic imports from payload content;
- no ProjectSchema mutation;
- no automatic activation;
- no trust restoration;
- reader diagnostics use redacted context;
- malicious payload claims are blocked as data, not executed as instructions.

Size, encoding, JSON shape, duplicate-key, schema, redaction, unsafe-claim,
stale-source, conflict, acknowledgement, and evidence policies remain enforced
by the reader and view-model.

## 31. Non-Actions

This gate does not:

- implement CLI explicit-path behavior;
- edit CLI source;
- edit runtime source;
- edit file-reader source;
- edit GUI source;
- add path argument implementation;
- read persisted state files at runtime;
- parse persisted state files at runtime;
- add runtime file reading;
- add runtime state parsing;
- add runtime reload acceptance;
- add default reload path;
- add background reload;
- scan directories;
- fetch network manifests;
- import plugin packages;
- add GUI file dialog behavior;
- create reloadable bundles;
- create export files;
- create report files;
- add clipboard behavior;
- add report attachment;
- add open-output-folder behavior;
- mutate ProjectSchema;
- add live discovery;
- add passive refresh;
- run validation execution;
- run solver execution;
- install dependencies;
- uninstall dependencies;
- uninstall solvers;
- automatically activate candidates;
- restore trust;
- mutate issues;
- mutate releases;
- mutate tags;
- mutate assets;
- bump version;
- claim validation-pass;
- claim validation-fail;
- claim issue closure;
- claim bundled solver;
- claim certification.

## 32. Future Implementation Test Plan

Future OSW-EXP-115 should test:

- command registration for `load-preview --path`;
- no path means explicit-path diagnostic, not default path;
- missing path diagnostic;
- directory and symlink policy passthrough;
- `--max-bytes` passthrough;
- `--allow-symlink` passthrough;
- `--allow-migration` passthrough;
- `--allow-unredacted-paths` passthrough;
- `--allow-secret-like-values` passthrough;
- reader diagnostics-only output;
- view-model preview-only output;
- text output determinism;
- JSON output determinism;
- reader blockers suppress view-model construction;
- reader safe mapping feeds reload view-model;
- source label remains redacted;
- schema/migration output;
- redaction/privacy output;
- acknowledgement/expiry output;
- candidate lifecycle output;
- stale-source/re-preview output;
- conflict/shared-stack output;
- unsafe-claim output;
- evidence/history output;
- action-state output;
- exit codes do not imply validation success or validation failure;
- no default reload path;
- no background reload;
- no directory scan;
- no network fetch;
- no plugin package import;
- no GUI file dialog;
- no runtime reload acceptance;
- no ProjectSchema mutation;
- no discovery, validation, or solver execution;
- no issue/release/tag/asset mutation;
- no files written.

## 33. Future Gates

Future gates remain separate:

- `OSW-EXP-115_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_EXPLICIT_PATH_IMPLEMENTATION`
- `OSW-EXP-116_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_DESIGN`
- `OSW-EXP-117_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

Runtime reload acceptance, activation review, discovery refresh, validation,
ProjectSchema integration, export/report integration, issue/release mutation,
and certification remain future-gated.
