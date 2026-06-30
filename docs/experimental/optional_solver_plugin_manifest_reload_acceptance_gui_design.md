# Optional Solver Plugin Manifest Reload Acceptance GUI Design

## 1. Status

Design-only.

This gate adds no reload acceptance GUI implementation, no GUI source edits, no
runtime source edits, no CLI source edits, no file-reader source edits, no reload
view-model source edits, no reload acceptance view-model source edits, no
acceptance buttons, no acceptance callbacks, no acceptance CLI commands, no
persistence writes, no ProjectSchema mutation, and no runtime reload acceptance.

This gate also adds no default reload path, no background reload, no directory
scan, no network fetch, no plugin package import, no CLI subprocess use, no
reloadable bundle creation, no export file creation, no report file creation, no
clipboard behavior, no report attachment, no open-output-folder behavior, no live
discovery, no passive refresh, no validation execution, no solver execution, no
dependency installation, no dependency uninstall, no solver uninstall, no
automatic activation, no trust restoration, no issue mutation, no issue closure,
no release mutation, no tag mutation, no asset mutation, no version bump, no
validation-pass claim, no validation-fail claim, no bundled-solver claim, and no
certification claim.

This document is not runtime reload acceptance authorization. OSW-EXP-121
implements the view-model-only GUI review surface described here without adding
acceptance buttons, callbacks, persistence writes, ProjectSchema mutation,
validation, solver execution, issue/release mutation, or certification claims.

## 2. Purpose

The purpose is to define future GUI semantics for reload acceptance review. The
future panel connects `OptionalSolverPluginManifestReloadAcceptanceViewModel`
from OSW-EXP-119 to a PySide review surface without implementing that surface in
this gate.

The design preserves reload preview, reader, reload view-model, GUI file-dialog,
CLI, state writer, ProjectSchema, discovery, validation, issue/release, and
certification boundaries.

## 3. Current State Before GUI Acceptance

- The OSW-EXP-113 reload file reader exists and reads one explicit local
  state-writer UX state file into diagnostics plus a safe mapping.
- The OSW-EXP-107 reload view-model exists and consumes in-memory mappings only.
- The OSW-EXP-115 reload CLI explicit path exists and is stdout-first,
  reader-first, and preview-only.
- The OSW-EXP-117 reload GUI file-dialog preview exists and is reader-first,
  explicit-file, and review-only.
- The OSW-EXP-118 reload acceptance design exists.
- The OSW-EXP-119 reload acceptance view-model exists.
- Existing reload GUI surfaces are preview/review-only.
- OSW-EXP-121 adds a reload acceptance GUI review panel after this design, but
  the panel remains view-model-only and review-only.
- No acceptance buttons exist.
- No runtime reload acceptance exists.
- No ProjectSchema mutation exists.
- No persistence write exists.

User/plugin files remain untrusted by default. Built-ins remain authoritative by
default. Skipped-missing remains skipped-missing. Issues `#6` through `#11`
remain open and separate.

## 4. Definition Of Reload Acceptance GUI Review

Reload acceptance GUI review is a future read-only review surface over
`OptionalSolverPluginManifestReloadAcceptanceViewModel`. It displays acceptance
readiness, blockers, acknowledgements, expiry reasons, diagnostics,
accepted-for-session-review representation, and disabled/future actions.

It may eventually render acceptance summary/readiness, missing
acknowledgements, blocker rows, accepted-for-session-review state when supplied,
future activation/discovery review requirements, disabled/future actions, and an
explicit future acceptance affordance in a later gate.

It must not accept reload on preview success, accept reload on file selection,
accept reload as trusted, activate candidates, restore trust, run discovery, run
validation, execute solvers, mutate ProjectSchema, persist state automatically,
close issues, mutate releases/tags/assets, or claim certification.

## 5. Non-Meaning Of Reload Acceptance GUI Review

