# Optional Solver Plugin Manifest Reload Acceptance CLI Design

## 1. Status

Design-only.

This gate adds no reload acceptance CLI implementation, no CLI source edits, no
GUI source edits, no runtime source edits, no file-reader source edits, no reload
view-model source edits, no reload acceptance view-model source edits, no
acceptance CLI commands, no acceptance flags, no acceptance callbacks, no
persistence writes, no ProjectSchema mutation, and no runtime reload acceptance.

This gate also adds no file IO, no file reading, no file parsing, no reader
invocation, no GUI behavior, no GUI subprocess use, no CLI subprocess use, no
default reload path, no background reload, no directory scan, no network fetch,
no plugin package import, no reloadable bundle creation, no export file
creation, no report file creation, no clipboard behavior, no report attachment,
no open-output-folder behavior, no live discovery, no passive refresh, no
validation execution, no solver execution, no dependency installation, no
dependency uninstall, no solver uninstall, no automatic activation, no trust
restoration, no issue mutation, no issue closure, no release mutation, no tag
mutation, no asset mutation, no version bump, no validation-pass claim, no
validation-fail claim, no issue-closure claim, no bundled-solver claim, and no
certification claim.

This document is not authorization to accept runtime reload state. OSW-EXP-123
is the earliest future gate that may implement a CLI acceptance review surface,
and that gate still must preserve stdout-first review, disabled/future unsafe
actions, and explicit non-action flags.

## 2. Purpose

The purpose is to define future CLI semantics for reload acceptance review. The
future CLI should make `OptionalSolverPluginManifestReloadAcceptanceViewModel`
records inspectable in text and machine-readable output without creating
accepted runtime state, writing files, mutating projects, or implying validation
evidence.

The design keeps the OSW-EXP-115 explicit-path reload preview CLI separate from
future reload acceptance review. Reader and reload preview success can feed an
acceptance view-model, but a future acceptance CLI renderer must not infer trust,
activation, validation, persistence, release, or issue state from that preview.

## 3. Current State Before CLI Acceptance

- OSW-EXP-113 provides an explicit-path reload file reader that reads one local
  state-writer UX state file only when a caller supplies the path.
- OSW-EXP-115 provides `load-preview --path` for reader-first reload preview.
- OSW-EXP-117 provides an explicit GUI file-dialog preview wrapper.
- OSW-EXP-118 defines reload acceptance semantics as future explicit reviewed
  preview to session-review state.
- OSW-EXP-119 provides the pure reload acceptance view-model.
- OSW-EXP-121 provides a view-model-only GUI acceptance review panel.
- No acceptance CLI command exists.
- No runtime reload acceptance exists.
- No persistence write exists.
- No ProjectSchema mutation exists.

User/plugin files remain untrusted by default. Built-ins remain authoritative by
default. Skipped-missing remains skipped-missing. Issues `#6` through `#11`
remain open and separate.

## 4. Definition Of Reload Acceptance CLI Review

Reload acceptance CLI review is a future stdout-first rendering surface over
already-built `OptionalSolverPluginManifestReloadAcceptanceViewModel` records.
It reports whether a supplied acceptance view-model is unavailable, blocked,
ready for a future acceptance action, accepted for session review, or requiring
future review.

The CLI review may eventually display acceptance summary/readiness,
preconditions and blockers, acknowledgement state, acknowledgement expiry,
accepted-state scope, reader/preview provenance, schema/migration state,
redaction/privacy state, candidate lifecycle state, stale-source/re-preview
state, conflict/shared-stack state, unsafe claims, evidence/history,
`OSPMG_RELOAD_ACCEPTANCE_*` diagnostics, non-action flags, disabled/future
actions, and exit semantics.

Reload acceptance CLI review must not perform runtime reload acceptance, read
files directly, invoke the reader, call GUI code, parse CLI preview output as
policy, persist state, mutate ProjectSchema, activate candidates, restore trust,
run discovery, run validation, execute solvers, install or uninstall
dependencies, mutate issues/releases/tags/assets, create output files, or claim
certification.

## 5. Non-Meaning Of Reload Acceptance CLI Review

