# Optional Solver Plugin Manifest Reload GUI File Dialog Design

## 1. Status

Design-only.

This gate adds no GUI file-dialog implementation, no GUI source edits, no CLI
source edits, no runtime source edits, no file-reader source edits, no reload
view-model source edits, no file dialog widgets, no file opening behavior, no
runtime file reading, no runtime state parsing, and no runtime reload
acceptance.

This gate also adds no default reload path, no background reload, no directory
scan, no network fetch, no plugin package import, no CLI subprocess use, no
reloadable bundle creation, no export file creation, no report file creation,
no clipboard behavior, no report attachment, no open-output-folder behavior, no
ProjectSchema mutation, no live discovery, no passive refresh, no validation
execution, no solver execution, no dependency installation, no dependency
uninstall, no solver uninstall, no automatic activation, no trust restoration,
no issue mutation, no release mutation, no tag mutation, no asset mutation, no
version bump, no validation-pass claim, no validation-fail claim, no
issue-closure claim, no bundled-solver claim, and no certification claim.

This document is not implementation authorization. It records the future
contract that a later OSW-EXP-117 implementation gate must satisfy.

Follow-up: OSW-EXP-117 implements this design in
[optional_solver_plugin_manifest_reload_gui_file_dialog_implementation.md](optional_solver_plugin_manifest_reload_gui_file_dialog_implementation.md)
as an outer GUI chooser/controller that opens no native dialog on construction,
uses the OSW-EXP-113 reader, renders diagnostics before view-model preview, and
keeps reload acceptance, activation, validation, solver execution,
ProjectSchema mutation, issue/release mutation, and certification out of scope.

## 2. Purpose

This document defines future GUI file-dialog semantics for optional solver
plugin manifest reload preview. The future behavior may connect a PySide file
chooser to the existing OSW-EXP-113 reload file reader and the OSW-EXP-107
reload view-model in a later implementation gate.

The design preserves the existing OSW-EXP-109 reload panel boundary: the panel
remains a pure renderer for already-built reload view-model records. Any file
selection and reader invocation belongs to an outer chooser/controller layer.

The design also preserves reload panel, reload file reader, reload CLI,
ProjectSchema, discovery, validation, issue/release, tag/asset, and
certification boundaries.

## 3. Current State Before GUI File Dialog

- The OSW-EXP-102 state writer exists and writes explicit local UX state files
  through caller-supplied paths.
- The OSW-EXP-113 reload file reader exists as a library-level explicit-path
  reader that returns diagnostics and safe mappings.
- The OSW-EXP-107 reload view-model exists and consumes caller-supplied
  in-memory mappings only.
- The OSW-EXP-109 reload GUI review panel exists and consumes already-built
  reload view-models.
- The OSW-EXP-115 reload CLI explicit path exists and is reader-first,
  stdout-first, and review-only.
- No GUI file dialog exists for reload.
- No runtime reload acceptance exists.
- No default reload path exists.

User/plugin files remain untrusted by default. Built-ins remain authoritative by
default. Skipped-missing remains skipped-missing. Issues `#6` through `#11`
remain open and separate.

## 4. Definition Of GUI File-Dialog Reload Preview

GUI file-dialog reload preview is a future explicit user action that selects one
local state file, invokes the OSW-EXP-113 library reader, displays reader
diagnostics, and only if the reader returns a safe mapping, displays reload
view-model review through the existing reload GUI review path.

The future GUI may eventually:

- offer an `Open reload state...` action;
- use a PySide file dialog;
- pass the selected path to the OSW-EXP-113 reader;
- render the reader report;
- render the reader safe mapping through the OSW-EXP-107 reload view-model;
- update the existing reload panel or a surrounding review container;
- keep all actions review-only.

The future GUI must not:

- choose a path automatically;
- use a default path;
- run background reload;
- scan directories;
- fetch URLs or network manifests;
- import plugin packages;
- call the reload CLI as a subprocess;
- accept reload as trusted;
- activate candidates;
- restore trust;
- run discovery, validation, or solver execution;
- mutate ProjectSchema;
- close issues;
- mutate releases, tags, or assets;
- claim certification.

## 5. Non-Meaning Of GUI File-Dialog Preview

GUI file-dialog preview is not validation success. GUI file-dialog preview is
not validation failure. GUI file-dialog preview is not trust restoration. GUI
file-dialog preview is not automatic activation. GUI file-dialog preview is not
discovery success. GUI file-dialog preview is not dependency installation. GUI
file-dialog preview is not solver execution. GUI file-dialog preview is not
ProjectSchema mutation. GUI file-dialog preview is not issue closure. GUI
file-dialog preview is not release mutation. GUI file-dialog preview is not tag
mutation. GUI file-dialog preview is not asset mutation. GUI file-dialog
preview is not certification. GUI file-dialog preview is not report generation.
GUI file-dialog preview is not reloadable bundle acceptance.

