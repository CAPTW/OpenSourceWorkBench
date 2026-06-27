# Optional solver plugin manifest state export summary design

## Status

Design-only.

No runtime behavior is added in this gate. This document defines the future safety
contract, UX flow, redaction model, summary content model, the
non-reloadable/export-bundle boundary, diagnostics, acknowledgement requirements,
and follow-up gates for optional solver plugin manifest state export summaries. It
is not implementation authorization and does not read as one.

Status boundaries:

- no runtime behavior added
- no runtime source behavior added
- no export implementation
- no file writes
- no export file creation
- no reloadable bundle creation
- no clipboard behavior
- no open-output-folder behavior
- no persistence implementation
- no settings file creation
- no project schema mutation
- no GUI export behavior
- no CLI export behavior
- no activation/deactivation/reactivation/discovery-refresh source mutation
- no automatic activation
- no trust restoration
- no file restoration
- no file rewrite
- no file deletion
- no dependency installation
- no dependency uninstall
- no solver uninstall
- no plugin package import
- no directory scan
- no network fetch
- no discovery execution
- no validation execution
- no solver execution
- no issue mutation
- no issue closure
- no release mutation
- no tag mutation
- no asset mutation
- no version bump
- no validation-pass claim
- no validation-fail claim
- no certification claim

## Purpose

Define future export-summary semantics for optional solver plugin manifest UX
state, while preserving the explicit-import, activation, deactivation,
reactivation, discovery-refresh, and persistence-design boundaries.

The purpose is to:

- define what future export summaries may include and what must be redacted or
  excluded
- preserve the OSW-EXP-079/080 activation boundaries
- preserve the OSW-EXP-081/085/086 deactivation boundaries
- preserve the OSW-EXP-087/088/089 reactivation boundaries
- preserve the OSW-EXP-082/083/084 discovery-refresh boundaries
- preserve the OSW-EXP-090 persistence-design boundaries
- make export summary distinct from persistence, reloadable state bundles,
  validation, trust restoration, plugin installation, solver installation, solver
  execution, issue closure, release mutation, and certification

An export summary is not persistence. An export summary is not automatically
reloadable. An export summary is not validation evidence. An export summary is not
trust restoration. An export summary is not issue closure.

## Current state before export summaries

- The explicit import GUI exists (OSW-EXP-077).
- Activation design/view-model/GUI exist (OSW-EXP-078/079/080).
- Deactivation design/view-model/GUI exist (OSW-EXP-081/085/086).
- Reactivation design/view-model/GUI exist (OSW-EXP-087/088/089).
- Discovery-refresh design/view-model/GUI exist (OSW-EXP-082/083/084).
- State persistence design exists (OSW-EXP-090), but no persistence implementation
  exists.
- All current surfaces remain non-persistent, non-installing, non-validating,
  non-executing, and issue/release-safe.
- User-selected and plugin-provided manifests remain untrusted and non-validating.

Issues `#6` through `#11` remain open. Package metadata remains `0.1.5rc1`. The
public prerelease remains `v0.1.5-rc1`.

## Definition of export summary

A future export summary is a redacted, human-reviewable, non-authoritative
representation of optional solver plugin manifest UX state, intended for human
review, bug reports, docs, support, or future handoff context.

An export summary may eventually include:

- redacted source labels
- source types and trust labels
- stack ids and display names
- preview/activation/deactivation/reactivation/discovery-refresh states
- acknowledgement status summaries
- diagnostic codes and messages
- conflict/shared-stack summaries
- stale-source/re-preview summaries
- unsafe-claim summaries
- evidence-retention summaries
- deactivation/reactivation history summaries
- schema/design version reference
- non-action flags
- limitations and non-certification statements

## What export summary must not include

An export summary must not include:

- raw absolute paths by default
- secrets, tokens, environment variables, home-directory paths, or API keys
- plugin code
- plugin package imports
- solver binaries
- dependency install instructions as executable actions
- validation-pass claims
- validation-fail claims
- issue-closure readiness claims
- certification claims
- release/tag/asset mutation commands
- arbitrary executable scripts
- unrestricted external URLs
- reloadable state semantics unless a future state-bundle gate defines them

## Export summary vs persistence vs reloadable bundle

- export summary: human-readable, redacted, review-focused, not necessarily
  reloadable
- persisted state: future versioned reloadable state, separately designed in
  OSW-EXP-090
- state bundle: a future explicit export/import artifact, not implemented here
- report attachment: a future optional human-readable artifact, not validation
  evidence

