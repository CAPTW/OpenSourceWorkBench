# FEASpec CalculiX ResultDataset writer

Status: experimental library writer implemented. No CLI write command. No GUI
write command. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this
  gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_dataset_writer.py`

## Public API

- `write_calculix_result_dataset`
- `prepare_calculix_result_dataset_write_payloads`
- `explain_calculix_result_dataset_write_result`

Public result objects:

- `FEASpecCalculiXResultDatasetWriteResult`
- `FEASpecCalculiXResultDatasetWrittenFile`
- `FEASpecCalculiXResultDatasetPreparedWritePayloads`
- `FEASpecCalculiXResultDatasetWriteResultStatus`

## Written files

The library writer writes exactly the reviewed standard layout:

- `result_dataset.json`
- `result_dataset_manifest.json`
- `diagnostics.json`
- `provenance.json`
- `README_REVIEW_FIRST.txt`

It does not write an `artifacts/` directory and does not copy original solver
outputs.

## Preconditions

The caller must provide:

- a valid ResultDataset write plan;
- a valid ResultDataset schema payload;
- an explicit output directory from the write plan;
- overwrite policy satisfied by the write plan or explicit writer argument;
- limitations acknowledgement already carried by the plan and schema payload.

Blocked plans, blocked schema payloads, missing output directories, unsafe
paths, unplanned file collisions, or artifact-copy requests block the write.

## Atomic write behavior

Each target file is written by:

- rendering deterministic payload text in memory;
- creating a temporary file in the target directory;
- flushing and fsyncing the temporary file on a best-effort local filesystem
  basis;
- atomically replacing the target with the temporary file;
- cleaning temporary files after failures where possible.

Failures are reported rather than hidden. A cleanup failure is classified as
`partial-cleanup-failed`.

## File metadata

The write result returns one metadata record per written file:

- path;
- relative path;
- payload kind;
- size;
- sha256.

Checksums are verified after the write completes.

## Diagnostics

The writer uses the shared `FDW_*` catalog and adds implementation diagnostics:

- `FDW_WRITE_COMPLETED`
- `FDW_WRITE_FAILED`
- `FDW_TEMP_WRITE_FAILED`
- `FDW_TARGET_REPLACE_FAILED`
- `FDW_UNPLANNED_FILE_COLLISION`
- `FDW_WRITTEN_FILE_HASH_FAILED`
- `FDW_ARTIFACT_COPY_FORBIDDEN`

Plan and schema diagnostics remain review evidence. The persisted
`diagnostics.json` preserves carried diagnostics from the schema payload.

## Safety boundary

This implementation preserves:

- no solver execution;
- no artifact copying;
- no CLI write command;
- no GUI write command;
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

The writer also adds no `.frd` numerical field parser, no mesh reconstruction,
no field reconstruction, no visualization arrays, no unit inference, no
bundled solver, and no industrial certification.

## Relationship to write plan and schema

The writer consumes the existing
[ResultDataset write plan](feaspec_calculix_result_dataset_write_plan.md) and
[ResultDataset schema payload](feaspec_calculix_result_dataset_schema.md). It
does not build new parser content, interpret solver correctness, or widen the
result import model.

The write plan and schema modules remain separately documented as in-memory
layers. Their own APIs still do not write files.

## Relationship to result import model and CLI preview

The result import model and `feaspec-calculix-result-import-preview` remain
preview-only. This writer is library-only and is not exposed as a write-capable
CLI or GUI flow.

## Relationship to future write CLI

[FEASpec CalculiX result import write CLI design](feaspec_calculix_result_import_write_cli_design.md)
defines how a future command may call this library writer after preview,
draft-mapping, write-plan, schema-payload, and acknowledgement checks pass. The
design gate does not register that command, does not change writer behavior,
and performs no ResultDataset writes.

## Fixture policy

Writer tests create synthetic result directories and write outputs only under
`tmp_path`. This gate adds no tracked `.frd`, `.dat`, `.sta`, `.cvg`, `.out`,
`.err`, or solver log fixtures.

## Relationship to #8

Issue `#8` remains open. The writer does not validate live `ccx`, does not
record issue `#8` pass evidence, and does not close issue `#8`.

## Non-goals

- no CLI write command;
- no GUI write command;
- no numerical `.frd` parser;
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

- `OSW-EXP-043_FEASPEC_RESULT_IMPORT_WRITE_CLI_DESIGN`
- `OSW-EXP-044_FEASPEC_RESULT_IMPORT_WRITE_CLI_IMPLEMENTATION`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