Reader success means only that a bounded local UX state file produced a safe
review mapping. It does not make a user/plugin manifest trusted, active,
validated, failed, installed, discovered, certified, or ready for issue closure.

## 6. Future User Flow

Future GUI states:

- `no_file_selected`
- `file_dialog_opened`
- `file_selected`
- `reader_preflight`
- `reader_blocked`
- `reader_warning`
- `reader_ready_for_review`
- `view_model_preview_ready`
- `review_acknowledgements_required`
- `reload_acceptance_future_gated`
- `cancelled_noop`
- `dialog_error`

These states describe preview readiness only. They do not authorize runtime
reload acceptance, ProjectSchema mutation, activation, discovery refresh,
validation, solver execution, issue mutation, release mutation, tag mutation, or
asset mutation.

## 7. File-Dialog Option Policy

The future GUI may accept exactly one explicit user-selected local file path.

File-dialog option policy:

- no default reload path;
- no recent-file fallback;
- no environment-variable path source;
- no home-directory default beyond whatever the platform dialog displays;
- no project path inference;
- no glob expansion;
- no directory selection;
- no URL or network location fetch;
- no background reload after startup;
- no hidden reload on project open;
- no parent directory creation;
- no save/export/report target selection;
- cancellation is a no-op;
- filters for JSON or state-writer payloads are hints only, not trust signals;
- selected path display is redacted to basename, source id, hash, or reader
  display text.

A selected path is not trusted merely because the user selected it.

## 8. Reader Invocation Policy

The future GUI controller may call only the OSW-EXP-113 library reader. It must
use a request object that carries the explicit selected path and conservative
reader policy options. It must render reader diagnostics first.

Reader invocation policy:

- call `OptionalSolverPluginManifestReloadFileReader.read(...)` or the
  repo-consistent helper;
- pass exactly the user-selected path;
- preserve reader defaults unless the user explicitly opts into a future policy
  override;
- never use ad hoc JSON loading;
- never bypass the reader with direct file open calls in GUI code;
- never call the CLI as a subprocess;
- never mutate reader results;
- never mutate reload view-model records;
- block view-model construction when reader blockers exist;
- route only reader `safe_mapping` output into the reload view-model;
- treat all reader statuses as review state, not validation evidence.

## 9. GUI Layout Model

The future GUI layout should separate the chooser/controller from the existing
`OptionalSolverPluginManifestReloadPanel`.

Layout model:

- an outer chooser/controller owns the future `Open reload state...` action;
- a compact status area shows `no_file_selected`, selected-file display, reader
  status, blocker/warning counts, and action state;
- a reader diagnostics area shows reader report rows before any view-model
  preview;
- the existing reload panel remains the pure view-model renderer;
- selected file labels are redacted;
- disabled/future-only actions remain visible or absent according to the
  existing action-state pattern;
- the preview area never writes files, creates reports, opens folders, copies to
  clipboard, accepts reload, activates candidates, or mutates ProjectSchema.

## 10. Reader Diagnostics Display

Reader diagnostics display should show:

- reader status;
- redacted target display;
- bytes read;
- payload hash or fingerprint display when available;
- payload kind;
- payload schema version;
- writer version;
- reader version;
- blocker count;
- warning count;
- diagnostic count;
- ready-for-viewmodel flag;
- each `OSPMG_RELOAD_READER_*` code with severity, blocker state, related
  redacted context, and suggested fix;
- action states and non-action flags.

Reader diagnostics are review diagnostics only. They are not validation success
and not validation failure.

## 11. Reload View-Model Display After Reader Success

Reload view-model display after reader success is allowed only when the reader
returns a non-`None` safe mapping. The future GUI may build an
`OptionalSolverPluginManifestReloadViewModel` from that safe mapping and the
reader redacted target display.

The existing reload panel or a surrounding review container should display:

- summary/readiness;
- source/provenance;
- schema/migration;
- candidates;
- acknowledgements/expiry;
- redaction/privacy;
- stale-source/re-preview;
- conflict/shared-stack;
- unsafe-claim;
- evidence/history;
- diagnostics;
- disabled/future action states;
- safety guidance.

If no safe mapping exists, the GUI must not synthesize one, partially display
payload fragments as authoritative view-model state, or call a reader blocker a
validation failure.