GUI acceptance review is not reload acceptance implementation. GUI acceptance
review is not runtime reload acceptance. GUI acceptance review is not validation
success. GUI acceptance review is not validation failure. GUI acceptance review
is not trust restoration. GUI acceptance review is not automatic activation. GUI
acceptance review is not discovery success. GUI acceptance review is not
dependency installation. GUI acceptance review is not dependency uninstall. GUI
acceptance review is not solver uninstall. GUI acceptance review is not solver
execution. GUI acceptance review is not ProjectSchema mutation. GUI acceptance
review is not persistence write. GUI acceptance review is not issue closure. GUI
acceptance review is not issue mutation. GUI acceptance review is not release
mutation. GUI acceptance review is not tag mutation. GUI acceptance review is
not asset mutation. GUI acceptance review is not report generation. GUI
acceptance review is not reloadable bundle creation. GUI acceptance review is
not validation-pass claim, validation-fail claim, issue-closure claim,
bundled-solver claim, or certification claim.

Reader success means only that the reader produced safe review data. Reload
view-model readiness means only that the mapping is coherent for review.
Acceptance GUI review means only that future GUI users can inspect the
acceptance view-model before any later explicit action gate exists.

## 6. Future GUI User Flow

The future GUI user flow is:

1. The user selects one explicit local state file through the existing reload
   GUI file-dialog preview.
2. The OSW-EXP-113 reader renders diagnostics before any view-model preview.
3. Only reader `safe_mapping` output feeds the reload view-model.
4. The existing reload panel renders reload preview sections.
5. A future acceptance GUI panel receives an already-built
   `OptionalSolverPluginManifestReloadAcceptanceViewModel`.
6. The panel renders readiness, blockers, acknowledgements, expiry, provenance,
   diagnostics, non-action flags, and disabled/future action states.
7. A later implementation gate may add an explicit acceptance affordance, but
   this design gate adds no acceptance buttons and no acceptance callbacks.

No flow step authorizes runtime reload, trust elevation, automatic activation,
discovery, validation, solver execution, ProjectSchema mutation, persistence
writes, issue/release/tag/asset mutation, output creation, or certification.

## 7. Input Policy

The future GUI accepts only supplied in-memory
`OptionalSolverPluginManifestReloadAcceptanceViewModel` records. It does not
accept paths, raw file content, JSON text, reader requests, CLI output, or
ProjectSchema state. It does not read persisted state files, parse persisted
state files, invoke the reader, call the CLI as a subprocess, import plugin
packages, scan directories, fetch network manifests, or create default reload
paths.

The GUI must not independently reinterpret reload policy. It must render the
acceptance view-model contract and use view-model diagnostics as the policy
source of truth.

## 8. Layout Model

The future panel should be a compact review surface with stable sections:

- summary/readiness;
- preconditions and blockers;
- acknowledgements;
- acknowledgement expiry;
- accepted-state scope;
- reader and preview provenance;
- schema/migration;
- redaction/privacy;
- candidate lifecycle;
- stale-source/re-preview;
- conflict/shared-stack;
- unsafe claims;
- evidence/history;
- diagnostics;
- non-action flags;
- disabled/future actions.

The panel should not hide blockers behind an action button. Blocking and
non-action sections should remain visible even when a preview is ready for a
future acceptance action.

## 9. Summary And Readiness Display

The summary/readiness display should render the acceptance state, readiness,
preview availability, ready-for-future-acceptance flag, missing acknowledgement
count, blocker count, accepted-for-session-review flag, future activation review
requirement, future discovery-refresh requirement, and all safety booleans.

The summary must state that readiness is future-only and not runtime acceptance,
not validation evidence, not validation failure, not trust restoration, not
automatic activation, not discovery success, not dependency installation, not
solver execution, not persistence write, and not ProjectSchema mutation.

## 10. Preconditions And Blockers Display

The preconditions and blockers display should list every
`ReloadAcceptanceBlockerRow`, including missing preview, reader blocked,
view-model blocked, missing acknowledgement, expired acknowledgement,
unsupported schema, migration required, unredacted path, secret-like value,
stale-source/re-preview, conflict/shared-stack, unsafe claim, trust policy
change, source fingerprint change, and acceptance policy change.

Blockers are instructions to re-review or defer. They are not validation failure
and do not imply issue closure, release mutation, or certification.

