# Optional solver plugin manifest reload file reader implementation

## 1. Status

Experimental reload file reader implemented (OSW-EXP-113).

- Explicit local path only.
- Library-level reader only.
- No CLI explicit path wiring.
- No GUI file dialog.
- No runtime reload acceptance.
- No ProjectSchema mutation.
- No discovery/validation/solver execution.
- No automatic activation.
- No trust restoration.

It implements the boundary designed in
[optional_solver_plugin_manifest_reload_file_reader_design.md](optional_solver_plugin_manifest_reload_file_reader_design.md).

## 2. Purpose

Provide a safe, bounded bridge from a state-writer-produced local UX state file
into OSW-EXP-107 reload view-model review. The reader reads and parses exactly one
explicit caller-provided path, validates it against the OSW-EXP-102 state-writer
payload family, and returns diagnostics plus a sanitized in-memory mapping. It
never accepts a reload, activates a candidate, restores trust, or implies
validation.

## 3. Public module/class/function names

- Module: `osw.experimental.optional_solvers.plugin_manifest_reload_file_reader`
- Reader: `OptionalSolverPluginManifestReloadFileReader` (method `read`)
- Function: `read_optional_solver_plugin_manifest_reload_file`
- Request: `OptionalSolverPluginManifestReloadFileReadRequest`
- Result: `OptionalSolverPluginManifestReloadFileReadResult`
- Status enum: `OptionalSolverPluginManifestReloadFileReaderStatus`
- Records: `OptionalSolverPluginManifestReloadFileReaderDiagnostic`,
  `...Summary`, `...PayloadMetadata`, `...ActionState`, `...NonActionFlags`
- Constants: `DEFAULT_MAX_BYTES`, `MIGRATABLE_PAYLOAD_SCHEMA_VERSIONS`,
  `READER_VERSION`, `OSPMG_RELOAD_READER_*`, `OSPMG_RELOAD_READER_DIAGNOSTIC_CODES`

The public names are re-exported from the experimental optional-solver package
namespace.

## 4. Request/result model

The request carries `target_path`, `max_bytes` (conservative default
`DEFAULT_MAX_BYTES`), `allow_symlink` (default false), `expected_payload_kind`
(default the state-writer kind), `expected_schema_version` (default the
state-writer schema), `allow_migration` (default false), `allow_unredacted_paths`
(default false), `allow_secret_like_values` (default false), `caller_context`, and
optional `acknowledgements`.

The result carries `status`, `summary`, `payload_metadata`, `diagnostics`,
`blockers`, `warnings`, `safe_mapping` (or `None`), `redacted_target_display`,
`bytes_read`, `payload_hash`, `non_action_flags`, `action_states`, and explicit
`no_validation_claim` / `no_trust_restoration` / `no_automatic_activation` /
`no_discovery_execution` / `no_solver_execution` / `no_issue_closure` /
`no_release_mutation` / `no_certification` honesty flags. `safe_mapping` is set
only when the read is `ready_for_viewmodel`.

## 5. Explicit path policy

The reader reads only the explicit caller path. There is no default path, no
background reload, no directory scan, no glob, no recursion, and no network path
fetch. A blank/`None` path and a non-existent path both yield
`OSPMG_RELOAD_READER_FILE_MISSING`. The reader never creates a parent directory.

## 6. File eligibility policy

The target must be a regular file. Directories and special files yield
`OSPMG_RELOAD_READER_NOT_REGULAR_FILE`; symlinks yield
`OSPMG_RELOAD_READER_SYMLINK_BLOCKED` unless `allow_symlink` is set; empty files
yield `OSPMG_RELOAD_READER_EMPTY_FILE`; files larger than `max_bytes` yield
`OSPMG_RELOAD_READER_FILE_TOO_LARGE` (checked by `stat` size and again by a bounded
read). The extension is only a hint; content validation is authoritative.

