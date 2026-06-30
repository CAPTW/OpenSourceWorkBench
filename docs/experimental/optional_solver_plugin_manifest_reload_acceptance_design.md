# Optional Solver Plugin Manifest Reload Acceptance Design

## 1. Status

Design-only.

This gate adds no reload acceptance implementation, no runtime source edits, no
GUI source edits, no CLI source edits, no file-reader source edits, no reload
view-model source edits, no acceptance buttons, no acceptance CLI commands, no
persistence writes, no ProjectSchema mutation, and no runtime reload acceptance.

This gate also adds no default reload path, no background reload, no directory
scan, no network fetch, no plugin package import, no CLI subprocess use, no
reloadable bundle creation, no export file creation, no report file creation, no
clipboard behavior, no report attachment, no open-output-folder behavior, no
live discovery, no passive refresh, no validation execution, no solver
execution, no dependency installation, no dependency uninstall, no solver
uninstall, no automatic activation, no trust restoration, no issue mutation, no
release mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

This document is not implementation authorization. It records the future
contract that a later acceptance view-model or GUI/CLI action gate must satisfy
before any accepted state can exist.

## 2. Purpose

The purpose is to define future reload acceptance semantics after explicit
reader and view-model preview. The design connects a successful reload file
reader result, reload view-model review, CLI explicit-path preview, and GUI
file-dialog preview to a future bounded in-memory/session UX state boundary.

The design preserves the reload reader, reload view-model, reload GUI, reload
CLI, state writer, ProjectSchema, discovery, validation, issue/release, asset,
tag, and certification boundaries.

Reload acceptance must remain a review-state transition. It is not a runtime
plugin loader, not validation evidence, not trust restoration, not activation,
not persistence, and not project mutation.

## 3. Current State Before Reload Acceptance

- The OSW-EXP-102 state writer exists and writes explicit local UX state files
  only through caller-supplied paths and acknowledgements.
- The OSW-EXP-113 reload file reader exists and returns diagnostics plus a safe
  mapping for review from one explicit local path.
- The OSW-EXP-107 reload view-model exists and consumes caller-supplied
  in-memory mappings only.
- The OSW-EXP-115 reload CLI explicit-path preview exists and is reader-first,
  stdout-first, and review-only.
- The OSW-EXP-117 reload GUI file-dialog preview exists and uses the reader,
  reload view-model, and existing reload panel for review-only display.
- Existing surfaces are preview/review-only.
- No reload acceptance exists.
- No runtime reload acceptance exists.
- No ProjectSchema mutation exists.
- No default reload path exists.

User/plugin files remain untrusted by default. Built-ins remain authoritative by
default. Skipped-missing remains skipped-missing. Issues `#6` through `#11`
remain open and separate.

## 4. Definition Of Reload Acceptance

Reload acceptance is a future explicit user/caller action after successful
reader and view-model review that may copy a reviewed, safe, redacted,
non-trusted UX state into a bounded in-memory/session review state.

Future reload acceptance may eventually:

- accept reviewed safe mapping into temporary/session UX state;
- mark a reload preview as acknowledged for this session;
- make accepted review state visible to later activation, deactivation,
  reactivation, and discovery-refresh review gates;
- keep accepted state untrusted by default;
- keep accepted state separate from ProjectSchema state;
- keep all unsafe/runtime actions disabled or future-only.

Reload acceptance must not:

- accept reload as trusted;
- activate candidates;
- restore trust;
- run discovery;
- run validation;
- execute solvers;
- mutate ProjectSchema;
- persist state automatically;
- close issues;
- mutate releases, tags, or assets;
- claim certification.

## 5. Non-Meaning Of Reload Acceptance

