# FEASpec CalculiX result import write CLI

Status: experimental CLI write command implemented. No GUI write command. No
solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- The public release, release tag, assets, and GitHub issues are not edited by
  this command.

## Command

```text
osw feaspec-calculix-result-import-write
```

The command is a review-first CLI wrapper over the existing FEASpec CalculiX
result import pipeline and library writer. It does not run CalculiX and does
not copy original solver artifacts.

## Modes

- plan-only default: build the import plan, draft mapping, write plan, and
  schema payload; write no files.
- explicit write: call the library writer only when `--write`,
  `--acknowledge-limitations`, and `--acknowledge-review-required` are all
  present.

## Required options

- `--result-dir PATH`: existing explicit CalculiX result directory.
- `--output-dir PATH`: explicit target directory for the standard
  ResultDataset layout.

## Acknowledgements

Write requires acknowledgements:

- `--acknowledge-limitations`: confirms carried parser/import limitations were
  reviewed.
- `--acknowledge-review-required`: confirms the `README_REVIEW_FIRST.txt`
  human-review workflow.

Plan-only mode can be used without acknowledgements because it writes no files.

## Write options

- `--write`: enable the explicit write path.
- `--plan-only`: force the default non-writing review mode.
- `--overwrite`: allow replacement of existing standard ResultDataset files.
- `--create-dir`: allow creation of the explicit output directory when parent
  policy allows it.
- `--format text|json`: choose output format.

## Pipeline

The command composes existing layers:

1. result import plan;
2. ResultDataset draft mapping;
3. ResultDataset write plan;
4. ResultDataset schema payload;
5. library writer `write_calculix_result_dataset` in explicit write mode only.

The CLI does not change writer semantics. Original `.dat`, `.frd`, `.sta`,
`.cvg`, log, or export artifacts remain references and are not copied.

## Text output

Text output includes mode, result directory, output directory, import status,
plan status, schema status, write status, planned files, diagnostics,
limitations, and written file hashes when write mode succeeds.

It also prints safety notes that no solver execution, artifact copying,
issue/release/tag mutation, or live issue `#8` validation occurs.

## JSON output

JSON output includes:

- `command`, `mode`, `result_dir`, `output_dir`;
- `import_status`, `draft_mapping_status`, `plan_status`, `schema_status`,
  and `write_status`;
- `planned_files` and `written_files`;
- `diagnostics`, `limitations`, and acknowledgement flags;
- `files_written`;
- `solver_execution_performed=false`;
- `artifact_copy_performed=false`;
- `issue_mutation_performed=false`;
- `release_mutation_performed=false`;
- `tag_mutation_performed=false`;
- `projectschema_mutation_performed=false`.

## Exit codes

- `0`: successful plan-only review or successful explicit write.
- `1`: CLI/read/internal failure or writer failure.
- `2`: blocked plan or write preconditions, including missing
  acknowledgements, invalid output path, existing output without overwrite,
  blocked import plan, blocked write plan, or blocked schema payload.

## Safety boundary

This command preserves:

- no solver execution;
- no CalculiX `ccx` invocation;
- no artifact copying;
- no GUI write command;
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

It also adds no `.frd` numerical field parser, no `.frd` value array parser, no
mesh reconstruction, no field reconstruction, no free-form `.dat` parser, no
unit inference, no engineering correctness claim, no bundled solver, and no
industrial certification.

## Relationship to #8

The write CLI does not validate live `ccx`. Issue `#8` remains open until a
separate prepared-machine live CalculiX validation gate records passing
evidence. Persisting review files is not live solver validation.

## Relationship to write GUI view-model

[FEASpec CalculiX result write view-model](feaspec_calculix_result_write_viewmodel.md)
exposes UI-agnostic panels, action states, disabled reasons, acknowledgements,
and save-path planning over the same import/write/schema records. The
view-model does not change this CLI behavior, does not call this CLI command,
does not invoke the writer, and does not add a GUI write command.

[FEASpec CalculiX result write GUI file dialog planning](feaspec_calculix_result_write_gui_file_dialog_planning.md)
defines the future output-directory chooser policy for GUI work while keeping
the CLI semantics unchanged. It remains planning-only and adds no QFileDialog
implementation, writer invocation, ResultDataset write, or solver execution.

[FEASpec CalculiX result write GUI writer integration design](feaspec_calculix_result_write_gui_writer_integration_design.md)
defines a future GUI writer-call boundary over the same plan, schema, and
library writer layers. That design does not call this CLI command and does not
change CLI options, exit codes, output formats, or write behavior.

## Non-goals

- no GUI write command;
- no solver execution;
- no artifact copy implementation;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no VLM API or provider credentials;
- no certification;
- no industrial certification;
- no bundled solver.

## Next implementation slices

- [FEASpec CalculiX result import write GUI design](feaspec_calculix_result_import_write_gui_design.md)
- [FEASpec CalculiX result write view-model](feaspec_calculix_result_write_viewmodel.md)
- [FEASpec CalculiX result write dialog](feaspec_calculix_result_write_dialog.md)
- [FEASpec CalculiX result write GUI file dialog planning](feaspec_calculix_result_write_gui_file_dialog_planning.md)
- [FEASpec CalculiX result write GUI writer integration design](feaspec_calculix_result_write_gui_writer_integration_design.md)
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