## 7. Encoding and JSON parsing policy

The reader decodes UTF-8 (stripping a leading BOM if present). A NUL byte or a
decode failure yields `OSPMG_RELOAD_READER_ENCODING_ERROR`. Parsing uses a strict
`object_pairs_hook` that records duplicate keys; a duplicate key yields
`OSPMG_RELOAD_READER_DUPLICATE_KEY_BLOCKED`. A non-object JSON root yields
`OSPMG_RELOAD_READER_ROOT_NOT_OBJECT`. No code is executed and nothing is
dynamically imported from the loaded data.

## 8. Payload kind/schema policy

The payload kind must equal the expected state-writer kind or the reader emits
`OSPMG_RELOAD_READER_PAYLOAD_KIND_MISMATCH`. A missing or unsupported schema
version yields `OSPMG_RELOAD_READER_SCHEMA_UNSUPPORTED`. A schema in
`MIGRATABLE_PAYLOAD_SCHEMA_VERSIONS`, or a payload that self-declares
`schema_migration[].migration_required`, yields
`OSPMG_RELOAD_READER_MIGRATION_REQUIRED`. A schema mismatch is not validation
failure, and migration remains future-gated (it always blocks the safe mapping in
this gate). The persistence schema model stays separate from ProjectSchema.

## 9. Writer metadata/provenance policy

`payload_metadata` surfaces the writer version, view-model schema version, state
scope, and generated-by display as provenance, plus a reader version. User/plugin
files remain untrusted by default, the trust label is not certification, and
fingerprints are not trust signals. Built-ins remain authoritative by default.

## 10. Non-action flag verification

The result's `non_action_flags` are all false and stay false. If the payload's own
`non_action_flags` carry any truthy value, or the payload asserts a top-level
`validation_success_claimed` / `validation_failure_claimed` /
`issue_closure_claimed` / `certification_claimed`, the reader treats that as an
unsafe claim and blocks with `OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED`. The reader
never upgrades a non-action flag to success.

## 11. Redaction/privacy behavior

The target path is redacted to its basename for all display and diagnostics; raw
paths never appear in messages or rendered text. A payload value matching an
unredacted absolute-path pattern (drive-letter path, `/home/`, `/Users/`,
`%USERPROFILE%`, `$HOME`), or a `redaction_privacy` row flagged
`unredacted_path_blocked`, yields `OSPMG_RELOAD_READER_UNREDACTED_PATH_BLOCKED`
unless `allow_unredacted_paths` is set. A secret-like value (api key, token,
password, bearer, private key, etc.) yields
`OSPMG_RELOAD_READER_SECRET_LIKE_VALUE_BLOCKED` unless `allow_secret_like_values`
is set.

## 12. Acknowledgement/expiry behavior

The reader surfaces the OSW-EXP-112 reload acknowledgement family as reference
context and emits `OSPMG_RELOAD_READER_ACKNOWLEDGEMENT_EXPIRED` when a persisted
acknowledgement row is marked expired. Persisted acknowledgements expire on reload,
source fingerprint change, schema version change, unsafe-claim appearance, trust
policy change, future discovery-refresh result, and file-reader policy change; a
persisted acknowledgement is a record that a warning was shown, not permission to
act.

## 13. Candidate lifecycle behavior

Loaded candidate rows remain review-only. An inactive preview stays preview; a
persisted-active candidate requires future activation review; a deactivated
candidate stays deactivated; reactivation routes to future activation review. The
reader performs no automatic activation and no trust restoration, and loaded state
never overrides built-ins.

## 14. Stale-source/re-preview behavior

A stale or re-preview-required source yields
`OSPMG_RELOAD_READER_STALE_SOURCE_REPREVIEW_REQUIRED` and blocks the safe mapping.
The reader does not inspect the referenced source files, does not restore them, and
treats stale state as review state, not validation failure.

## 15. Conflict/shared-stack behavior