Reload acceptance is not validation success. Reload acceptance is not validation
failure. Reload acceptance is not trust restoration. Reload acceptance is not
automatic activation. Reload acceptance is not discovery success. Reload
acceptance is not dependency installation. Reload acceptance is not dependency
uninstall. Reload acceptance is not solver uninstall. Reload acceptance is not
solver execution. Reload acceptance is not ProjectSchema mutation. Reload
acceptance is not issue closure. Reload acceptance is not release mutation.
Reload acceptance is not tag mutation. Reload acceptance is not asset mutation.
Reload acceptance is not certification. Reload acceptance is not report
generation. Reload acceptance is not reloadable bundle creation. Reload
acceptance is not persistence write. Reload acceptance is not validation-pass
claim, validation-fail claim, issue-closure claim, bundled-solver claim, or
certification claim.

Reader success means only that a bounded local UX state file produced a safe
review mapping. View-model readiness means only that the mapping is coherent for
review. Acceptance means only that the reviewed mapping has been acknowledged
for the current session/review boundary.

## 6. Future Acceptance Preconditions

Future acceptance requires all of the following:

- explicit user/caller action;
- a successful OSW-EXP-113 reader result with no blockers;
- a non-`None` reader `safe_mapping`;
- an OSW-EXP-107 reload view-model built from that safe mapping;
- visible reader diagnostics before acceptance is available;
- visible reload view-model summary, source, schema, candidates,
  acknowledgements, redaction/privacy, stale-source, conflict/shared-stack,
  unsafe-claim, evidence/history, trust/provenance, and action-state records;
- required acknowledgements satisfied for this preview;
- redaction/privacy review complete;
- no unredacted-path or secret-like blocker;
- no stale-source/re-preview blocker;
- no conflict/shared-stack blocker;
- no unsafe-claim blocker;
- payload kind and schema version supported without migration;
- source fingerprint or reader payload hash still matching the preview;
- no issue/release/tag/asset/version mutation requested;
- no validation, discovery, solver execution, dependency install, dependency
  uninstall, solver uninstall, automatic activation, trust restoration,
  persistence write, ProjectSchema mutation, export, report, clipboard, or
  open-folder action requested.

## 7. Future Acceptance Blockers

Future acceptance is blocked by:

- missing explicit action;
- reader blocker diagnostics;
- missing reader safe mapping;
- view-model unavailable or blocked;
- missing required acknowledgement;
- expired acknowledgement;
- unsupported schema;
- migration required;
- payload kind mismatch;
- raw path or secret-like content blocker;
- stale source or re-preview required state;
- unresolved conflict/shared-stack blocker;
- unsafe validation success, validation failure, issue closure, release
  mutation, tag mutation, asset mutation, bundled solver, dependency install,
  dependency uninstall, solver uninstall, solver execution, trust restoration,
  automatic activation, or certification claim;
- a changed selected file, payload hash, reader policy, schema version, trust
  policy, source fingerprint, or unsafe-claim set since preview;
- any request to mutate ProjectSchema, persist state, run discovery, run
  validation, execute a solver, install/uninstall dependencies, activate
  candidates, restore trust, close issues, mutate releases/tags/assets, create
  reports, create export files, create reloadable bundles, copy to clipboard, or
  open an output folder.

## 8. Future User Flow

Future user flow states:

- `no_reload_preview`
- `reader_preview_required`
- `reader_blocked`
- `view_model_review_required`
- `acknowledgement_required`
- `acceptance_ready_for_session`
- `acceptance_blocked`
- `accepted_for_session_review`
- `accepted_state_stale`
- `accepted_state_cleared`
- `future_activation_review_required`
- `future_discovery_refresh_required`

The flow is:

1. The user/caller selects or supplies one explicit local state file through the
   existing reader-first CLI or GUI preview surface.
2. The OSW-EXP-113 reader validates the file and emits diagnostics.
3. Only reader `safe_mapping` output feeds the reload view-model.
4. The user/caller reviews all required reload view-model sections.
5. The user/caller satisfies acknowledgements for the current preview.
6. A future acceptance action may copy the reviewed mapping into
   session-scoped UX review state.