CLI acceptance review is not reload acceptance implementation. CLI acceptance
review is not runtime reload acceptance. CLI acceptance review is not validation
success. CLI acceptance review is not validation failure. CLI acceptance review
is not trust restoration. CLI acceptance review is not automatic activation. CLI
acceptance review is not discovery success. CLI acceptance review is not
dependency installation. CLI acceptance review is not dependency uninstall. CLI
acceptance review is not solver uninstall. CLI acceptance review is not solver
execution. CLI acceptance review is not ProjectSchema mutation. CLI acceptance
review is not persistence write. CLI acceptance review is not file IO. CLI
acceptance review is not reader invocation. CLI acceptance review is not GUI
behavior. CLI acceptance review is not GUI subprocess use. CLI acceptance review
is not issue closure. CLI acceptance review is not issue mutation. CLI
acceptance review is not release mutation. CLI acceptance review is not tag
mutation. CLI acceptance review is not asset mutation. CLI acceptance review is
not report generation. CLI acceptance review is not export file creation. CLI
acceptance review is not reloadable bundle creation. CLI acceptance review is
not validation-pass claim, validation-fail claim, issue-closure claim,
bundled-solver claim, or certification claim.

Reader success means only that the reader produced safe review data. Reload
view-model readiness means only that the mapping is coherent for review. Future
acceptance view-model readiness means only that a later explicit acceptance
action may be considered after all acknowledgements, blockers, stale-source,
conflict, and unsafe-claim checks are visible.

## 6. Future Command Vocabulary

The following vocabulary is reserved for a future implementation gate only. It is
not implemented by this design gate:

- acceptance summary review;
- acceptance blockers review;
- acceptance acknowledgements review;
- acceptance acknowledgement-expiry review;
- acceptance accepted-state-scope review;
- acceptance provenance review;
- acceptance schema/migration review;
- acceptance redaction/privacy review;
- acceptance candidate-lifecycle review;
- acceptance stale-source/re-preview review;
- acceptance conflict/shared-stack review;
- acceptance unsafe-claim review;
- acceptance evidence/history review;
- acceptance diagnostics review;
- acceptance non-action-flags review;
- acceptance disabled/future-actions review;
- future accept-for-session-review action, disabled unless a later gate
  explicitly implements it.

The future command vocabulary must remain stdout-first and review-first. It must
not add default reload paths, hidden file reads, background reload, directory
scan, network fetch, plugin package import, GUI subprocess use, or automatic
acceptance.

## 7. Future CLI User Flow

The future CLI user flow is:

1. A caller obtains reload preview records from an existing reader/reload
   preview path such as OSW-EXP-115 `load-preview --path`.
2. A caller builds an `OptionalSolverPluginManifestReloadAcceptanceViewModel`
   from supplied in-memory records.
3. The future CLI renderer receives the acceptance view-model records directly.
4. The renderer prints text output by default and may print JSON when requested.
5. The renderer exits with a rendering status, not a validation status.
6. Any future accept-for-session-review action remains disabled/future-only until
   a separate implementation gate explicitly adds and tests it.

No flow step authorizes runtime reload acceptance, trust elevation, activation,
discovery, validation, solver execution, ProjectSchema mutation, persistence
writes, issue/release/tag/asset mutation, output creation, or certification.

## 8. Input Policy

The future CLI accepts only supplied in-memory acceptance view-model records or a
safe mapping already produced by such a view-model. It does not accept raw file
paths, raw file content, arbitrary JSON state files, GUI output, CLI preview
stdout, plugin package imports, directory roots, network URLs, ProjectSchema
objects, or persisted state files as acceptance input.

If a future implementation needs to combine explicit-path reload preview with
acceptance review, it must call the existing reader and reload preview
contracts through a separately tested gate and must keep reader diagnostics,
reload review diagnostics, and acceptance diagnostics distinct.

The future CLI must not independently reinterpret acceptance policy. The
acceptance view-model remains the policy source of truth.

## 9. Output Modes

Text output is the default. It should be concise, sectioned, and suitable for
stdout review in terminals and CI logs.

JSON output may be added for deterministic automation, but it must remain a
review artifact. JSON output must not be a reloadable bundle, runtime state file,
settings file, schema file, export file, report file, report attachment, release
asset, validation artifact, issue-closure artifact, or certification artifact.

No output mode may write files by default. Future file output, if ever needed,
requires a separate persistence/export/report gate.

## 10. Summary And Readiness Output

Summary/readiness output should show acceptance state, readiness,
ready-for-future-acceptance flag, accepted-for-session-review flag, preview
availability, missing acknowledgement count, blocker count, future activation
review required, future discovery-refresh review required, source trust labels,
and safety booleans.

The summary must state that readiness is future-only and not runtime acceptance,
not validation evidence, not validation failure, not trust restoration, not
automatic activation, not discovery success, not dependency installation, not
solver execution, not persistence write, and not ProjectSchema mutation.

