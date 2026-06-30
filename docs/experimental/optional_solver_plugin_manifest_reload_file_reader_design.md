# Optional solver plugin manifest reload file reader design

## 1. Status

Design-only.

This gate defines a future safety contract. It is **not** implementation
authorization. Specifically, this gate carries:

- no file reader implementation
- no parser implementation
- no runtime file reading
- no runtime state parsing
- no runtime reload
- no source edits
- no CLI source edits
- no GUI source edits
- no default reload path
- no background reload
- no directory scan
- no network fetch
- no plugin package import
- no reloadable bundle creation
- no export file creation
- no report file creation
- no clipboard behavior
- no report attachment
- no open-output-folder behavior
- no ProjectSchema mutation
- no live discovery
- no passive refresh
- no validation execution
- no solver execution
- no dependency installation
- no dependency uninstall
- no solver uninstall
- no automatic activation
- no trust restoration
- no issue mutation
- no release mutation
- no tag mutation
- no asset mutation
- no version bump
- no validation-pass claim
- no validation-fail claim
- no bundled-solver claim
- no certification claim

## 2. Purpose

Define a future explicit local file reader/parser boundary for persisted optional
solver plugin manifest UX state files produced by the OSW-EXP-102 state writer.

The design preserves the existing reload, state-writer, reload view-model, reload
GUI, reload CLI, ProjectSchema, discovery, validation, issue/release, and
certification boundaries. The future reader is a *bridge* from an explicit local
file into already-defined OSW-EXP-107 reload review semantics, and nothing more.

## 3. Current state before file reader

- The OSW-EXP-102 state writer exists and can write explicit local UX state files
  to caller-selected paths.
- The OSW-EXP-106 reload design exists.
- The OSW-EXP-107 pure reload view-model exists over caller-supplied mappings.
- The OSW-EXP-109 reload GUI review panel exists (review-only).
- The OSW-EXP-111 reload CLI review surface exists (stdout-first, review-only).
- No reload file reader/parser exists.
- No runtime reload behavior exists.
- No default reload path exists.

The missing piece is a *safe* way to turn an explicit local state file into a
sanitized in-memory mapping that the reload view-model can review. This document
designs that boundary without building it.

## 4. Definition of reload file reader

Definition of reload file reader: a future, explicit local-path reader that may
eventually transform a user/caller-selected file into a sanitized in-memory
mapping suitable for OSW-EXP-107 reload view-model review.

The future reader **may eventually**:

- receive an explicit local path from the caller
- enforce file size limits
- enforce UTF-8 or a documented encoding policy
- parse a JSON-like payload
- verify payload kind
- verify schema version
- verify writer metadata
- verify non-action flags
- reject unsafe claims
- apply redaction checks
- surface stale-source state
- preserve evidence/history as references only
- build diagnostics
- return a safe mapping or reader report

The future reader **must not**:

- choose paths
- scan directories
- fetch URLs
- import plugin packages
- run reload
- activate candidates
- restore trust
- run discovery/validation/solver execution
- mutate ProjectSchema
- close issues
- mutate releases/tags/assets
- claim certification

The reader is an input sanitizer, not a trust authority and not a reload engine.

## 5. Non-meaning of reading a reload file

Reading a reload file does not change product truth. Explicitly:

- reading a reload file is not validation success
- reading a reload file is not validation failure
- reading a reload file is not trust restoration
- reading a reload file is not automatic activation
- reading a reload file is not discovery success
- reading a reload file is not dependency installation
- reading a reload file is not solver execution
- reading a reload file is not ProjectSchema mutation
- reading a reload file is not issue closure
- reading a reload file is not release mutation
- reading a reload file is not certification
- reading a reload file is not report generation
- reading a reload file is not reloadable bundle acceptance

A successfully read file yields review-only data. It never yields permission to
act.

## 6. Explicit path policy

The future reader may accept **only** an explicit caller/user-selected local path.