## 11. Acknowledgement Display

The acknowledgement display should render every required acknowledgement id,
satisfied state, missing state, expired state, blocker state, and description.
Rows should include boundaries that reload acceptance GUI review is not
validation, not validation failure, not trust restoration, not automatic
activation, not discovery success, not dependency installation, not dependency
uninstall, not solver uninstall, not solver execution, not issue closure, not
release mutation, not certification, not persistence write, and not ProjectSchema
mutation.

Acknowledgements are review controls. They do not validate, fail, reload, trust,
activate, discover, install, uninstall, execute, persist, mutate ProjectSchema,
close issues, mutate releases/tags/assets, create outputs, or certify anything.

## 12. Acknowledgement Expiry Display

The acknowledgement expiry display should show expiry reasons from the
acceptance view-model, including new reload preview, source fingerprint change,
schema version change, unsafe-claim appearance, trust policy change, future
discovery-refresh result, file-reader policy change, GUI file-dialog policy
change, CLI explicit-path policy change, acceptance policy change,
ProjectSchema policy change, and validation issue state change.

Expired acknowledgement state blocks future acceptance and requires re-review. It
is not validation failure.

## 13. Accepted-State Scope Display

The accepted-state scope display should render supplied
`ReloadAcceptanceAcceptedStateRow` values when present. It must state that
accepted-for-session-review is representation-only, session/review scoped,
untrusted by default, not persisted state, not ProjectSchema state, not
validation evidence, not validation failure, not automatic activation, not trust
restoration, not discovery success, not dependency installation, not solver
execution, not issue closure, not release mutation, and not certification.

The panel must not create or persist accepted state in this design gate.

## 14. Reader And Preview Provenance Display

The reader and preview provenance display should render redacted target display,
reader status when supplied, payload hash or safe source fingerprint display,
reader version, reader policy summary, payload kind, schema version, writer
version, generated-by display, caller context, source labels, and trust labels.

Provenance is not trust. Hashes are not certification. A CLI caller or GUI
caller label is not validation evidence. User/plugin source remains untrusted by
default unless it is already a built-in OSW source.

## 15. Schema And Migration Display

The schema/migration display should show payload kind, schema version,
supported/unsupported state, migration-required state, payload-kind mismatch, and
future migration policy notes.

Unsupported schema and migration-required states block future acceptance.
Migration remains a separate gate. Persistence schema is separate from
ProjectSchema. The GUI writes no schema files.

## 16. Redaction And Privacy Display

The redaction/privacy display should show redacted selected-file display,
redaction-required state, redaction-review state, unredacted-path blocker,
secret-like-value blocker, and any source whose display was redacted.

The GUI must not leak raw absolute paths, home directories, environment
variables, tokens, API keys, credentials, private keys, private network paths,
solver install paths, plugin install paths, or arbitrary external URLs. The
display must reinforce that redaction review happens before future acceptance.

## 17. Candidate Lifecycle Display

The candidate lifecycle display should render candidate ids, display names,
lifecycle state, validation state, skipped-missing state, future activation
review requirement, future discovery-refresh requirement, trust label, source
type, and review-only state.

Inactive preview remains review-only. Persisted active state requires future
activation review. Deactivated state remains deactivated review state.
Reactivation routes to future activation review. Discovery-refresh state routes
to future discovery-refresh review. Skipped-missing remains skipped-missing.
There is no automatic activation and no trust restoration.

## 18. Stale-Source And Re-Preview Display

The stale-source/re-preview display should show source id, stale-source state,
re-preview requirement, source fingerprint mismatch, source policy change, and
accepted-state stale state when supplied.

Stale sources require re-preview. The GUI does not inspect source paths, repair
files, restore files, run passive refresh, run discovery, or treat stale-source
state as validation failure.

## 19. Conflict And Shared-Stack Display

The conflict/shared-stack display should show conflict ids, candidate ids,
conflict type, blocker state, shared-stack warning visibility, built-in
authority, and future policy requirement.

Built-ins remain authoritative by default. Reloaded state does not override
built-ins. Conflict resolution remains a future policy gate.

