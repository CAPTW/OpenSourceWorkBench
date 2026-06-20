# FEASpec CalculiX result write GUI writer integration design

Status: design-only. No GUI writer invocation. No GUI file writes. No solver
execution.

Implementation follow-up:
[FEASpec CalculiX result write GUI writer integration](feaspec_calculix_result_write_gui_writer_integration.md)
documents the later guarded GUI writer call through the existing library writer.
This design page remains the historical pre-implementation contract.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This design is post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Relationship to existing layers

This design depends on the already separated FEASpec CalculiX ResultDataset
write layers:

- [result write GUI file dialog](feaspec_calculix_result_write_gui_file_dialog.md)
  collects an explicit output directory and performs no write;
- [result write dialog](feaspec_calculix_result_write_dialog.md) renders the
  existing review surface and disabled write actions;
- [result write view-model](feaspec_calculix_result_write_viewmodel.md)
  computes panels, actions, disabled reasons, acknowledgements, and save-path
  evidence without importing PySide/Qt or invoking the writer;
- [result import write CLI](feaspec_calculix_result_import_write_cli.md)
  remains the review-gated command-line write path and is not called by the
  GUI;
- [ResultDataset writer](feaspec_calculix_result_dataset_writer.md) remains the
  library-only persistence function;
- the write plan and schema payload models remain the in-memory contract for
  planned paths, payload records, diagnostics, provenance, and limitations.

The future GUI writer integration must bind those layers without changing CLI
or library writer behavior.

## Future write action enablement

The future GUI write action may become enabled only when all preconditions are
visible and satisfied:

- output directory selected explicitly by the user;
- write plan ready and not blocked;
- schema ready and not blocked;
- limitations acknowledged;
- review required acknowledged;
- overwrite acknowledged when planned files already exist;
- create-dir acknowledged when the target directory or required parent needs an
  explicit create-directory decision.

Missing, stale, or blocked evidence keeps the write action disabled with a
visible reason. A selected output directory does not by itself authorize a
write.

## Confirmation flow

Before any future GUI writer call, the dialog must show a final confirmation
summary. The summary should include:

- source result directory;
- selected output directory;
- files to be written;
- planned overwrite or create-directory requirements;
- limitations and diagnostics;
- no solver execution warning;
- note that issue `#8` live CalculiX validation remains separate.

Canceling confirmation is a no-op. Accepting confirmation only authorizes the
single bounded library writer call described below; it does not authorize solver
execution, artifact copying, release mutation, tag mutation, or issue mutation.

## Future writer invocation boundary

The only allowed future writer boundary is a single explicit call to the
library writer after the GUI has refreshed the current records:

1. build or refresh the result import plan;
2. build the draft ResultDataset mapping;
3. build the write plan for the selected output directory;
4. build the schema payload;
5. show and accept final confirmation;
6. call the library writer once;
7. update the view-model with the writer result summary.

That future call must not invoke a solver or subprocess. It must not copy
original solver artifacts by default. It must not mutate GitHub releases,
assets, tags, or issues. It must not mutate ProjectSchema.

## Failure handling

The future GUI flow must keep failures inspectable and retryable:

- blocked write plan: keep write disabled and show blocker diagnostics;
- blocked schema: keep write disabled and show schema diagnostics;
- writer failure: show the returned error and leave the selected output
  directory visible;
- partial cleanup failure: surface the cleanup diagnostic and the affected path;
- overwrite or collision failure: require renewed overwrite acknowledgement;
- target path issue: refresh save-path analysis and keep the write action
  disabled until the path is corrected.

Failure handling must not hide partial evidence, retry automatically, or delete
caller files outside the writer's own bounded atomic-write cleanup contract.

## Post-write UI

After a future successful write, the dialog may show:

- written files;
- file sizes and SHA-256 hashes;
- output directory;
- writer diagnostics and limitations;
- a future open output folder action.

The open output folder action is intentionally future behavior. If added later,
it must be separately reviewed because it can cross into platform integration.

## Retry behavior

Retry behavior must be explicit:

- safe retry after failure is allowed only after the current state is refreshed;
- overwrite acknowledgement is required again when planned outputs collide;
- stale plans must be rebuilt before the next confirmation;
- a successful writer result should not be reused as authorization for a second
  write.

## State refresh

The future integration must refresh state at the following boundaries:

- after output-dir change;
- after acknowledgement change;
- after writer result;
- after any writer or schema diagnostic changes;
- before final confirmation.

The view-model remains the presentation state boundary. GUI code should not
embed hidden parser, writer, or path-policy logic.

## Test plan

Future implementation tests should use mocks and temporary directories:

- mocked writer success;
- mocked writer failure;
- confirmation accepted and cancelled;
- acknowledgements gating;
- overwrite and create-directory gating;
- stale plan refresh;
- writer result summary display;
- no solver execution;
- no unexpected file writes before the mocked writer boundary;
- no SolverAdapter, runner, subprocess, ProjectSchema, release, tag, asset, or
  issue mutation.

## Safety boundary

This gate adds no implementation. It adds:

- no writer invocation;
- no GUI file writes;
- no ResultDataset persistence from GUI;
- no GUI source mutation;
- no view-model source mutation;
- no CLI behavior change;
- no library writer behavior change;
- no solver execution;
- no CalculiX `ccx` invocation;
- no SolverAdapter;
- no runner;
- no subprocess;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no release, asset, tag, or issue mutation.

External solvers are optional and not bundled. The future integration must not
present ResultDataset persistence as engineering correctness, live solver
validation, or certification evidence.

## Relationship to #8

Future GUI writer integration does not validate live `ccx`. Issue `#8` remains
open until a separate prepared-machine live CalculiX validation gate records
passing evidence. Writing reviewed ResultDataset files is not live optional
solver validation.

## Non-goals

- no implementation in this gate;
- no GUI writer invocation;
- no GUI file writes;
- no ResultDataset persistence from GUI;
- no QFileDialog behavior change;
- no CLI behavior change;
- no library writer behavior change;
- no artifact copying;
- no solver execution;
- no live `ccx` validation;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no bundled solver;
- no certification;
- no industrial certification.

## Next implementation slices

- `OSW-EXP-051_FEASPEC_RESULT_IMPORT_WRITE_GUI_WRITER_INTEGRATION`
- [FEASpec CalculiX result write GUI writer integration](feaspec_calculix_result_write_gui_writer_integration.md)
- `OSW-EXP-052_FEASPEC_RESULT_IMPORT_WRITE_GUI_POST_WRITE_POLISH`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