7. Later activation, deactivation, reactivation, or discovery-refresh surfaces
   may see that accepted review state, but must run their own review gates.

No flow state authorizes runtime reload, trust, activation, discovery,
validation, solver execution, ProjectSchema mutation, issue/release/tag/asset
mutation, persistence writes, export/report generation, reloadable bundle
creation, or certification claims.

## 9. Acknowledgement Model

Future acceptance requires visible acknowledgements:

- `reload_acceptance_not_validation`
- `reload_acceptance_not_validation_failure`
- `reload_acceptance_not_trust_restoration`
- `reload_acceptance_not_automatic_activation`
- `reload_acceptance_not_discovery_success`
- `reload_acceptance_not_dependency_install`
- `reload_acceptance_not_dependency_uninstall`
- `reload_acceptance_not_solver_uninstall`
- `reload_acceptance_no_solver_execution`
- `reload_acceptance_not_issue_closure`
- `reload_acceptance_not_release_mutation`
- `reload_acceptance_not_tag_mutation`
- `reload_acceptance_not_asset_mutation`
- `reload_acceptance_not_certification`
- `reload_acceptance_not_persistence_write`
- `reload_acceptance_not_projectschema_mutation`
- `reload_acceptance_session_scoped`
- `redaction_reviewed`
- `unredacted_paths_blocked`
- `secret_like_values_blocked`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `activation_review_required_after_acceptance`
- `no_live_discovery`
- `no_passive_refresh`
- `no_plugin_package_import`
- `no_validation_execution`
- `no_solver_execution`
- `trust_label_not_certification`

Acknowledgements are review controls. They do not validate, fail, reload,
trust, activate, discover, install, uninstall, execute, persist, mutate
ProjectSchema, close issues, mutate releases/tags/assets, create outputs, or
certify anything.

## 10. Acknowledgement Expiry Policy

Acknowledgements expire on:

- new reload preview;
- selected file change;
- payload hash or fingerprint change;
- reader version or policy change;
- schema version change;
- migration policy change;
- redaction policy change;
- trust policy change;
- source fingerprint change;
- stale-source state change;
- conflict/shared-stack state change;
- unsafe-claim appearance or change;
- future discovery-refresh result;
- future activation/deactivation/reactivation policy change;
- OSW version or acceptance contract version change.

Expired acknowledgement state blocks acceptance and requires re-review. An
expired acknowledgement is not validation failure and does not imply issue
closure, release mutation, or certification.

## 11. Accepted-State Scope Model

Accepted reload state is session/review scoped. It is not persisted by default
and is not ProjectSchema state.

Future accepted state may contain:

- redacted target display;
- reader payload hash or safe source fingerprint display;
- reader version and policy summary;
- payload kind and schema version;
- reload view-model summary;
- redacted sources and provenance;
- reviewed candidate records;
- acknowledgement satisfaction records for this session;
- redaction/privacy review state;
- stale-source/re-preview state;
- conflict/shared-stack state;
- unsafe-claim state;
- evidence/history reference state;
- disabled/future action-state records;
- acceptance diagnostics.

Accepted state must not contain raw secret paths, plugin code, plugin package
imports, solver binaries, dependency install instructions as executable actions,
validation-pass evidence, validation-fail evidence, issue-closure readiness,
release mutation commands, tag mutation commands, asset mutation commands,
arbitrary executable scripts, certification claims, or unrestricted external
URLs.

## 12. Reader And Preview Provenance

Accepted review state must retain reader and preview provenance:

- selected file display is redacted;
- reader payload hash or fingerprint display is stored for staleness checks;
- reader version is visible;
- reader policy options are visible;
- payload kind and schema version are visible;
- writer version and generated-by display remain provenance only;
- CLI or GUI caller context is visible as a review source, not a trust signal;
- source labels and trust labels remain untrusted by default unless they are
  built-in records already known to OSW;