A conflict/shared-stack row yields `OSPMG_RELOAD_READER_CONFLICT_REVIEW_REQUIRED`
and blocks the safe mapping. Built-ins win by default; the reader surfaces the
conflict but does not resolve it.

## 16. Unsafe-claim behavior

Unsafe claims (validation success/failure, issue closure, release mutation,
bundled solver, dependency install, solver execution, trust restoration,
certification) are visible and blocked via
`OSPMG_RELOAD_READER_UNSAFE_CLAIM_BLOCKED`; they are never loaded as truth.

## 17. Evidence/history behavior

Deactivation/reactivation history and historical evidence are retained as
reference only and surfaced with `OSPMG_RELOAD_READER_EVIDENCE_REFERENCE_ONLY`
(an informational, non-blocking diagnostic). Skipped-missing remains
skipped-missing. The reader deletes/rewrites no evidence and implies no issue
closure; loaded state is not validation evidence.

## 18. Diagnostics behavior

The reader reserves and emits the 23-code `OSPMG_RELOAD_READER_*` vocabulary,
always ending a successful read with `OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY`,
`OSPMG_RELOAD_READER_REVIEW_ONLY`, `OSPMG_RELOAD_READER_READY_FOR_VIEWMODEL`, and
`OSPMG_RELOAD_READER_READ_COMPLETED`. Every diagnostic uses redacted context only.

## 19. Safe mapping behavior

A `safe_mapping` is returned only when no blockers remain. It is the freshly
parsed payload (parsed independently on each read, so callers cannot mutate reader
state), is suitable for reload view-model review via `from_payload_mapping`, and is
not a reload acceptance. The reader adds no raw filesystem paths and marks nothing
trusted by default.

## 20. Relationship to state writer

The reader consumes only the OSW-EXP-102 state-writer payload family
([optional_solver_plugin_manifest_state_writer_implementation.md](optional_solver_plugin_manifest_state_writer_implementation.md)).
It is the inverse-but-asymmetric counterpart of the writer: the writer emits, the
reader sanitizes for review. The reader writes nothing, repairs nothing, and
migrates nothing.

## 21. Relationship to reload view-model

The reader's `safe_mapping` feeds the OSW-EXP-107 reload view-model
([optional_solver_plugin_manifest_reload_viewmodel.md](optional_solver_plugin_manifest_reload_viewmodel.md))
through `from_payload_mapping`. The view-model stays pure and path-free; the reader
imports only the view-model's payload-kind/schema constants and never mutates
view-model records.

## 22. Relationship to reload CLI

The reload CLI
([optional_solver_plugin_manifest_reload_cli_implementation.md](optional_solver_plugin_manifest_reload_cli_implementation.md))
still uses deterministic in-memory records only. This gate does not wire the reader
into the CLI; `load-preview`/`read-file` remain disabled/future-only until a
separate CLI explicit-path gate (OSW-EXP-114/115). Reader status never implies a
validation pass/fail exit.

## 23. Relationship to reload GUI

The reload GUI panel remains review-only over already-built records. This gate adds
no GUI file dialog; that remains a separate design/implementation gate
(OSW-EXP-116/117).

## 24. Relationship to ProjectSchema

The reader does not import, instantiate, or mutate ProjectSchema. Loaded state is
not ProjectSchema state and not project validation evidence; it emits
`OSPMG_RELOAD_READER_PROJECT_SCHEMA_BOUNDARY` to make this explicit.

## 25. Relationship to live optional validation issues

Issues `#6` through `#11` remain open. The reader does not close issues, its output
is not live optional validation, skipped-missing remains skipped-missing, and
prepared-machine validation remains separate.

## 26. Security/privacy review

The reader treats every file as untrusted, potentially hostile data and fails
closed: explicit path only, bounded size, UTF-8 only, no NUL/binary, strict JSON
object root, duplicate-key rejection, secret-like blocking, unredacted-path
blocking, no secrets or raw paths in diagnostics, no remote fetch, no script
execution, no plugin import, and no solver execution. Size/encoding/structure
limits bound denial-of-service exposure.