## 11. Preconditions And Blockers Output

Preconditions/blockers output should list every blocker row, including missing
preview, reader blocked, reload view-model blocked, missing acknowledgement,
expired acknowledgement, unsupported schema, migration required, unredacted path,
secret-like value, stale-source/re-preview, conflict/shared-stack, unsafe claim,
trust policy change, source fingerprint change, and acceptance policy change.

Blockers are review instructions. They are not validation failure, issue closure,
release mutation, or certification evidence.

## 12. Acknowledgement Output

Acknowledgement output should list required acknowledgement ids, satisfied state,
missing state, expired state, blocking state, and explanation. It should include
review boundaries for acceptance_not_validation,
acceptance_not_validation_failure, acceptance_not_trust_restoration,
acceptance_not_automatic_activation, acceptance_not_discovery_success,
acceptance_not_dependency_install, acceptance_no_solver_execution,
acceptance_not_issue_closure, acceptance_not_release_mutation,
acceptance_not_certification, acceptance_not_persistence_write,
acceptance_not_project_schema_mutation, redaction_reviewed,
unredacted_paths_blocked, stale_source_requires_repreview,
untrusted_source_remains_untrusted, activation_review_required_after_acceptance,
no_discovery_execution, no_plugin_package_import, no_validation_execution,
no_solver_execution, trust_label_not_certification, and
persisted_acknowledgements_may_expire.

Acknowledgements do not validate, fail, reload, trust, activate, discover,
install, uninstall, execute, persist, mutate ProjectSchema, close issues, mutate
releases/tags/assets, create outputs, or certify anything.

## 13. Acknowledgement Expiry Output

Acknowledgement expiry output should show expiry reasons from the acceptance
view-model, including reload, source fingerprint change, schema version change,
unsafe-claim appearance, trust policy change, future discovery-refresh result,
file-reader policy change, GUI file-dialog policy change, CLI explicit-path
policy change, acceptance policy change, ProjectSchema policy change, and
validation issue state change.

Expired acknowledgement state blocks future acceptance and requires re-review. It
is not validation failure.

## 14. Accepted-State Scope Output

Accepted-state scope output should render supplied accepted-for-session-review
rows when present. It must state that accepted-for-session-review is
representation-only, bounded to session/review state, untrusted by default, not
persisted state, not ProjectSchema state, not runtime reload acceptance, not
validation evidence, not validation failure, not trust restoration, not
automatic activation, not discovery success, not dependency installation, not
solver execution, not issue closure, not release mutation, and not
certification.

The future CLI must not create, persist, or restore accepted state unless a later
gate explicitly implements that behavior with tests.

## 15. Reader And Preview Provenance Output

Reader and preview provenance output should render redacted target display,
reader status when supplied, source fingerprint, payload kind, payload schema
version, writer version, reader policy summary, generated-by display, caller
context, source labels, trust labels, and reload preview status.

Provenance is not trust. Hashes are not certification. CLI caller labels are not
validation evidence. User/plugin source remains untrusted by default unless it is
already a built-in OSW source.

## 16. Schema And Migration Output

Schema/migration output should show payload kind, schema version,
supported/unsupported state, migration-required state, payload-kind mismatch,
future migration policy, and the boundary between persistence schema and
ProjectSchema.

Unsupported schema and migration-required states block future acceptance.
Migration remains a separate gate. The future CLI writes no schema files.

## 17. Redaction And Privacy Output

Redaction/privacy output should show redacted selected-file display,
redaction-required state, redaction-reviewed acknowledgement state,
unredacted-path blockers, secret-like-value blockers, and sources whose display
was redacted.

The future CLI must not leak raw absolute paths, home directories, environment
variables, tokens, API keys, credentials, private keys, private network paths,
solver install paths, plugin install paths, or arbitrary external URLs.

## 18. Candidate Lifecycle Output

Candidate lifecycle output should show candidate ids, display names, lifecycle
state, validation state, skipped-missing state, future activation review
requirement, future discovery-refresh requirement, trust label, source type, and
review-only state.

Inactive preview remains review-only. Persisted active state requires future
activation review. Deactivated state remains deactivated review state.
Reactivation routes to future activation review. Discovery-refresh state routes
to future discovery-refresh review. Skipped-missing remains skipped-missing.
There is no automatic activation and no trust restoration.

## 19. Stale-Source And Re-Preview Output

