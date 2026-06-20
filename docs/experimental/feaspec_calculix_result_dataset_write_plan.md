# FEASpec CalculiX ResultDataset write plan

Status: experimental in-memory write plan implemented. No ResultDataset
persistence. No actual file writes. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this
  gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_dataset_write_plan.py`
- `src/osw/experimental/feaspec/calculix_result_dataset_write_diagnostics.py`

## Public API

- `plan_calculix_result_dataset_write`
- `validate_calculix_result_dataset_write_plan`
- `explain_calculix_result_dataset_write_plan`

The API consumes an existing FEASpec CalculiX ResultDataset draft mapping or a
compatible object. It returns pure Python records that describe a reviewed
future persistence operation. It does not create directories, copy artifacts,
write JSON, write README files, persist a `ResultDataset`, mutate
ProjectSchema, execute CalculiX, or call SolverAdapter or runner code.

## Public result objects

- `FEASpecCalculiXResultDatasetWritePlan`
- `FEASpecCalculiXResultDatasetWritePlanValidation`
- `FEASpecCalculiXResultDatasetWriteTarget`
- `FEASpecCalculiXResultDatasetPlannedFile`
- `FEASpecCalculiXResultDatasetArtifactReferencePlan`
- `FEASpecCalculiXResultDatasetAtomicWritePlan`
- `FEASpecCalculiXResultDatasetWriteStatus`
- `FEASpecCalculiXResultDatasetWriteDiagnostic`

Status values are `planned`, `planned-with-warnings`, `blocked`,
`unsupported`, and `persistence-not-implemented`.

## Planned output layout

For a reviewed output directory, the plan model records these standard future
files:

- `result_dataset.json`
- `result_dataset_manifest.json`
- `diagnostics.json`
- `provenance.json`
- `README_REVIEW_FIRST.txt`

Each file is represented as a planned file with a role, relative path, target
path, temporary path, existence flag, and write flag. The write flag remains
`false` because this gate performs no actual file writes.

## Target and path policy

The model requires an explicit output directory for the standard layout.

- Missing output produces `FDW_OUTPUT_PATH_REQUIRED`.
- Single-file `output_path` mode is unsupported and produces
  `FDW_OUTPUT_DIRECTORY_REQUIRED`.
- Missing parent directories produce `FDW_PARENT_MISSING` unless `create_dir`
  is explicitly requested.
- `create_dir=True` records `FDW_CREATE_DIR_REQUIRED` and marks directory
  creation as planned only; it does not create the directory.
- Paths with `..` segments produce `FDW_PATH_TRAVERSAL_REJECTED`.
- Paths under forbidden locations such as `.git` or `.codex` produce
  `FDW_UNSAFE_PATH`.
- Existing file targets and non-empty directories block by default.
- `overwrite=True` records reviewed overwrite intent but still does not modify
  or delete files.

The planner never chooses a hidden output path on behalf of the caller.

## Atomic write plan

The atomic write object records:

- planned-only status;
- future temporary directory path;
- final target directory path;
- temp-to-target file pairs for the standard files.

It emits `FDW_ATOMIC_WRITE_PLANNED_ONLY` and
`FDW_ATOMIC_WRITE_NOT_IMPLEMENTED` for review visibility. It does not create a
temporary directory, write files, rename files, replace files, clean partial
outputs, or implement atomic persistence.

## Artifact reference plan

Artifact references are retained from the draft mapping by:

- source path;
- filename;
- role;
- suffix;
- SHA-256;
- size in bytes;
- existence and size/hash match flags.

Existing artifact references are checked read-only for size and SHA-256
consistency. Missing path, hash, or size produces
`FDW_ARTIFACT_REFERENCE_MISSING`. A changed size or hash produces
`FDW_ARTIFACT_HASH_MISMATCH`. `copy_artifacts=True` records
`FDW_ARTIFACT_COPY_NOT_IMPLEMENTED`; artifacts remain referenced and are not
copied.

## Validation policy

Validation preserves the draft mapping safety boundary:

- blocked or unsupported drafts produce `FDW_DRAFT_BLOCKED`;
- missing write schema version produces `FDW_SCHEMA_VERSION_MISSING`;
- missing provenance produces `FDW_PROVENANCE_INCOMPLETE`;
- existing draft diagnostics produce `FDW_DIAGNOSTICS_UNREVIEWED`;
- draft limitations require explicit `acknowledge_limitations=True` and
  otherwise produce `FDW_LIMITATIONS_NOT_ACKNOWLEDGED`.

The validation object reports blocker state, diagnostics, and explicit
`writes_files=false` and `result_dataset_persistence=false` flags.

## Diagnostics

- `FDW_WRITE_NOT_IMPLEMENTED`
- `FDW_OUTPUT_PATH_REQUIRED`
- `FDW_OUTPUT_DIRECTORY_REQUIRED`
- `FDW_PARENT_MISSING`
- `FDW_CREATE_DIR_REQUIRED`
- `FDW_OUTPUT_EXISTS`
- `FDW_OUTPUT_NOT_EMPTY`
- `FDW_UNSAFE_PATH`
- `FDW_PATH_TRAVERSAL_REJECTED`
- `FDW_DRAFT_BLOCKED`
- `FDW_SCHEMA_VERSION_MISSING`
- `FDW_PROVENANCE_INCOMPLETE`
- `FDW_ARTIFACT_REFERENCE_MISSING`
- `FDW_ARTIFACT_HASH_MISMATCH`
- `FDW_DIAGNOSTICS_UNREVIEWED`
- `FDW_LIMITATIONS_NOT_ACKNOWLEDGED`
- `FDW_ATOMIC_WRITE_PLANNED_ONLY`
- `FDW_ATOMIC_WRITE_NOT_IMPLEMENTED`
- `FDW_ARTIFACT_COPY_NOT_IMPLEMENTED`
- `FDW_RESULTDATASET_PERSISTENCE_FORBIDDEN`

Historical design diagnostics such as `FDW_ATOMIC_WRITE_FAILED` and
`FDW_PARTIAL_WRITE_CLEANUP_FAILED` remain future implementation concerns, not
implemented behavior in this planning gate.

Writer implementation diagnostics now live in the shared catalog for the
separate library writer:

- `FDW_WRITE_COMPLETED`
- `FDW_WRITE_FAILED`
- `FDW_TEMP_WRITE_FAILED`
- `FDW_TARGET_REPLACE_FAILED`
- `FDW_UNPLANNED_FILE_COLLISION`
- `FDW_WRITTEN_FILE_HASH_FAILED`
- `FDW_ARTIFACT_COPY_FORBIDDEN`

The write-plan module still performs no actual file writes and no
ResultDataset persistence.

## Relationship to draft mapping

[FEASpec CalculiX ResultDataset draft mapping](feaspec_calculix_result_dataset_draft_mapping.md)
provides the in-memory source payload. The write plan model consumes that draft
mapping, preserves artifact and provenance evidence, carries diagnostics and
limitations forward, and plans a future reviewed output layout. It does not
turn the draft into persisted `ResultDataset` files.

## Relationship to schema payload model

[FEASpec CalculiX ResultDataset schema payload model](feaspec_calculix_result_dataset_schema.md)
consumes this write plan and the draft mapping to assemble deterministic
in-memory ResultDataset, manifest, diagnostics, provenance, and review README
payload records. It still performs no actual file writes, creates no
directories, copies no artifacts, persists no ResultDataset, and executes no
solver.

## Relationship to library writer

[FEASpec CalculiX ResultDataset writer](feaspec_calculix_result_dataset_writer.md)
consumes this reviewed plan plus a schema payload. The writer is the separate
explicit persistence layer; this planning module remains in-memory only.

## Relationship to write CLI

[FEASpec CalculiX result import write CLI](feaspec_calculix_result_import_write_cli.md)
composes the result import preview, draft mapping, this write plan, schema
payload, and library writer. The CLI is separate from this planning module and
does not add file writes or solver execution to the plan model itself.

## Relationship to result import model and CLI preview

The result import model and `feaspec-calculix-result-import-preview` remain
preview-only. The write plan can be called from tests and the separate
review-gated import write CLI to inspect path and validation readiness, but
this module still has no CLI behavior, no GUI write/import command, and no
ResultDataset persistence.

## Relationship to future write GUI

[FEASpec CalculiX result import write GUI design](feaspec_calculix_result_import_write_gui_design.md)
defines how a future GUI should expose this write plan: explicit output
directory, visible disabled reasons, limitations/review acknowledgements,
overwrite/create-directory acknowledgement, and review-first confirmation. This
planning module still does not implement GUI behavior or file dialogs.

## Safety boundary

This model preserves:

- no actual file writes;
- no directory creation;
- no artifact copying;
- no ResultDataset persistence;
- no CLI behavior inside this write plan model;
- no GUI write/import command;
- no solver execution;
- no subprocess;
- no SolverAdapter;
- no runner;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no release mutation;
- no asset upload or delete;
- no tag mutation;
- no issue mutation.

The model also adds no `.frd` numerical field parser, no mesh reconstruction,
no field reconstruction, no visualization arrays, no unit inference, no bundled
solver, and no industrial certification.

## Fixture policy

Tests create synthetic result directories under `tmp_path`. This gate adds no
tracked `.frd`, `.dat`, `.sta`, `.cvg`, `.out`, `.err`, or solver log fixtures.

## Relationship to #8

Issue `#8` remains open. The write plan model does not validate live `ccx`,
does not record issue `#8` pass evidence, and does not close issue `#8`.

## Non-goals

- no actual ResultDataset persistence;
- no actual file writes;
- no atomic write implementation;
- no artifact copy implementation;
- no CLI behavior inside this write plan model;
- no GUI write/import command;
- no `.frd` numerical parser;
- no mesh reconstruction;
- no field reconstruction;
- no solver execution;
- no SolverAdapter handoff;
- no runner handoff;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no certification;
- no industrial certification;
- no bundled solver.

## Next implementation slices

- `OSW-EXP-042_FEASPEC_RESULT_IMPORT_DATASET_WRITE_IMPLEMENTATION`
  (completed as the separate library writer)
- `OSW-EXP-043_FEASPEC_RESULT_IMPORT_WRITE_CLI_DESIGN`
- `OSW-EXP-044_FEASPEC_RESULT_IMPORT_WRITE_CLI_IMPLEMENTATION`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