## 12. Schema/Migration Display

Schema/migration display should show required payload kind, actual payload kind,
required schema version, actual schema version, writer version, migration-needed
state, unsupported-schema blockers, migration policy, and ProjectSchema
separation.

Schema mismatch is not validation failure. Migration is future-gated. The
persistence schema model remains separate from ProjectSchema. This design gate
creates no schema file and performs no migration.

## 13. Redaction/Privacy Display

Redaction/privacy display should state that raw absolute paths are hidden by
default. Target display is redacted. Unredacted-path blockers and secret-like
value blockers are visible. Future allow flags are explicit policy overrides,
not defaults and not trust restoration.

Fingerprints and hashes are not trust signals. Diagnostics must not leak raw
home directories, environment variables, tokens, API keys, credentials, private
keys, private network paths, solver install paths, or plugin install paths.
Redaction review happens before future activation review.

## 14. Acknowledgement/Expiry Display

Acknowledgement/expiry display should include:

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
and file-reader policy change. Satisfied acknowledgements do not validate,
reload, trust, activate, close issues, mutate releases, or certify anything.

## 15. Candidate Lifecycle Display

Candidate lifecycle display should show persisted lifecycle state and reload
review state:

- inactive preview remains review-only;
- persisted active requires future activation review;
- deactivated remains deactivated review state;
- reactivation routes to future activation review;
- discovery-refresh state remains review state;
- skipped-missing remains skipped-missing when represented.

The future GUI file-dialog preview provides no automatic activation and no trust
restoration.

## 16. Stale-Source/Re-Preview Display

Stale-source/re-preview display should show that old preview data is not
silently trusted. Missing, moved, changed, or stale sources require re-preview
when that state is present in the payload.

The selected dialog file is a path to persisted UX state only. The GUI must not
inspect referenced plugin/source paths, repair stale sources, run passive
refresh, run discovery, or turn stale-source state into validation failure.

## 17. Conflict/Shared-Stack Display

Conflict/shared-stack display should keep conflicts visible:

- built-ins win by default;
- persisted state does not override built-ins;
- shared-stack warnings are visible;
- conflict review remains blocked or warning-only according to reader and
  view-model diagnostics;
- conflict resolution requires a separate future policy gate.

The GUI file-dialog preview does not resolve conflicts and does not elevate
user/plugin manifests.

## 18. Unsafe-Claim Display

Unsafe-claim display should show claims as visible and blocked, never as truth.
Unsafe claims are visible and blocked. Unsafe claims include validation success.
Unsafe claims include validation failure.

Unsafe claims include validation success, validation failure, issue closure,
release mutation, tag mutation, asset mutation, bundled solver support,
dependency installation, dependency uninstall, solver uninstall, solver
execution, trust restoration, automatic activation, industrial certification,
proprietary solver parity, and full commercial replacement claims.

The future GUI must not convert unsafe claims into output that looks like
evidence.

## 19. Evidence/History Display

Evidence/history display should retain deactivation and reactivation history as
reference only. Historical evidence remains reference-only. Skipped-missing
remains skipped-missing.

GUI file-dialog preview is not fresh validation evidence. It performs no
evidence deletion, no evidence rewrite, and implies no issue closure.

## 20. Action-State Display

Action-state display should render disabled/future-only states for:

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

Only the future explicit file selection and reader preview may become enabled in
a later implementation gate. Runtime reload, acceptance, activation, discovery,
validation, solver execution, ProjectSchema, issue, release, tag, asset, export,
report, clipboard, open-folder, and certification actions remain disabled or
future-only.

## 21. Dialog Cancellation And Error Policy

Dialog cancellation and error policy:

- cancellation returns to `cancelled_noop` or `no_file_selected`;
- cancellation performs no file read;
- cancellation performs no state parse;
- cancellation preserves the current accepted preview, if any;
- cancellation mutates no ProjectSchema state;
- file-dialog errors render diagnostics without attempting CLI fallback;
- reader errors render reader diagnostics and stop before view-model preview;
- unexpected GUI errors do not claim validation failure;
- no temporary files, export files, report files, or reloadable bundles are
  created.

## 22. Relationship To Reload File Reader

The future GUI file-dialog implementation should be a thin caller of the
OSW-EXP-113 reload file reader. It must not duplicate reader parsing, weaken
reader policy, bypass reader diagnostics, or make the GUI responsible for JSON
shape, schema, redaction, unsafe-claim, stale-source, or conflict policy.