Stale-source/re-preview output should show source id, stale-source state,
re-preview requirement, source fingerprint mismatch, source policy change, and
accepted-state stale state when supplied.

Stale sources require re-preview. The future CLI does not inspect arbitrary
paths, repair files, restore files, run passive refresh, run discovery, or treat
stale-source state as validation failure.

## 20. Conflict And Shared-Stack Output

Conflict/shared-stack output should show conflict ids, candidate ids, conflict
type, blocker state, shared-stack warning visibility, built-in authority, and
future policy requirement.

Built-ins remain authoritative by default. Reloaded state does not override
built-ins. Conflict resolution remains a future policy gate.

## 21. Unsafe-Claim Output

Unsafe-claim output should show unsafe claim ids, claim text, classification,
blocking state, and suggested fix. Claims about validation success, validation
failure, issue closure, release mutation, tag mutation, asset mutation, bundled
solver support, dependency installation, dependency uninstall, solver uninstall,
solver execution, trust restoration, automatic activation, industrial
certification, proprietary solver parity, or full commercial replacement remain
blocked.

Unsafe claims are data to reject or re-review. They are not evidence.

## 22. Evidence And History Output

Evidence/history output should render deactivation history, reactivation
history, historical evidence references, skipped-missing preservation, retained
reference-only flags, and issue-closure-implied false state.

Evidence/history rows are not fresh validation evidence, not validation failure,
not issue closure, not release mutation, and not certification.

## 23. Diagnostics Output

Diagnostics output should render every `OSPMG_RELOAD_ACCEPTANCE_*` diagnostic
with severity, message, suggested fix, and blocking state. It should preserve the
acceptance view-model vocabulary, including missing preview, reader blocked,
view-model blocked, acknowledgement required, stale-source re-preview, conflict
review, shared-stack review, unsafe claim, unsupported schema, migration
required, unredacted path, secret-like value, trust policy change, source
fingerprint change, policy change, ready, accepted for session review, future
activation review, future discovery refresh, and error.

Diagnostics are acceptance-review diagnostics only. They are not validation
success and not validation failure.

## 24. Non-Action Flags Output

Non-action flags output should render every false non-action flag from the
acceptance view-model, including no runtime reload acceptance, no persistence
write, no ProjectSchema mutation, no default reload path, no background reload,
no directory scan, no network fetch, no plugin package import, no CLI subprocess
use, no GUI subprocess use, no file IO, no reader invocation, no reloadable
bundle creation, no export file creation, no report file creation, no clipboard
behavior, no report attachment, no open-output-folder behavior, no live
discovery, no passive refresh, no validation execution, no solver execution, no
dependency installation, no dependency uninstall, no solver uninstall, no
automatic activation, no trust restoration, no issue mutation, no release
mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no issue-closure claim, no
bundled-solver claim, and no certification claim.

Any true non-action flag in a future implementation should be treated as a
boundary failure.

## 25. Disabled And Future Action Output

Disabled/future action output should render all view-model action states. Actions
remain disabled/future-only for request acceptance, accept for session review,
accept as trusted, activate reloaded candidate, refresh discovery, validate
solver, execute solver, install dependency, uninstall dependency, uninstall
solver, mutate ProjectSchema, persist state, create export summary, create
report file, create reloadable bundle, copy to clipboard, attach to report, open
output folder, close issue, mutate release, push tag, upload asset, claim
validation success, claim validation failure, and claim certification.

This design gate adds no enabled action, no acceptance flag, no acceptance CLI
command, and no callback.

## 26. Exit-Code Policy

Future exit codes must report CLI rendering/invocation status only:

- `0`: the review command rendered the supplied acceptance view-model
  successfully. It is not validation success, not validation failure, not
  runtime reload acceptance, not issue closure, not release mutation, and not
  certification.
- `2`: a future strict review mode may report that the supplied acceptance
  view-model is blocked or unavailable. It is not validation failure.
- other nonzero codes: CLI invocation, malformed supplied view-model, or
  rendering failure. They are not solver failure, validation failure, release
  failure, or issue-closure failure.

No exit code may imply bundled solver support, dependency installation,
automatic activation, trust restoration, ProjectSchema mutation, or prepared
machine validation.

## 27. Relationship To Reload Acceptance ViewModel

The future CLI consumes `OptionalSolverPluginManifestReloadAcceptanceViewModel`
as the sole acceptance review contract. It should render `to_mapping()` or
explicit records deterministically and must not mutate the view-model. It must
not edit reload acceptance view-model source.