## 20. Unsafe-Claim Display

The unsafe-claim display should show unsafe claim ids, claim text, classification,
blocker state, and suggested fix. Claims about validation success, validation
failure, issue closure, release mutation, tag mutation, asset mutation, bundled
solver support, dependency installation, dependency uninstall, solver uninstall,
solver execution, trust restoration, automatic activation, industrial
certification, proprietary solver parity, or full commercial replacement remain
blocked.

Unsafe claims are data to reject or re-review. They are not evidence.

## 21. Evidence And History Display

The evidence/history display should render deactivation history, reactivation
history, historical evidence references, skipped-missing preservation, retained
reference-only flags, and issue-closure-implied false state.

Evidence/history rows are not fresh validation evidence, not validation failure,
not issue closure, not release mutation, and not certification.

## 22. Diagnostics Display

The diagnostics display should render every `OSPMG_RELOAD_ACCEPTANCE_*`
diagnostic with severity, message, suggested fix, and blocking state. It should
preserve the acceptance view-model diagnostic vocabulary, including missing
preview, reader blocked, view-model blocked, acknowledgement required,
stale-source re-preview, conflict review, shared-stack review, unsafe claim,
unsupported schema, migration required, unredacted path, secret-like value, trust
policy change, source fingerprint change, policy change, ready, accepted for
session review, future activation review, future discovery refresh, and error.

Diagnostics are acceptance-review diagnostics only. They are not validation
success and not validation failure.

## 23. Non-Action Flags Display

The non-action flags display should render every false non-action flag from
`ReloadAcceptanceNonActionFlags`, including no runtime reload acceptance, no
persistence write, no ProjectSchema mutation, no default reload path, no
background reload, no directory scan, no network fetch, no plugin package
import, no CLI subprocess use, no reloadable bundle creation, no export file
creation, no report file creation, no clipboard behavior, no report attachment,
no open-output-folder behavior, no live discovery, no passive refresh, no
validation execution, no solver execution, no dependency installation, no
dependency uninstall, no solver uninstall, no automatic activation, no trust
restoration, no issue mutation, no release mutation, no tag mutation, no asset
mutation, no version bump, no validation-pass claim, no validation-fail claim,
no issue-closure claim, no bundled-solver claim, and no certification claim.

Any true non-action flag in a future implementation should be treated as a
boundary failure.

## 24. Disabled And Future Action Display

The disabled/future action display should render all view-model action states.
Actions remain disabled/future-only for request acceptance, accept for
session-review, accept as trusted, activate reloaded candidate, refresh
discovery, validate solver, execute solver, install dependency, uninstall
dependency, uninstall solver, mutate ProjectSchema, persist state, create export
summary, create report file, create reloadable bundle, copy to clipboard, attach
to report, open output folder, close issue, mutate release, push tag, upload
asset, claim validation success, claim validation failure, and claim
certification.

This design gate adds no enabled action and no callback.

## 25. Relationship To Reload Acceptance ViewModel

The future GUI consumes `OptionalSolverPluginManifestReloadAcceptanceViewModel`
as the sole acceptance review contract. It should use `to_mapping()` or explicit
record attributes for deterministic rendering and should not mutate the
view-model. It must not edit reload acceptance view-model source.

## 26. Relationship To Reload GUI File-Dialog Preview

The OSW-EXP-117 reload GUI file-dialog preview remains reader-first and
preview-only. A future acceptance GUI panel may be shown after that preview
creates reload and acceptance view-model records, but it must not add file
opening behavior, direct JSON parsing, native dialog behavior beyond the
existing preview wrapper, CLI subprocess use, or runtime reload acceptance.

## 27. Relationship To Reload Panel

The OSW-EXP-109 reload panel remains a read-only renderer over reload
view-model records. The future acceptance GUI should be a separate review
surface or tab that renders acceptance view-model records and should not mutate
the existing reload panel, reload view-model, or preview data.

## 28. Relationship To Reload CLI

