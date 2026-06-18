# FEASpec human review record model

## Status

- Experimental record model implemented.
- No GUI implementation.
- CLI record commands are implemented separately as a no-run JSON workflow.
- No result import implementation.
- No run gate implementation.
- No solver execution.

This gate adds a data boundary under `src/osw/experimental/feaspec/` for
capturing reviewed FEASpec decisions. It does not approve execution by itself
and does not persist ProjectSchema records.

## Release Context

`v0.1.4-rc1` is a public prerelease. This work is post-release development on
`develop` and does not edit the public release, mutate tags, upload assets,
close issues, install solvers, or run live optional validation.

The current package and CLI version remain `0.1.4rc1`.

## Package Paths

The experimental model is scoped to:

- `src/osw/experimental/feaspec/human_review.py`
- `src/osw/experimental/feaspec/human_review_io.py`
- `src/osw/experimental/feaspec/human_review_errors.py`
- `src/osw/experimental/feaspec/__init__.py`

The model layer imports only lightweight Python standard-library helpers and
the local FEASpec human-review error types. It does not import GUI modules,
runner modules, solver adapter modules, subprocess APIs, VLM providers, API
clients, credential helpers, or ProjectSchema persistence code.

## Public API

The record model exposes:

- `HumanReviewState`
- `HumanReviewAction`
- `ReviewDiagnosticReference`
- `AcceptedWarning`
- `DiagnosticDecision`
- `HumanReviewSummary`
- `FEASpecHumanReviewValidationResult`
- `FEASpecHumanReviewRecord`
- `create_human_review_record`
- `validate_human_review_record`
- `summarize_human_review_record`
- `explain_human_review_record`
- `parse_human_review_record_dict`
- `human_review_record_from_dict`
- `human_review_record_to_dict`
- `load_human_review_record`
- `dump_human_review_record`

These APIs are experimental and preserve review evidence for the CLI record
workflow plus later GUI, export, run-gate, and result-import surfaces. They are
not a solver execution API.

## Review States

The model records these states:

- `unreviewed`
- `needs_changes`
- `rejected`
- `approved_for_no_run_export`
- `approved_for_installed_only_run_request`

`approved_for_no_run_export` means the reviewed FEASpec evidence can be used by
future no-run export surfaces when all validation gates pass. It does not mean
CalculiX has run.

`approved_for_installed_only_run_request` records reviewer intent to ask a
future installed-only run gate to proceed. The run gate remains separate and
must still check installed `ccx`, bundle metadata, reviewed README status,
path isolation, timeout policy, and user authorization.

## Review Actions

The model records these actions:

- `mark_needs_changes`
- `reject`
- `approve_no_run_export`
- `request_installed_only_run`
- `accept_warning`
- `reject_diagnostic`
- `add_note`

Actions map to record state through `create_human_review_record` unless a
caller supplies an explicit state for parsing stored data.

## Record Fields

`FEASpecHumanReviewRecord` preserves:

- schema version;
- record id;
- source FEASpec id;
- reviewer identity;
- reviewed timestamp supplied by the caller;
- review state and action;
- notes;
- accepted warnings with explicit reasons;
- diagnostic decisions;
- validator report summary;
- validator report hash;
- bridge summary;
- case-plan summary;
- export preview summary;
- export write summary;
- provenance metadata;
- acknowledgement flags;
- solver execution authorization intent;
- solver execution performed flag.

Timestamps are caller-provided. The model does not generate timestamps, create
directories, mutate project files, or infer reviewer identity from the local
machine.

## Approval Rules

Validation always requires:

- reviewer identity;
- reviewed timestamp;
- source FEASpec id;
- review action;
- review state;
- `solver_execution_performed == false`.

Approval records additionally require a validator report summary and validator
report hash. Needs-changes and rejected records may be saved without validator
evidence so reviewers can record incomplete or blocked review outcomes.

Approval for no-run export is blocked when validator summaries report blockers
or errors. Accepted warnings require a reason. Blocker diagnostics cannot be
accepted away.

Installed-only run request records require:

- no-run export review acknowledgement;
- limitations acknowledgement;
- acknowledgement that the actual run gate remains separate;
- explicit solver execution authorization intent;
- `solver_execution_performed == false`.

The model can record reviewer intent for a future installed-only run request,
but it cannot run a solver and cannot mark solver execution as performed.

## IO Behavior

`human_review_io.py` provides JSON-only helpers:

- `load_human_review_record(path)`
- `dump_human_review_record(record, path, overwrite=False)`