## 28. Relationship To Reload Acceptance GUI Panel

The OSW-EXP-121 GUI panel and the future CLI should render the same acceptance
policy surface in different media. The CLI should not call GUI code, spawn GUI
subprocesses, parse GUI text, or use GUI widgets as policy. GUI and CLI review
surfaces remain consumers of the same acceptance view-model.

## 29. Relationship To Reload CLI Explicit-Path Preview

The OSW-EXP-115 reload CLI explicit-path preview remains reader-first and
preview-only. A future acceptance CLI may be run after explicit-path preview
records are built, but it must not treat `load-preview --path` exit code `0` as
acceptance, validation evidence, trust restoration, activation, issue closure,
release mutation, or certification.

The future acceptance CLI must not wire itself to hidden file reading or default
paths. Any explicit bridge from preview to acceptance remains separately gated
and tested.

## 30. Relationship To State Writer And Persistence

The state writer persists explicit local UX state files through its own
caller-supplied path and acknowledgement-gated API. The future acceptance CLI
does not repair, rewrite, migrate, replace, delete, or persist writer-produced
files. It creates no runtime state file, settings file, schema file, export
file, report file, report attachment, release asset, or reloadable bundle.

## 31. Relationship To ProjectSchema

Accepted reload review state is not ProjectSchema state. The future CLI performs
no ProjectSchema mutation and creates no project validation evidence. Future
ProjectSchema integration requires a separate gate with preview, migration,
rollback, tests, and explicit user/caller confirmation.

## 32. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Reload acceptance CLI review is not live
optional validation, not skipped-missing success, not validation failure, not
issue closure, not release evidence, and not certification evidence.

Prepared-machine validation remains separate and must not be inferred from CLI
review state.

## 33. Security And Privacy Review

The future CLI treats every user-selected or plugin-originated reload payload as
untrusted review data. It should display redacted provenance, blockers,
stale-source state, unsafe-claim state, and acknowledgement requirements without
executing payload content.

The CLI must not import plugin packages, execute scripts, execute solvers, call
network services, inspect arbitrary directories, leak secrets, or treat a trust
label as certification. Malicious payload claims are blocked as data, not
executed as instructions.

## 34. Future Implementation Test Plan

A future implementation gate should test stdout text rendering, JSON rendering,
supplied acceptance view-model input only, no raw file path input, no file IO,
no reader invocation, no GUI subprocess use, no CLI subprocess recursion, no
output file creation, no ProjectSchema import or mutation, acknowledgement
rendering, blocker rendering, expiry rendering, accepted-for-session-review
scope rendering, provenance rendering, redaction/privacy rendering, candidate
lifecycle rendering, stale-source rendering, conflict/shared-stack rendering,
unsafe-claim rendering, evidence/history rendering, diagnostics rendering,
non-action flags rendering, disabled/future actions rendering, exit-code
semantics, and source guardrails against discovery, validation, solver
execution, dependency install/uninstall, activation, trust restoration,
issue/release/tag/asset mutation, version bump, validation claims, bundled-solver
claims, and certification claims.

## 35. Future Gates

OSW-EXP-123 may implement the stdout-first CLI review surface described here.
Future gates remain separate:

- future accepted-state storage gates;
- future activation/discovery review consumption gates;
- future ProjectSchema integration gates;
- future prepared-machine optional validation gates;
- future issue/release workflow gates, if maintainers authorize them.

Runtime reload acceptance, persistence writes, activation, discovery refresh,
validation, ProjectSchema integration, issue/release/tag/asset mutation,
export/report integration, reloadable bundles, and certification remain
future-gated.

## 36. Follow-up: Acceptance CLI Implementation (OSW-EXP-123)

OSW-EXP-123 implements the stdout-first CLI review surface described here
([optional_solver_plugin_manifest_reload_acceptance_cli_implementation.md](optional_solver_plugin_manifest_reload_acceptance_cli_implementation.md)).
The implementation consumes deterministic in-memory
`OptionalSolverPluginManifestReloadAcceptanceViewModel` records only and renders
readiness, blockers, acknowledgements, expiry, diagnostics, non-action flags,
disabled/future actions, and safety guidance.

The implementation still accepts no `--path`, reads no files, invokes no
reader, calls no GUI code, uses no GUI subprocess, performs no runtime reload
acceptance, writes no persistence, mutates no ProjectSchema, runs no discovery,
validation, or solver execution, activates no candidates, restores no trust,
mutates no issues/releases/tags/assets, and claims no certification.
