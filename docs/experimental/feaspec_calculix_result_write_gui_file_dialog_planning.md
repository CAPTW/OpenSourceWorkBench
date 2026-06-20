# FEASpec CalculiX result write GUI file dialog planning

Status: design/planning-only. No QFileDialog implementation. No GUI source
changes. No writer invocation. No file writes. No ResultDataset persistence.
No solver execution.

## Release context

OpenSolver Workbench `v0.1.4-rc1` is a public prerelease. This planning gate is
post-release development on `develop`. It does not change the public release,
release tag, assets, package version, or issue state.

## Relationship to existing layers

The future file-dialog behavior sits above existing experimental FEASpec
CalculiX result-write layers:

- the display-only write dialog renders reviewed state and disabled actions;
- the pure write view-model computes panels, action states, acknowledgements,
  disabled reasons, preview records, and lexical save-path plans;
- the write CLI already defines review-gated `--output-dir`,
  `--acknowledge-limitations`, `--acknowledge-review-required`, create-dir, and
  overwrite semantics;
- the library writer persists standard ResultDataset review files only when a
  caller explicitly invokes it;
- the human-review file-dialog pattern shows how mockable path selection can be
  separated from any write operation.

This document only plans the future GUI output-directory selection boundary. It
does not add QFileDialog usage, GUI source changes, writer integration, or
ResultDataset write behavior.

## Future entry points

The future GUI may expose these controls once a separate implementation gate is
approved:

- choose output directory action;
- output directory text field showing the selected directory;
- create-dir acknowledgement for missing output directories;
- overwrite acknowledgement when planned ResultDataset review files already
  exist;
- visible disabled reasons from the write view-model before any write action is
  enabled.

The controls must bind to the existing view-model/save-plan contract first.
They must not bypass the view-model or call the library writer during
selection.

## QFileDialog policy

The future chooser should use directory selection only. It should not select an
individual `result_dataset.json` file. The chosen directory is the candidate
output directory for the standard ResultDataset review file set.

The policy is:

- no hidden defaults;
- no automatic write;
- no solver execution;
- no result parsing;
- no external command execution;
- no artifact copy;
- no automatic ResultDataset persistence;
- no broad ProjectSchema mutation.

The dialog may only collect explicit user intent. It may update the in-memory
save path plan and visible state.

## Default directory policy

The default directory should be visible and reviewable:

- prefer the last successful explicit selection from the current GUI session;
- otherwise use a visible project or result context fallback when one exists;
- otherwise leave the field blank and show a missing-output-directory disabled
  reason;
- never default silently to hidden temporary directories;
- never default silently to release asset directories;
- never default silently to `.git`, `.codex`, cache, or build artifact
  locations.

Defaults are suggestions only. The selected directory remains explicit user
input.

## Selection behavior

Cancel is no-op. A canceled directory chooser must leave the existing
view-model/save-plan state unchanged and must not record a failed write.

An accepted directory selection updates the output directory text field and the
view-model/save-plan only. It must not write files. It must not create
directories. It must not copy artifacts. It must not call the writer. It must
not run CalculiX or any other solver.

## Path validation

The future implementation should normalize and validate selected directories
before enabling a write action:

- normalize path separators and redundant path components for display;
- reject traversal or unsafe internal paths;
- reject reserved Windows names and invalid Windows path characters;
- reject `.git`, `.codex`, release asset output directories, caches, and build
  artifact locations;
- reject paths that would place ResultDataset review files inside solver
  runtime artifact directories unless explicitly allowed by a separate gate;
- require the parent context needed by the write plan to be visible to the user.

Validation should produce disabled reasons instead of hidden mutation.

## Create-dir behavior

Missing output directories require an explicit create-dir acknowledgement. The
file-dialog selection step must not create the directory. Directory creation, if
ever implemented, belongs to the future writer invocation path and must be
covered by separate implementation tests.

The future GUI should show:

- the normalized selected directory;
- whether it exists according to the write plan;
- whether create-dir acknowledgement is required;
- why the write action remains disabled until acknowledgement is present.

## Overwrite behavior

Overwrite checks are based on the planned standard files in the write plan.
Existing planned files require an explicit overwrite acknowledgement. Selection
must not overwrite anything.

The future GUI should show which planned files would be affected:

- `result_dataset.json`;
- `result_dataset_manifest.json`;
- `diagnostics.json`;
- `provenance.json`;
- `README_REVIEW_FIRST.txt`.

The acknowledgement must be visible and separate from choosing the directory.

## CLI/GUI consistency

The GUI should mirror the write CLI semantics:

- explicit output directory is required;
- plan-only inspection precedes write;
- limitations acknowledgement is required;
- review-required acknowledgement is required;
- create-dir acknowledgement is required when needed;
- overwrite acknowledgement is required when needed;
- disabled reasons should match the same blocker concepts used by the CLI and
  view-model;
- text/JSON CLI evidence should map to visible GUI status without changing CLI
  behavior.

GUI selection does not change the CLI command and does not call the library
writer.

## Future implementation test plan

A future implementation gate should add mocked tests for:

- QFileDialog accepted directory;
- QFileDialog cancel no-op;
- unsafe path rejection;
- missing parent/create-dir acknowledgement;
- existing planned file overwrite acknowledgement;
- no writer call during selection;
- no file writes during selection;
- no directory creation during selection;
- no artifact copy;
- no solver execution;
- no SolverAdapter, runner, subprocess, or external command usage;
- no ProjectSchema mutation;
- no release, tag, asset, or issue mutation.

Tests should use generated temporary directories and files. They should not add
tracked solver output fixtures.

## Safety boundary

The planning boundary is:

- no QFileDialog implementation;
- no GUI source changes;
- no view-model source changes;
- no CLI behavior changes;
- no library writer behavior changes;
- no writer invocation;
- no ResultDataset file writes;
- no artifact copying;
- no CalculiX execution;
- no solver execution;
- no SolverAdapter integration;
- no runner integration;
- no subprocess use;
- no external command invocation;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no dependency install or upgrade;
- no release edit, release create, release publish, asset upload, or asset
  delete;
- no tag creation or push;
- no issue creation, comment, or closure.

## Relationship to issue #8

This file-dialog planning does not validate live `ccx`. Issue `#8` remains
open until a separate prepared-machine live CalculiX validation gate records
passing evidence. Selecting a future output directory is not solver validation
and must not be used to close issue `#8`.

## Non-goals

- no QFileDialog implementation;
- no file dialog implementation;
- no GUI source changes;
- no GUI file write behavior;
- no writer invocation;
- no ResultDataset persistence;
- no CLI behavior change;
- no library writer behavior change;
- no solver execution;
- no live `ccx` validation;
- no bundled solver;
- no certification;
- no industrial certification.

## Next implementation slices

- `OSW-EXP-049_FEASPEC_RESULT_IMPORT_WRITE_GUI_FILE_DIALOG_IMPLEMENTATION`
- `OSW-EXP-050_FEASPEC_RESULT_IMPORT_WRITE_GUI_WRITER_INTEGRATION_NO_SOLVER`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