- no default path
- no background reload
- no glob
- no directory recursion
- no hidden recent-file reload
- no environment-variable expansion without a future explicit policy
- no home-directory leak in diagnostics
- symlink policy must be explicit in the future implementation
- parent creation is forbidden for reading
- a missing file is a diagnostic, not hidden success

The caller always names the file. The reader never guesses, remembers, or
discovers a path.

## 7. File eligibility policy

The future reader applies a conservative file eligibility policy before parsing:

- regular file only
- reject directories
- reject special devices/pipes/sockets
- reject symlinks unless a future explicit policy allows them
- reject oversized files
- reject empty file
- reject binary-looking file
- reject unsupported extension unless a future policy allows it
- extension is only a hint, not trust
- content validation is authoritative

Eligibility is about shape and safety, never about trust. An eligible file is
still untrusted user/plugin data.

## 8. Encoding and JSON policy

- UTF-8 preferred
- a documented BOM policy
- malformed text is a diagnostic
- a JSON object root is required
- a duplicate key policy is defined (reject or last-wins must be explicit)
- maximum nesting/array/string length policy
- unknown keys are retained only as inert diagnostics or rejected by schema policy
- no script execution from loaded data
- no dynamic import from loaded data

Parsing is pure data interpretation. Loaded data is never executable and never a
code path.

## 9. Payload kind and schema policy

- the expected payload kind comes from the OSW-EXP-102 state writer
- a schema version is required
- an unsupported schema blocks
- a migration-required marker blocks
- a schema mismatch is not validation failure
- the persistence schema model remains separate from ProjectSchema
- migration remains future-gated

Schema checks gate review readiness; they never assert that an optional solver
stack passed or failed validation.

## 10. Writer metadata and provenance policy

- the writer version is displayed
- source provenance is retained
- file reader provenance is added (the reader records that it read a file)
- a reader report timestamp may appear in diagnostics only
- user/plugin sources remain untrusted by default
- trust label is not certification
- fingerprints are not trust signals
- built-ins remain authoritative by default

Provenance is descriptive metadata. It never elevates an untrusted file to a
trusted or certified state.

## 11. Non-action flag verification

- payload non-action flags must be present or default conservatively
- any claim of validation execution blocks or is marked unsafe
- any claim of solver execution blocks or is marked unsafe
- any claim of issue/release/tag/asset mutation blocks
- any claim of certification blocks
- the reader never upgrades non-action flags to success

If a file claims an action was performed, the reader treats that as a blocked
unsafe claim, not as evidence the action is real or permitted.

## 12. Redaction/privacy policy

- raw paths are hidden by default
- basename/hash/source-id/display-name are preferred
- home directories, environment variables, secrets, tokens, and API keys are
  blocked
- unredacted paths require a future explicit policy
- fingerprints are not trust signals
- redaction review happens before activation review
- reader diagnostics must use redacted context

The reader is redaction-first. A privacy failure is a blocker, not a warning to
be ignored.

## 13. Acknowledgement and expiry policy

The future reader surfaces these acknowledgement identifiers:

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

Acknowledgements persisted inside a file expire and must be re-shown. Expiry
reasons include:

- reload
- source fingerprint change
- schema version change
- unsafe claim appearance
- trust policy change
- future discovery-refresh result
- file reader policy change

A persisted acknowledgement is a record that a warning was shown, never standing
permission to act.

## 14. Candidate lifecycle policy

- an inactive-preview candidate remains review-only
- a persisted-active candidate requires future activation review
- a deactivated candidate remains a deactivated review state
- reactivation routes to future activation review
- a discovery-refresh state remains a review state
- no automatic activation
- no trust restoration
- loaded state does not override built-ins

Reading a file never changes a candidate's real lifecycle. It only populates
review state.

## 15. Stale-source/re-preview policy

- an old preview is not silently trusted
- missing/moved/changed sources require re-preview
- the file reader does not inspect referenced source files in this gate
- stale-source state is not validation failure
- re-preview remains future-gated

The reader surfaces staleness; it does not resolve it.

