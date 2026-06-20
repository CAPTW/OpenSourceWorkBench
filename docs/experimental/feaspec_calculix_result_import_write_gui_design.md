# FEASpec CalculiX result import write GUI design

Status: design-only. No GUI write command implementation. No file dialog
implementation. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This design is post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Relationship to existing layers

The future GUI write workflow is a review surface over existing non-GUI
layers:

- `feaspec-calculix-result-import-preview` inspects an explicit result
  directory and returns preview-only import evidence.
- `feaspec-calculix-result-import-write` provides the current review-gated CLI
  behavior for plan-only and explicit write modes.
- The ResultDataset write plan model records output-directory intent, planned
  standard files, path safety, overwrite intent, artifact references,
  diagnostics, provenance, and limitations acknowledgement.
- The schema payload model builds deterministic in-memory ResultDataset,
  manifest, diagnostics, provenance, and review README payload records.
- The library writer writes the five standard ResultDataset review files only
  after the plan and schema payload are valid.
- The ResultDataset write view-model provides the first UI-agnostic state layer
  over those records. It computes panels, rows, action states, disabled
  reasons, acknowledgements, and lexical save-path plans, but it does not
  implement a GUI command, file dialog, or writer invocation.
- Existing human review GUI patterns use a pure view-model, explicit disabled
  reasons, visible safety copy, and mockable file-dialog providers.

This gate does not add a GUI command or alter the CLI, write plan, schema
payload, or library writer.

## Proposed GUI entry points

Future implementation may expose the workflow through:

- a result import preview panel that starts from an explicit result directory;
- a future ResultDataset write dialog opened from the preview evidence;
- a future project context action when a reviewed FEASpec CalculiX result
  import draft is already available.

All entry points must land in the same review-first state model and must not
write files until the future write action is enabled and explicitly confirmed.

## Workflow

The proposed user workflow is:

1. Select an explicit CalculiX result directory.
2. Inspect the result import preview, artifacts, parser diagnostics, and
   limitations.
3. Build the in-memory ResultDataset draft mapping.
4. Inspect planned files from the write plan.
5. Choose an explicit output directory.
6. Acknowledge limitations.
7. Acknowledge that the written files require human review first.
8. Optionally acknowledge overwrite for existing standard files.
9. Optionally request creation of the explicit output directory.
10. Perform a final review-first confirmation.
11. In a later implementation gate, invoke the future write action only if
    every precondition remains satisfied.

The design preserves plan-before-write behavior and keeps output selection
visible before any filesystem mutation.

## Panels and tabs

The future dialog should expose these panels or tabs:

- source/result directory;
- artifact summary;
- parser diagnostics;
- draft mapping;
- write plan;
- schema/manifest preview;
- safety/limitations;
- write action.

Panels should be inspectable without running CalculiX, copying artifacts, or
persisting ResultDataset files.

## Action states

The GUI state model should represent:

- `plan blocked`;
- `plan ready`;
- `write disabled`;
- `write ready with acknowledgements`;
- `write completed`;
- `write failed`.

The state names may be adapted to local enum style in a future implementation,
but the user-facing semantics should stay aligned with the CLI plan/write
boundary.

## Disabled reasons

The write action stays disabled when any of these conditions applies:

- missing result directory;
- missing result dir;
- missing output directory;
- missing output dir;
- blocked import plan;
- blocked write plan;
- missing acknowledgement;
- overwrite required;
- unsafe path.

Disabled reasons should be visible in the dialog, not hidden in logs or console
output.

## File dialog policy

The future file dialog policy is:

- require an explicit output directory;
- use no hidden defaults for write targets;
- remember successful selections only;
- create no parent directory implicitly unless the user explicitly requests the
  reviewed create-directory behavior;
- use no implicit parent creation unless explicitly requested;
- require overwrite confirmation before replacing existing standard files;
- reject unsafe internal paths such as `.git`, `.codex`, and release artifact
  output locations.

Choosing a directory should only update the pending write plan. The chooser
must not write files by itself.

## Acknowledgements

The dialog should require explicit acknowledgements for:

- limitations;
- review required;
- overwrite;
- create directory.

Acknowledgement state should be represented in the view-model and translated
to the same safety meaning as the CLI options:
`--acknowledge-limitations`, `--acknowledge-review-required`, `--overwrite`,
and `--create-dir`.

## CLI and GUI consistency

The GUI should stay consistent with the CLI by preserving:

- same modes;
- same acknowledgements;
- same safety language;
- same diagnostics;
- plan-only inspection before write;
- explicit write intent;
- the same required acknowledgement meanings;
- the same path and overwrite safety language;
- the same diagnostics and blocker semantics;
- exit/status semantics translated to visible UI state;
- `solver_execution_performed=false`;
- `artifact_copy_performed=false`;
- `release_mutation_performed=false`;
- `issue_mutation_performed=false`;
- `tag_mutation_performed=false`;
- `projectschema_mutation_performed=false`.

## Safety boundary

This design preserves:

- no solver execution;
- no CalculiX `ccx` invocation;
- no artifact copying by default;
- no release mutation;
- no issue mutation;
- no tag mutation;
- no SolverAdapter;
- no runner;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no dependency install or upgrade.

The future GUI write surface must not become a direct solver execution path or
a hidden project mutation path.

## Relationship to issue #8

The GUI write design does not validate live `ccx`. Issue `#8` remains open
until a separate prepared-machine live CalculiX validation gate records
passing evidence. Persisting reviewed ResultDataset files is not live solver
validation and must not close issue `#8`.

## Non-goals

- no implementation in this gate;
- no GUI command implementation in this gate;
- no file dialog implementation in this gate;
- no CLI behavior change;
- no library writer behavior change;
- no ResultDataset file write in this gate;
- no artifact copy implementation;
- no solver execution;
- no live `ccx` validation;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no certification;
- no industrial certification;
- no bundled solver.

## Future implementation tests

A future implementation should add tests for:

- dialog construction;
- view-model action states;
- disabled reasons;
- file-dialog mock behavior;
- acknowledgement gating;
- writer mock/call boundary;
- no solver execution.

The tests should also verify no artifact copy, no release/tag/asset mutation,
no issue mutation, no ProjectSchema mutation, no SolverAdapter/runner import,
and no subprocess invocation.

## Next implementation slices

- [FEASpec CalculiX result write view-model](feaspec_calculix_result_write_viewmodel.md)
  implemented `OSW-EXP-046_FEASPEC_RESULT_IMPORT_WRITE_GUI_VIEWMODEL` as a pure
  Python state layer only.
- [FEASpec CalculiX result write dialog](feaspec_calculix_result_write_dialog.md)
  implements `OSW-EXP-047_FEASPEC_RESULT_IMPORT_WRITE_GUI_DIALOG_IMPLEMENTATION`
  as a display-only PySide6 surface over the view-model. It adds no
  QFileDialog, writer invocation, ResultDataset write behavior, solver
  execution, SolverAdapter/runner path, ProjectSchema mutation, or issue `#8`
  validation.
- `OSW-EXP-048_FEASPEC_RESULT_IMPORT_WRITE_GUI_FILE_DIALOG_PLANNING`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