The helpers require `.json` paths. Writes refuse overwrite unless
`overwrite=True`. Writes do not create parent directories implicitly.

The JSON helpers serialize model data only. They do not write export bundles,
solver decks, ProjectSchema files, release assets, credentials, logs, or result
artifacts.

## Relationship To Human Review CLI

The [FEASpec human review CLI approval](feaspec_human_review_cli_approval.md)
commands use this record model to create, validate, and summarize JSON review
records:

- `feaspec-human-review-create`
- `feaspec-human-review-validate`
- `feaspec-human-review-summary`

Those commands are a record-only workflow. They may write one explicit review
JSON file for `create`, but they do not implement a GUI, result importer, run
gate, SolverAdapter handoff, runner handoff, subprocess path, ProjectSchema
mutation, VLM API, dependency install, or solver execution.

## Safety Boundary

The record model is a review evidence boundary:

- no GUI implementation;
- no solver-executing CLI approval;
- no result import implementation;
- no run gate implementation;
- no solver execution;
- no SolverAdapter or runner call;
- no subprocess or external command invocation;
- no ProjectSchema mutation;
- no VLM API;
- no credentials;
- no bundled solver;
- no certification.

Human review data can support future commands and UI panels, but every
mutation, export, run, and import action remains a separate gate with separate
preconditions.

## Relationship To CLI Preview And Write

Existing FEASpec CalculiX preview/write commands remain no-run boundaries. The
human-review CLI can persist a separate review JSON record from validator,
bridge, case-plan, preview, and write summaries, but export preview/write do
not run solvers and do not convert a review record into execution permission.

## Relationship To Run Gate

Run gate remains separate.

Issue `#8` remains open until installed-only validation passes on a prepared
machine. The record model does not validate local `ccx`, does not invoke
CalculiX, does not close issue `#8`, and does not convert a review record into
permission for automatic execution.

Any future installed-only run gate must verify reviewed no-run artifact
metadata, installed solver availability, explicit authorization, timeout
policy, isolated working directory, log capture, and artifact classification.

## Relationship To Result Import

Result import remains a future gate. The review record can provide provenance
for imported result summaries later, but the current model does not inspect
`.dat`, `.frd`, `.sta`, logs, manifests, or result directories. It does not
create ResultDataset records.

## Non-Goals

- No GUI implementation.
- No solver-executing CLI approval implementation.
- No result import implementation.
- No run gate implementation.
- No CalculiX execution.
- No SolverAdapter integration.
- No runner integration.
- No subprocess or external command invocation.
- No ProjectSchema mutation.
- No VLM provider or API integration.
- No credentials.
- No topology optimization.
- No Abaqus exporter.
- No industrial certification.
- No bundled solver.
- No release edit, release publish, asset upload, tag push, or issue closure.

## Next Implementation Slices

Possible later gates:

- `OSW-EXP-020_FEASPEC_HUMAN_REVIEW_CLI_APPROVAL`
- `OSW-EXP-021_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_DESIGN`
- `OSW-EXP-022_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_VIEWMODEL`
- `OSW-EXP-023_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_IMPLEMENTATION`
- `OSW-EXP-024_FEASPEC_HUMAN_REVIEW_GUI_SAVE_INTEGRATION`
- `OSW-EXP-025_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`

Those gates must preserve the current boundary: review record creation does not
run solvers, and solver execution must remain installed-only, explicit, and
separate.

The
[FEASpec human review GUI dialog design](feaspec_human_review_gui_dialog_design.md)
is the first GUI-facing follow-up. It is a design-only contract for future
dialog entry points, panels, warning acceptance, approval gating, and record
preview; it does not add GUI source, result import, run-gate behavior,
ProjectSchema mutation, SolverAdapter or runner calls, VLM APIs, dependency
installation, or solver execution.

The
[FEASpec human review GUI dialog view-model](feaspec_human_review_gui_dialog_viewmodel.md)
adds a pure Python binding layer around this record model. It constructs
deterministic dialog state, action availability, diagnostic rows, warning rows,
record previews, and save plans without writing files or importing GUI, solver,
runner, exporter, renderer, VLM, credential, or ProjectSchema mutation paths.

The
[FEASpec human review GUI dialog implementation](feaspec_human_review_gui_dialog_implementation.md)
adds the first read-only PySide6 dialog that displays this evidence. The dialog
does not save review records, open file dialogs, import results, request or run
CalculiX, call SolverAdapter or runner code, mutate ProjectSchema, add VLM
APIs, install dependencies, close issue `#8`, or execute solvers.