Clearly:

- export summary is not persistence
- export summary is not automatic reload
- export summary is not validation evidence
- export summary is not trust restoration

## Export preconditions

Future preconditions before export may be allowed:

- explicit user action (never automatic)
- visible redaction preview
- visible source/provenance labels
- visible trust labels
- visible non-validation warning
- visible non-install/non-execution warning
- visible issue/release non-action warning
- visible stale-source/re-preview warning
- visible unsafe-claim summary
- visible acknowledgement summary
- export target or copy surface explicitly chosen by a future gate
- no discovery/validation/solver execution required

## User acknowledgement model

Future export requires explicit acknowledgements before it can proceed:

- `export_not_validation`
- `export_not_persistence`
- `export_not_reloadable_bundle`
- `export_not_trust_restoration`
- `export_not_install`
- `export_no_solver_execution`
- `export_not_issue_closure`
- `export_not_release_mutation`
- `redaction_reviewed`
- `unredacted_paths_blocked`
- `stale_source_requires_repreview`
- `untrusted_source_remains_untrusted`
- `no_discovery_execution`
- `no_plugin_package_import`
- `trust_label_not_certification`

Acknowledgements are recorded as future in-memory state only. They do not grant
trust-by-default and do not constitute validation evidence.

## Redaction and privacy policy

- Raw absolute paths are not shown by default.
- Source references use basename, hash, source id, or caller-supplied display name
  where possible.
- Unredacted paths are blocked unless a future explicit gate defines review/allow
  behavior.
- No secrets, tokens, API keys, or environment variables.
- No home-directory paths unless explicitly reviewed by a future gate.
- Diagnostics should remain useful without leaking private paths.
- Source fingerprints, hashes, or ids must not become hidden trust signals.

## Summary content model

Conceptual sections (this does not create an export file format):

- header
- scope and non-action flags
- source/provenance summary
- candidate state summary
- activation summary
- deactivation summary
- reactivation summary
- discovery-refresh summary
- acknowledgement summary
- diagnostics summary
- conflicts/shared-stack summary
- stale-source/re-preview summary
- unsafe-claim summary
- evidence/history summary
- limitations
- issue/release non-action statement
- redaction report
- future-gate references

## Suggested text format and future formats

Future options, discussed without implementing:

- plain text summary
- Markdown summary
- JSON-like redacted diagnostic summary
- HTML report attachment
- clipboard preview
- project report section
- support bundle summary

Reloadable JSON/YAML state bundles require separate future gates.

## Source/trust/provenance model

Future labels:

- `source_type`: `built_in`, `user_selected_json_file`, `plugin_provided_manifest`,
  `future_imported_manifest`, `future_persisted_state`, `future_state_bundle`
- `trust_label`: `built_in`, `untrusted_user_file`, `untrusted_plugin_manifest`,
  `future_trusted_by_user`
- `export_summary_kind`: `session_summary`, `redacted_report_section`,
  `support_summary`, `future_state_bundle_summary`

Rules:

- the source reference must be redacted by default
- a trust label is not certification
- an exported summary is not validation evidence
- an exported summary is not trust restoration
- user-selected and plugin-provided manifests are untrusted by default

## State coverage model

Export summaries may mention: `inactive_preview`, `activation_ready`,
`active_candidate`, `deactivated`, `reactivation_requested`, `reactivation_ready`,
`future_activation_required`, discovery-refresh included/excluded state,
stale-source/re-preview required state, and persistence-designed-but-not-implemented
state.

Blocked interpretations:

- exported state directly to active candidate
- exported state directly to trusted source
- exported state directly to persistence
- exported state directly to reloadable bundle
- exported state directly to discovery execution
- exported state directly to validation execution
- exported state directly to dependency install
- exported state directly to solver execution
- exported state directly to issue closure
- exported state directly to release mutation
- exported state directly to certification claim

## Stale-source and re-preview policy

- Exported summaries must not silently trust old preview data.
- Missing, moved, or changed sources should be represented as stale or
  re-preview-required.
- A future implementation may compare fingerprints, mtimes, user-supplied source
  ids, or content hashes only if a separate gate defines it.
- This design gate does no file IO.
- An export summary must not restore, rewrite, or delete manifest files.

## Conflict and shared-stack policy

- Built-ins win by default.
- Exported user/plugin state must not imply built-in override.
- Duplicate stack ids must remain visible.
- Deactivated/reactivated/exported state must not hide conflicts.
- Conflicts should be shown as blocked or review-required until a future policy
  resolves them.