The OSW-EXP-115 reload CLI explicit path remains stdout-first and preview-only.
Future GUI acceptance must not infer acceptance from CLI exit codes, parse CLI
stdout as policy, or use the CLI as a GUI bridge. CLI acceptance remains a
future separate design and implementation path.

## 29. Relationship To State Writer And Persistence

The state writer persists explicit local UX state files only through its own
caller-supplied path and acknowledgement-gated API. The future acceptance GUI
does not repair, rewrite, migrate, replace, delete, or persist writer-produced
files. It creates no runtime state file, settings file, schema file, export
file, report file, or reloadable bundle.

## 30. Relationship To ProjectSchema

Accepted reload review state is not ProjectSchema state. The GUI performs no
ProjectSchema mutation and creates no project validation evidence. Future
ProjectSchema integration requires a separate gate with preview, migration,
rollback, tests, and explicit user/caller confirmation.

## 31. Relationship To Live Optional Validation Issues

Issues `#6` through `#11` remain open. Reload acceptance GUI review is not live
optional validation, not skipped-missing success, not validation failure, not
issue closure, not release evidence, and not certification evidence.

Prepared-machine validation remains separate and must not be inferred from GUI
review state.

## 32. Security And Privacy Review

The future GUI treats every user-selected or plugin-originated reload payload as
untrusted review data. The panel should display redacted provenance, blockers,
stale-source state, unsafe-claim state, and acknowledgement requirements without
executing payload content.

The GUI must not import plugin packages, execute scripts, execute solvers, call
network services, inspect arbitrary directories, leak secrets, or treat a trust
label as certification. Malicious payload claims are blocked as data, not
executed as instructions.

## 33. Future Implementation Test Plan

A future implementation gate should test inert construction, supplied
acceptance view-model rendering, no native dialog on construction, no reader
invocation, no CLI subprocess use, no file IO, no output file creation, no
ProjectSchema import or mutation, no acceptance buttons before explicitly
gated, acknowledgement/blocker/expiry rendering, accepted-for-session-review
display, redaction/privacy rendering, stale-source rendering, conflict rendering,
unsafe-claim rendering, evidence/history rendering, diagnostics rendering,
non-action flags rendering, disabled/future actions rendering, and source
guardrails against discovery, validation, solver execution, dependency
install/uninstall, activation, trust restoration, issue/release/tag/asset
mutation, version bump, validation claims, bundled-solver claims, and
certification claims.

## 34. Future Gates

OSW-EXP-121 implements the view-model-only GUI review surface described here.
Future gates remain separate:

- `OSW-EXP-122_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_CLI_DESIGN`
- `OSW-EXP-123_OPTIONAL_SOLVER_PLUGIN_MANIFEST_RELOAD_ACCEPTANCE_CLI_IMPLEMENTATION`
- future activation/discovery review consumption gates;
- future ProjectSchema integration gates;
- future prepared-machine optional validation gates.

Runtime reload acceptance, persistence writes, activation, discovery refresh,
validation, ProjectSchema integration, issue/release/tag/asset mutation,
export/report integration, reloadable bundles, and certification remain
future-gated.

## 35. Follow-up: Acceptance GUI Implementation (OSW-EXP-121)

OSW-EXP-121 implements the PySide review panel
`OptionalSolverPluginManifestReloadAcceptancePanel`
([optional_solver_plugin_manifest_reload_acceptance_gui_implementation.md](optional_solver_plugin_manifest_reload_acceptance_gui_implementation.md)).
The implementation consumes already-built
`OptionalSolverPluginManifestReloadAcceptanceViewModel` records only and renders
summary/readiness, blockers, acknowledgements, expiry reasons,
accepted-state scope, provenance, schema/migration, redaction/privacy,
candidate lifecycle, stale-source, conflict/shared-stack, unsafe claims,
evidence/history, trust/provenance, diagnostics, non-action flags,
disabled/future actions, and safety guidance.

The implementation adds no acceptance buttons, callbacks, runtime reload
acceptance, reader invocation, CLI bridge, file IO, persistence writes,
ProjectSchema mutation, discovery, validation, solver execution, activation,
trust restoration, issue/release/tag/asset mutation, output creation, or
certification claims.