- trust label is not certification.

Reader and preview provenance does not make a payload trusted. It does not
authorize plugin imports, discovery, validation, solver execution, issue
closure, release mutation, tag mutation, asset mutation, or certification.

## 13. Schema/Migration Policy

Acceptance requires a supported payload kind and schema version. Missing,
unsupported, or migratable schema states block acceptance. Migration remains a
future separate gate.

Schema mismatch is not validation failure. Persistence schema is separate from
ProjectSchema. Acceptance creates no schema file, writes no settings file, and
performs no migration.

Future migration behavior must define its own preview, rollback, tests,
diagnostics, and ProjectSchema boundary before it can feed acceptance.

## 14. Redaction/Privacy Policy

Acceptance keeps redaction-first behavior:

- raw absolute paths are hidden by default;
- selected target display is redacted;
- source references use basename, source id, hash, or reader display text;
- unredacted paths block acceptance unless a later policy explicitly allows
  them;
- secret-like values block acceptance unless a later policy explicitly allows
  them;
- fingerprints and hashes are not trust signals;
- diagnostics must not leak home directories, environment variables, tokens,
  API keys, credentials, private keys, private network paths, solver install
  paths, or plugin install paths.

Redaction review happens before future acceptance and before any later
activation review.

## 15. Candidate Lifecycle Policy

Candidate lifecycle state remains review state:

- inactive preview remains review-only;
- persisted active state requires future activation review;
- deactivated state remains deactivated review state;
- reactivation routes to future activation review;
- discovery-refresh state remains review state;
- skipped-missing remains skipped-missing when represented.

Acceptance does not automatically activate candidates and does not restore
trust. Accepted review state may be visible to future activation,
deactivation, reactivation, or discovery-refresh gates only as prior review
context.

## 16. Stale-Source/Re-Preview Policy

Acceptance requires the current preview to match the selected file and reader
result. Missing, moved, changed, or stale sources require re-preview when that
state is present in the payload.

Acceptance does not inspect referenced plugin/source paths, repair stale
sources, restore files, run passive refresh, run discovery, or turn stale-source
state into validation failure.

If accepted state becomes stale after acceptance, future surfaces must mark it
`accepted_state_stale` and require re-preview before forward review.

## 17. Conflict/Shared-Stack Policy

Conflicts remain visible. Built-ins win by default. Reloaded state does not
override built-ins. Shared-stack warnings remain visible. Conflict resolution
requires a future separate policy gate.

Acceptance is blocked when the reader or view-model marks a conflict as a
blocker. Warning-only conflict state may be accepted only as visible review
context and never as trust elevation.

## 18. Unsafe-Claim Policy

Unsafe claims are visible and blocked, never accepted as truth. Unsafe claims
include validation success, validation failure, issue closure, release mutation,
tag mutation, asset mutation, bundled solver support, dependency installation,
dependency uninstall, solver uninstall, solver execution, trust restoration,
automatic activation, industrial certification, proprietary solver parity, and
full commercial replacement claims.

Future acceptance must not convert unsafe claims into validation evidence,
failure evidence, release evidence, issue evidence, trust evidence, or
certification evidence.

## 19. Evidence/History Policy

Deactivation and reactivation history remain reference-only. Historical
evidence remains reference-only. Skipped-missing remains skipped-missing.

Acceptance is not fresh validation evidence. It performs no evidence deletion,
no evidence rewrite, and no issue closure. It must preserve reader/view-model
diagnostics that explain what was reviewed and why unsafe actions remain
disabled.

## 20. Action-State Policy

Future acceptance must render disabled/future-only actions for:

- accept reload as trusted;
- activate reloaded candidate;
- refresh discovery;
- validate solver;
- execute solver;
- install dependency;
- uninstall dependency;
- uninstall solver;
- mutate ProjectSchema;
- persist state;
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
- claim bundled solver support;
- claim certification.