## Unsafe claim policy

Export summaries must not convert unsafe claims into accepted claims. Unsafe claims
include:

- bundled solver binaries
- automatic dependency install
- validation success
- validation failure reversal
- issue closure readiness
- industrial certification
- proprietary solver parity
- full OpenFOAM/ANSYS/MATLAB/Abaqus replacement
- solver execution during discovery/persistence/reload/export

## Validation and evidence policy

- An export summary is not validation success.
- An export summary is not validation failure.
- An export summary does not delete or rewrite historical evidence.
- An export summary may describe evidence limitations.
- Skipped-missing remains skipped-missing.
- An export summary must not close live validation issues.
- Prepared-machine validation remains a separate gate.
- Evidence references must preserve limitations and diagnostics.

## Relationship to state persistence design

- OSW-EXP-090 designs future persistence semantics.
- An export summary may summarize state but does not implement persistence.
- An export summary is not necessarily reloadable.
- Reloadable state bundles require separate design and implementation gates.
- This gate creates no schema file and writes no state.

## Relationship to activation view-model and GUI

- Activation state may be summarized.
- Exported activation-ready state must still require visible review in future use.
- An export summary must not silently activate candidates.
- This gate does not alter activation view-model or GUI source.

## Relationship to deactivation view-model and GUI

- Deactivation state and history may be summarized.
- Exported deactivation state is not file deletion or uninstall.
- An export summary must preserve evidence history and deactivation history.
- This gate does not alter deactivation view-model or GUI source.

## Relationship to reactivation view-model and GUI

- Reactivation state may be summarized.
- Exported reactivation-ready state is not automatic activation.
- Exported reactivation-ready state is not trust restoration.
- Reloaded or reused reactivation information must route through future activation
  review.
- This gate does not alter reactivation view-model or GUI source.

## Relationship to discovery-refresh view-model and GUI

- Discovery-refresh state may be summarized.
- Exported included/excluded state is not discovery execution.
- An export summary must not automatically run discovery.
- Deactivated candidates remain excluded or inactive unless future policy changes
  supplied state.
- This gate does not alter discovery-refresh view-model or GUI source.

## Relationship to explicit import GUI

- Explicit import preview does not imply export summary.
- An export summary must not bypass explicit import preview safety.
- Exported references to imported files must be redacted by default.
- Missing or changed sources require re-preview or future policy.

## Relationship to ProjectSchema

- No ProjectSchema mutation in this gate.
- An export summary must not be treated as project schema state.
- Project validation must not treat exported summaries as solver validation
  evidence.
- Future report attachment or project-local export support requires separate
  gates.

## Relationship to CLI

- No CLI behavior change in this gate.
- No CLI export-summary command.
- A future CLI export-summary design or implementation would require a separate
  gate.

## Relationship to GUI, report, and export

- No GUI export button in this gate.
- No clipboard behavior in this gate.
- No file dialog in this gate.
- No open-output-folder action in this gate.
- Future GUI/report export must be display-only or explicit-write gated.
- Export summaries are report/support evidence, not validation proof.

## Relationship to live optional validation issues

- Issues `#6` through `#11` remain open.
- An export summary is not live optional validation.
- An export summary must not mark issues ready to close.
- Skipped-missing remains skipped-missing.
- Prepared-machine validation remains a separate gate.

## Diagnostics reserved for future export summaries

Reserved design-only diagnostic code names (not implemented in this gate):

- `OSPMG_EXPORT_SUMMARY_NOT_IMPLEMENTED`
- `OSPMG_EXPORT_SUMMARY_ACK_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_NOT_VALIDATION`
- `OSPMG_EXPORT_SUMMARY_NOT_PERSISTENCE`
- `OSPMG_EXPORT_SUMMARY_NOT_RELOADABLE_BUNDLE`
- `OSPMG_EXPORT_SUMMARY_NOT_TRUST_RESTORE`
- `OSPMG_EXPORT_SUMMARY_NO_INSTALL`
- `OSPMG_EXPORT_SUMMARY_NO_SOLVER_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_NOT_ISSUE_CLOSURE`
- `OSPMG_EXPORT_SUMMARY_NOT_RELEASE_MUTATION`
- `OSPMG_EXPORT_SUMMARY_REDACTION_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_UNREDACTED_PATH_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_STALE_SOURCE_REPREVIEW_REQUIRED`
- `OSPMG_EXPORT_SUMMARY_UNTRUSTED_SOURCE`
- `OSPMG_EXPORT_SUMMARY_CONFLICT_BLOCKED`
- `OSPMG_EXPORT_SUMMARY_UNSAFE_CLAIM`
- `OSPMG_EXPORT_SUMMARY_EVIDENCE_RETAINED`
- `OSPMG_EXPORT_SUMMARY_HISTORY_RETAINED`
- `OSPMG_EXPORT_SUMMARY_NO_DISCOVERY_EXECUTION`
- `OSPMG_EXPORT_SUMMARY_NO_PLUGIN_IMPORT`
- `OSPMG_EXPORT_SUMMARY_FUTURE_GATE`