## 16. Conflict/shared-stack policy

- conflicts are visible
- built-ins win by default
- persisted state does not override built-ins
- shared-stack warnings are visible
- the file reader does not resolve conflicts
- a future policy is required

The reader shows conflicts honestly and leaves resolution to a future policy
gate.

## 17. Unsafe-claim policy

- unsafe claims are visible and blocked
- unsafe claims are not loaded as truth
- unsafe claims include validation success/failure, issue closure, release
  mutation, bundled solver, dependency installation, solver execution, trust
  restoration, and certification
- unsafe claims produce `OSPMG_RELOAD_READER_*` diagnostics

A file may *claim* anything; the reader records dangerous claims as blocked
diagnostics rather than acting on them.

## 18. Evidence/history policy

- deactivation/reactivation history is retained
- historical evidence is retained as reference only
- skipped-missing remains skipped-missing
- loaded state is not validation evidence
- no evidence deletion/rewrite
- no issue closure is implied

History travels with the payload as inert references. It is never re-interpreted
as fresh validation evidence.

## 19. Reader report model

Conceptual records only (no Python model is implemented in this gate):

- summary
- source file display
- payload metadata
- schema status
- redaction status
- acknowledgement status
- candidate rows
- diagnostics
- warnings/blockers
- raw-payload rejected marker
- safe mapping output
- non-action flags

These describe what a future reader report would contain so that a later
implementation has a target shape, not a built object.

## 20. Diagnostics vocabulary

Design-only reserved codes:

- `OSPMG_RELOAD_READER_FILE_MISSING`
- `OSPMG_RELOAD_READER_NOT_REGULAR_FILE`
- `OSPMG_RELOAD_READER_SYMLINK_BLOCKED`
- `OSPMG_RELOAD_READER_FILE_TOO_LARGE`
- `OSPMG_RELOAD_READER_EMPTY_FILE`
- `OSPMG_RELOAD_READER_ENCODING_ERROR`
- `OSPMG_RELOAD_READER_JSON_PARSE_ERROR`
- `OSPMG_RELOAD_READER_ROOT_NOT_OBJECT`
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

These are reserved names for a future implementation. They are explanatory and
trigger no runtime behavior in this gate.

## 21. Relationship to state writer

- the state writer creates explicit local UX state files
- the file reader may eventually read only that bounded payload family
- the reader is not the writer
- the reader does not write files
- the reader does not repair files
- the reader does not create migration output

Reader and writer are inverse-but-asymmetric: the writer emits, the reader
sanitizes for review only.

## 22. Relationship to reload view-model

- future reader output feeds the OSW-EXP-107 reload view-model
- the view-model remains pure and path-free
- the reader must not mutate view-model records
- the view-model and reader should share diagnostics vocabulary but remain
  separate layers

The reader produces a mapping; the view-model interprets a mapping. Neither
absorbs the other.

## 23. Relationship to reload CLI

- the reload CLI currently uses deterministic in-memory records only
- a future CLI explicit-path reload requires this reader implementation gate first
- the CLI `load-preview` (and any `read-file`) command remains disabled until a
  later implementation gate
- exit codes must not imply validation pass/fail

The CLI keeps its review-only contract until the reader and a separate CLI
explicit-path gate exist.

## 24. Relationship to reload GUI

- the reload GUI currently consumes already-built view-model records only
- a future GUI file dialog requires separate design/implementation gates
- a file dialog must not imply trust, activation, validation, or reload
  acceptance

Choosing a file in a future dialog must remain as inert as naming a path on the
CLI.

## 25. Relationship to ProjectSchema

- no ProjectSchema mutation
- loaded state is not ProjectSchema state
- loaded state is not project validation evidence
- future ProjectSchema integration requires a separate gate

The reader stays entirely inside the experimental optional-solver UX surface and
never touches project state.

## 26. Relationship to live optional validation issues