The reader remains a library-level explicit-path sanitizer. The GUI remains a
review surface. Reader status never implies validation pass/fail GUI semantics.

## 23. Relationship To Reload View-Model

The future GUI consumes OSW-EXP-107 reload view-model records built from the
reader safe mapping. It must not mutate the reload view-model source, mutate
view-model records, add path IO to the view-model, or make the view-model
responsible for filesystem policy.

CLI and GUI reload surfaces should continue to share semantics through the
reload view-model.

## 24. Relationship To Existing Reload Panel

The existing OSW-EXP-109 `OptionalSolverPluginManifestReloadPanel` remains
read-only/review-only over already-built view-model records. The panel remains
pure view-model rendering.

Future file-dialog behavior belongs outside the panel or in a surrounding
controller. The panel should not gain direct `QFileDialog`, direct file open,
directory scan, CLI subprocess, ProjectSchema mutation, discovery, validation,
solver, activation, trust, issue, release, tag, asset, export, report,
clipboard, or open-folder behavior.

## 25. Relationship To Reload CLI

The OSW-EXP-115 reload CLI explicit-path implementation already provides
`load-preview --path` for stdout-first review. Future GUI file-dialog behavior
may share reader and view-model semantics with that CLI but must not call the
CLI as a subprocess.

The GUI should not inherit CLI exit-code semantics as validation semantics. CLI
completion is not validation success, and CLI blocked preview is not validation
failure.

## 26. Relationship To State Writer

The state writer creates explicit local UX state files after caller-supplied
path, acknowledgement, and preflight checks. The future GUI file-dialog preview
may read only that bounded payload family through the OSW-EXP-113 reader.

Written state is not validation evidence, not trust restoration, and not
automatic activation. The GUI must not repair, rewrite, migrate, replace, or
delete writer-produced files.

## 27. Relationship To ProjectSchema

There is no ProjectSchema mutation. Reloaded state is not ProjectSchema state.
Reloaded state is not project validation evidence.

Future ProjectSchema integration requires a separate gate with preview,
migration, rollback, docs, and focused tests.

## 28. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. GUI file-dialog preview does not close
issues. GUI file-dialog preview output is not live optional validation.
Skipped-missing remains skipped-missing. Prepared-machine validation remains a
separate gate.

The future GUI must not mark issues ready to close, mutate issue state, mutate
release state, edit tags, edit assets, or claim public validation evidence.

## 29. Security And Privacy Review

The future GUI file-dialog flow treats every user-selected state file as
untrusted, potentially hostile data:

- explicit user selection only;
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

## 30. Non-Actions

This gate does not:

- implement GUI file-dialog behavior;
- edit GUI source;
- edit CLI source;
- edit runtime source;
- edit file-reader source;
- edit reload view-model source;
- add file dialog widgets;
- add file opening behavior;
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
- use a CLI subprocess;
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

No runtime source, GUI source, CLI source, reload file-reader source, reload
view-model source, ProjectSchema source, release asset, tag, issue, release,
version metadata, solver/runtime artifact, export file, report file, or
reloadable bundle is changed by this design gate.

## 31. Future Implementation Test Plan

Future OSW-EXP-117 should test:

- no file selected initial state;
- `Open reload state...` action is explicit user action only;
- dialog cancellation is a no-op;
- selected path display is redacted;
- JSON/state-writer filters are hints only;
- no default reload path;
- no recent/env/home/project fallback;
- no directory selection, URL fetch, glob, or background reload;
- reader request carries exactly the selected path;
- reader diagnostics render before view-model preview;
- reader blockers suppress view-model construction;
- reader warnings remain visible;
- reader safe mapping feeds reload view-model;
- source label remains redacted;
- existing reload panel stays pure view-model rendering;
- schema/migration display;
- redaction/privacy display;
- acknowledgement/expiry display;
- candidate lifecycle display;
- stale-source/re-preview display;
- conflict/shared-stack display;
- unsafe-claim display;
- evidence/history display;
- action-state display;
- no CLI subprocess use;
- no GUI source direct JSON parsing or direct file open bypass;
- no file writes or output files;
- no runtime reload acceptance;
- no ProjectSchema mutation;
- no discovery, validation, solver execution, install, uninstall, activation,
  trust restoration, issue/release/tag/asset mutation, or certification claim.

## 32. Future Gates

Future gates remain separate:

- `OSW-EXP-117_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-EXP-118_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_DESIGN` if
  runtime acceptance is ever considered
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

Runtime reload acceptance, activation review, discovery refresh, ProjectSchema
integration, validation, issue/release workflows, export/report integration,
and certification remain future-gated.