These names are reservations only. No diagnostic emitter, runtime constant, or GUI
handler is added in this gate.

## Future implementation test plan

A later implementation gate must add tests that verify:

- export is unavailable unless explicitly requested
- an export summary requires redaction review
- an unredacted path blocks export unless future policy allows it
- export does not silently trust stale sources
- export does not auto-activate candidates
- export does not restore trust
- export does not persist state
- export does not create reloadable bundles
- export does not install dependencies
- export does not run discovery
- export does not run validation
- export does not execute solvers
- export does not close issues
- export does not mutate releases/tags/assets
- the built-ins-win / shared-stack policy remains visible
- unsafe claims block or warn
- source references are redacted
- a trust label is not certification
- skipped-missing remains skipped-missing
- summary text includes limitations and non-actions

These are future tests. This gate adds only a focused docs test for this design
document and the related guardrail/risk/checklist/validation references.

## Non-actions

This gate explicitly does not:

- implement export behavior
- write files
- create export files
- create reloadable bundles
- add clipboard behavior
- add open-output-folder behavior
- implement persistence
- create settings files
- implement project schema mutation
- implement GUI export behavior
- implement CLI export behavior
- alter activation view-model or GUI source
- alter deactivation view-model or GUI source
- alter reactivation view-model or GUI source
- alter discovery-refresh view-model or GUI source
- restore, rewrite, or delete manifest files
- install dependencies
- uninstall dependencies
- uninstall solvers
- import plugin packages
- scan directories
- fetch network manifests
- run discovery
- run validation
- execute solvers
- mutate issues
- mutate releases
- create, move, delete, or push tags
- build or upload assets
- bump versions
- claim validation success
- claim validation failure
- claim issue closure
- claim bundled solvers
- claim certification

No runtime source, GUI source, view-model source, CLI source, loader source,
discovery source, plugin manager source, or ProjectSchema source is changed in
this gate. This design adds no validation-pass claim, no validation-fail claim, no
issue-closure claim, no bundled-solver claim, and no certification claim.
User-selected and plugin-provided manifests remain untrusted; deactivation and
reactivation history and historical validation evidence are retained;
skipped-missing optional validation remains neither pass nor failure, and issues
`#6` through `#11` stay open.

## Future gates

Proposed follow-up candidates, not implemented here:

- `OSW-EXP-092_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_VIEWMODEL`
- `OSW-EXP-093_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_SCHEMA_MODEL`
- `OSW-EXP-094_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_GUI_DESIGN`
- `OSW-EXP-095_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_GUI_IMPLEMENTATION`
- `OSW-EXP-096_OPTIONAL_SOLVER_PLUGIN_MANIFEST_PERSISTENCE_CLI_DESIGN`
- `OSW-EXP-097_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_VIEWMODEL`
- `OSW-EXP-098_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_GUI_DESIGN`
- `OSW-EXP-099_OPTIONAL_SOLVER_PLUGIN_MANIFEST_EXPORT_SUMMARY_GUI_IMPLEMENTATION`
- `OSW-VALID-OPTIONAL_PREPARED_MACHINE_MANIFEST_STATE_VALIDATION` (only if a
  prepared machine is available)

Numbering note: this continues the optional-solver plugin manifest cadence. State
persistence (OSW-EXP-090) and this export-summary design (091) are the two
state-handling design gates; persistence view-model/schema/GUI/CLI (092-096) and
export-summary view-model/GUI (097-099) are later, separately gated steps. If the
repo later re-reserves a different sequence, follow the repo's latest convention
and update this mapping. Export implementation, file writes, reloadable bundles,
persistence implementation, schema files, discovery integration, validation,
install/uninstall, solver execution, and any live validation remain separate, later
gates regardless of numbering.