- issues `#6` through `#11` remain open
- the file reader does not close issues
- file reader output is not live optional validation
- skipped-missing remains skipped-missing
- prepared-machine validation remains separate

Reading a file changes nothing about the open live-validation issues.

## 27. Security and privacy review

- no secrets in diagnostics
- no raw path leak
- no remote URL fetch
- no script execution
- no plugin import
- no solver execution
- no trust restoration
- a malicious payload is treated as rejected data, not as instructions
- denial-of-service controls through size/depth/length limits

The reader treats every input file as potentially hostile, untrusted data and
fails closed.

## 28. Non-actions

This gate does not:

- implement file reader
- implement parser
- edit source
- edit CLI source
- edit GUI source
- read persisted state files
- parse persisted state files
- add runtime reload behavior
- add default reload path
- add background reload
- create reloadable bundles
- create export files
- create report files
- add clipboard behavior
- add report attachment
- add open-output-folder behavior
- mutate ProjectSchema
- add live discovery
- add passive refresh
- import plugin packages
- scan directories
- fetch network manifests
- run validation
- run solver execution
- install dependencies
- uninstall dependencies
- uninstall solvers
- automatically activate candidates
- restore trust
- mutate issues
- mutate releases
- mutate tags
- mutate assets
- bump version
- claim validation-pass
- claim validation-fail
- claim issue closure
- claim bundled solver
- claim certification

## 29. Future implementation test plan

A future OSW-EXP-113 implementation must test:

- explicit path only
- no default path
- missing file diagnostic
- directory rejected
- symlink rejected or policy-enforced
- oversized file rejected
- malformed encoding rejected
- malformed JSON rejected
- root array rejected
- payload kind mismatch rejected
- unsupported schema blocked
- migration required blocked
- unredacted path blocked
- secret-like value blocked
- unsafe claims blocked
- stale-source surfaced
- conflicts surfaced
- evidence/history retained as reference
- safe mapping feeds reload view-model
- no raw path leak
- no discovery/validation/solver execution
- no ProjectSchema mutation
- no issue/release/tag/asset mutation
- no validation pass/fail exit semantics
- no files written

## 30. Future gates

Suggested sequence (follow the repo's latest numbering convention if it differs):

- `OSW-EXP-113_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_FILE_READER_IMPLEMENTATION`
- `OSW-EXP-114_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_EXPLICIT_PATH_DESIGN`
- `OSW-EXP-115_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_CLI_EXPLICIT_PATH_IMPLEMENTATION`
- `OSW-EXP-116_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_DESIGN`
- `OSW-EXP-117_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

Each remains a separate, explicitly-scoped gate. This design gate authorizes none
of them; it only defines the safety contract the reader implementation must meet.

## Follow-up: implemented (OSW-EXP-113)

The reader designed here is implemented in OSW-EXP-113 as a library-level,
explicit-path reader. See
[optional_solver_plugin_manifest_reload_file_reader_implementation.md](optional_solver_plugin_manifest_reload_file_reader_implementation.md).
The implementation honors this contract: explicit path only, bounded eligibility,
UTF-8/JSON object validation, payload-kind/schema checks, redaction/secret/unsafe
blocking, stale/conflict surfacing, reference-only evidence, a safe review mapping,
and no CLI wiring, GUI dialog, runtime reload acceptance, ProjectSchema mutation,
discovery/validation/solver execution, activation, or trust restoration.

## Follow-up: CLI explicit-path design (OSW-EXP-114)

OSW-EXP-114 designs future CLI explicit-path semantics for using the implemented
reader from `load-preview --path`
([optional_solver_plugin_manifest_reload_cli_explicit_path_design.md](optional_solver_plugin_manifest_reload_cli_explicit_path_design.md)).
It remains design-only: no CLI source edits, no path argument implementation, no
runtime file reading/parsing in this gate, no default path, no background reload,
no GUI file dialog, no runtime reload acceptance, no ProjectSchema mutation, no
discovery/validation/solver execution, no activation, no trust restoration, no
issue/release mutation, and no certification claim.