Only the future explicit acceptance transition may become enabled in a later
implementation gate. Runtime reload, trust, activation, discovery, validation,
solver execution, ProjectSchema, persistence, issue, release, tag, asset,
export, report, clipboard, open-folder, and certification actions remain
disabled or future-only.

## 21. GUI Acceptance Design Relationship

The OSW-EXP-117 GUI file-dialog preview may become a caller of a future
acceptance view-model or controller, but only after a separate implementation
gate. The GUI relationship must remain:

- explicit user-selected file preview first;
- reader diagnostics before view-model preview;
- no native dialog on construction;
- no CLI subprocess bridge;
- no direct GUI JSON parsing;
- no acceptance button in this design gate;
- no runtime reload acceptance without a later gate;
- no ProjectSchema mutation;
- no discovery, validation, solver execution, automatic activation, trust
  restoration, issue/release/tag/asset mutation, or certification claim.

The existing reload panel remains a pure view-model renderer unless a future
gate changes that boundary with tests.

## 22. CLI Acceptance Design Relationship

The OSW-EXP-115 CLI explicit-path preview may become a caller of future
acceptance semantics, but only through a separate acceptance CLI design and
implementation gate.

CLI acceptance must remain explicit and must not be inferred from exit code,
text output, JSON output, or reader success. CLI acceptance must not add default
paths, background reload, directory scans, network fetches, plugin package
imports, GUI file dialogs, ProjectSchema mutation, persistence writes, live
discovery, validation execution, solver execution, dependency install/uninstall,
automatic activation, trust restoration, issue/release/tag/asset mutation, or
certification claims.

## 23. Persistence/State Writer Relationship

The state writer writes explicit local UX state files after caller-supplied
path, acknowledgement, and preflight checks. Reload acceptance may consume only
reader-safe mappings from that payload family and may copy reviewed state into
session UX review state.

Acceptance does not repair, rewrite, migrate, replace, delete, or persist
writer-produced files. Acceptance is not a state writer. Acceptance performs no
persistence write and creates no runtime state file, settings file, schema file,
export file, report file, or reloadable bundle.

## 24. ProjectSchema Relationship

There is no ProjectSchema mutation. Accepted reload state is not ProjectSchema
state. Accepted reload state is not project validation evidence.

Future ProjectSchema integration requires a separate gate with preview,
migration, rollback, docs, tests, and explicit user/caller confirmation.

## 25. Live Optional Validation Issues Relationship

Issues `#6` through `#11` remain open. Reload acceptance does not close issues.
Accepted reload state is not live optional validation. Skipped-missing remains
skipped-missing. Prepared-machine validation remains a separate gate.

Future acceptance must not mark issues ready to close, mutate issue state,
mutate release state, edit tags, edit assets, or claim public validation
evidence.

## 26. Diagnostics Reserved

Future implementation may reserve `OSPMG_RELOAD_ACCEPTANCE_*` diagnostics:

- `OSPMG_RELOAD_ACCEPTANCE_DESIGN_ONLY`
- `OSPMG_RELOAD_ACCEPTANCE_NOT_IMPLEMENTED`
- `OSPMG_RELOAD_ACCEPTANCE_EXPLICIT_ACTION_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_READER_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_SAFE_MAPPING_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_VIEWMODEL_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_ACK_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_ACK_EXPIRED`
- `OSPMG_RELOAD_ACCEPTANCE_SCHEMA_UNSUPPORTED`
- `OSPMG_RELOAD_ACCEPTANCE_MIGRATION_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_REDACTION_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_SECRET_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_RELOAD_ACCEPTANCE_CONFLICT_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_UNSAFE_CLAIM_BLOCKED`
- `OSPMG_RELOAD_ACCEPTANCE_SESSION_SCOPED`
- `OSPMG_RELOAD_ACCEPTANCE_PROJECT_SCHEMA_BOUNDARY`
- `OSPMG_RELOAD_ACCEPTANCE_NOT_VALIDATION`
- `OSPMG_RELOAD_ACCEPTANCE_NOT_VALIDATION_FAILURE`
- `OSPMG_RELOAD_ACCEPTANCE_NOT_TRUST_RESTORE`
- `OSPMG_RELOAD_ACCEPTANCE_NOT_AUTOMATIC_ACTIVATION`
- `OSPMG_RELOAD_ACCEPTANCE_NO_DISCOVERY_EXECUTION`
- `OSPMG_RELOAD_ACCEPTANCE_NO_PLUGIN_IMPORT`
- `OSPMG_RELOAD_ACCEPTANCE_NO_VALIDATION_EXECUTION`
- `OSPMG_RELOAD_ACCEPTANCE_NO_SOLVER_EXECUTION`
- `OSPMG_RELOAD_ACCEPTANCE_NO_PERSISTENCE_WRITE`
- `OSPMG_RELOAD_ACCEPTANCE_NO_ISSUE_CLOSURE`
- `OSPMG_RELOAD_ACCEPTANCE_NO_RELEASE_MUTATION`
- `OSPMG_RELOAD_ACCEPTANCE_NO_CERTIFICATION`
- `OSPMG_RELOAD_ACCEPTANCE_FUTURE_GATE`

Diagnostics are acceptance-review diagnostics only. They are not validation
success, validation failure, trust restoration, activation, issue closure,
release mutation, or certification.

## 27. Security And Privacy Review

Acceptance treats every user-selected or plugin-originated reload payload as
untrusted, potentially hostile data:

- explicit user/caller action only;
- reader-bounded file size and parsing before acceptance;
- no raw path leak;
- no secret leak;
- no remote URL fetch;
- no plugin package import;
- no script execution;
- no solver execution;
- no dynamic import from payload content;
- no ProjectSchema mutation;
- no automatic activation;
- no trust restoration;
- reader and view-model diagnostics use redacted context;
- malicious payload claims are blocked as data, not executed as instructions.

Size, encoding, JSON shape, duplicate-key, schema, redaction, unsafe-claim,
stale-source, conflict, acknowledgement, and evidence policies remain enforced
before future acceptance.

## 28. Future Implementation Test Plan

Future OSW-EXP-119 and later implementation gates should test:

- unavailable/no-preview state;
- reader-blocked state;
- missing safe mapping blocks acceptance;
- view-model blocker blocks acceptance;
- explicit user/caller action required;
- required acknowledgements;
- acknowledgement expiry;
- accepted state is session scoped;
- accepted state is not trusted;
- selected-file display and sources remain redacted;
- reader payload hash/fingerprint staleness;
- schema/migration blockers;
- redaction/privacy blockers;
- stale-source/re-preview blockers;
- conflict/shared-stack blockers;
- unsafe-claim blockers;
- evidence/history retention;
- skipped-missing preservation;
- disabled/future action states;
- GUI relationship without direct JSON parsing, CLI subprocess use, or
  ProjectSchema mutation;
- CLI relationship without exit-code validation semantics or default paths;
- no persistence write;
- no output files;
- no reloadable bundle;
- no clipboard/report/open-folder behavior;
- no discovery, validation, solver execution, dependency install/uninstall,
  automatic activation, trust restoration, issue/release/tag/asset mutation, or
  certification claim.

## 29. Future Gates

Future gates remain separate:

- `OSW-EXP-119_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_VIEWMODEL`
- `OSW-EXP-120_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_GUI_DESIGN`
- `OSW-EXP-121_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_GUI_IMPLEMENTATION`
- `OSW-EXP-122_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_CLI_DESIGN`
- `OSW-EXP-123_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_CLI_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` if a prepared
  machine is available

Runtime reload acceptance, activation review, discovery refresh, ProjectSchema
integration, validation, issue/release workflows, export/report integration,
persistence writes, reloadable bundles, and certification remain future-gated.