## 27. Non-actions

This gate adds no default reload path, background reload, directory scan, network
fetch, plugin package import, CLI explicit-path wiring, GUI file dialog, runtime
reload acceptance, reloadable bundle creation, export/report file creation,
clipboard/report/open-folder behavior, ProjectSchema mutation, live discovery,
passive refresh, validation execution, solver execution, dependency
install/uninstall, solver uninstall, automatic activation, trust restoration,
issue/release/tag/asset mutation, version bump, or validation-pass/fail,
issue-closure, bundled-solver, or certification claim. The reader writes, creates,
and deletes no files.

## 28. Testing strategy

`tests/unit/test_optional_solver_plugin_manifest_reload_file_reader.py` uses
`tmp_path` only and covers missing/no-path/directory/symlink/empty/oversized/
binary/malformed-JSON/root-array/duplicate-key rejections; payload-kind, schema,
migration, unredacted-path, secret-like, unsafe-claim, stale-source, and conflict
blockers; evidence reference-only retention; a valid payload that yields a safe
mapping that feeds the reload view-model; no raw path leak; no file writes;
all-false non-action flags; and an AST purity scan asserting the source has no
directory scan, network, subprocess, GUI/CLI/ProjectSchema imports, or file
write/delete behavior.

## 29. Future gates

- `OSW-EXP-114_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_EXPLICIT_PATH_DESIGN`
- `OSW-EXP-115_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_EXPLICIT_PATH_IMPLEMENTATION`
- `OSW-EXP-116_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_DESIGN`
- `OSW-EXP-117_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

Runtime reload acceptance, activation review, discovery refresh, validation,
ProjectSchema integration, and certification remain future-gated.

## 30. Follow-up: CLI explicit-path design (OSW-EXP-114)

OSW-EXP-114 designs the future CLI bridge from `load-preview --path` to this
reader
([optional_solver_plugin_manifest_reload_cli_explicit_path_design.md](optional_solver_plugin_manifest_reload_cli_explicit_path_design.md)).
The design does not wire this reader into the CLI, does not edit reader source,
does not add path arguments, does not read or parse files at runtime in this
gate, and does not add runtime reload acceptance, ProjectSchema mutation,
discovery, validation, solver execution, automatic activation, trust restoration,
issue/release mutation, or certification claims.

## 31. Follow-up: CLI explicit-path implementation (OSW-EXP-115)

OSW-EXP-115 wires this reader into the reload CLI only for explicit
`load-preview --path` review
([optional_solver_plugin_manifest_reload_cli_explicit_path_implementation.md](optional_solver_plugin_manifest_reload_cli_explicit_path_implementation.md)).
The CLI remains a caller of the reader rather than duplicating parser logic:
reader diagnostics render first, reader blockers suppress view-model preview,
and reader `safe_mapping` output feeds the reload view-model only for review.
This follow-up does not edit reader source, add default paths, add background
reload, add GUI file dialogs, accept runtime reload, mutate ProjectSchema, run
discovery/validation/solver execution, activate candidates, restore trust, mutate
issues/releases/tags/assets, or claim certification.

## 32. Follow-up: GUI file-dialog design (OSW-EXP-116)

OSW-EXP-116 designs a future GUI chooser/controller that may call this reader
with one explicit user-selected state file, render reader diagnostics before
view-model preview, and pass only reader `safe_mapping` output into reload
view-model review. That design does not edit reader source, add GUI file-dialog
implementation, add direct GUI JSON parsing, call the CLI as a subprocess, add
default/background reload, accept runtime reload, mutate ProjectSchema, run
discovery/validation/solver execution, activate candidates, restore trust,
mutate issues/releases/tags/assets, or claim certification.
