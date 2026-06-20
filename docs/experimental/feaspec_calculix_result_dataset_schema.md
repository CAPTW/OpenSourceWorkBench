# FEASpec CalculiX ResultDataset schema payload model

Status: experimental in-memory schema payload model implemented. No
ResultDataset persistence. No file writes. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this
  gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_dataset_schema.py`
- `src/osw/experimental/feaspec/calculix_result_dataset_schema_diagnostics.py`

## Public API

- `build_calculix_result_dataset_schema_payload`
- `validate_calculix_result_dataset_schema_payload`
- `explain_calculix_result_dataset_schema_payload`
- `build_calculix_result_dataset_manifest_payload`
- `build_calculix_result_dataset_diagnostics_payload`
- `build_calculix_result_dataset_provenance_payload`
- `build_calculix_result_dataset_review_readme`

The API consumes an existing FEASpec CalculiX ResultDataset draft mapping and
an existing ResultDataset write plan. It returns pure Python records only. It
does not create directories, serialize JSON, write README files, persist a
`ResultDataset`, mutate ProjectSchema, execute CalculiX, or call SolverAdapter
or runner code.

## Public result objects

- `FEASpecCalculiXResultDatasetSchemaPayload`
- `FEASpecCalculiXResultDatasetSchemaValidation`
- `FEASpecCalculiXResultDatasetSchemaVersion`
- `FEASpecCalculiXResultDatasetManifestPayload`
- `FEASpecCalculiXResultDatasetDiagnosticsPayload`
- `FEASpecCalculiXResultDatasetProvenancePayload`
- `FEASpecCalculiXResultDatasetReviewReadmePayload`
- `FEASpecCalculiXResultDatasetSchemaStatus`
- `FEASpecCalculiXResultDatasetSchemaDiagnostic`

Status values are `payload-ready`, `payload-ready-with-warnings`, `partial`,
`blocked`, and `schema-model-only`.

## Schema metadata

The payload records:

- `schema_name`: `osw.feaspec.calculix.resultdataset`;
- `schema_version`: currently `0.1`;
- `producer`: OpenSolver Workbench FEASpec CalculiX result import;
- `producer_version`: installed OSW package metadata such as `0.1.4rc1`;
- `source_version`: provenance or package source version;
- `source_release`: `v0.1.4-rc1` for this development line.

Missing schema name, schema version, producer version, or source version blocks
payload validation.

## Dataset payload

The dataset payload is assembled from the draft mapping and preserves:

- dataset id, source, solver, analysis type, and draft status;
- artifact references;
- status summaries from `.sta` / `.cvg` scanners;
- bounded `.dat` scalar and table preview candidates;
- deferred `.frd` field references;
- provenance;
- carried diagnostics;
- carried limitations;
- explicit `writes_files=false`;
- explicit `result_dataset_persistence=false`.

It does not add numerical `.frd` parsing, mesh reconstruction, field
reconstruction, visualization arrays, unit inference, or solver correctness
claims.

## Manifest payload

The manifest payload is built in memory from the write plan and includes:

- schema metadata;
- dataset id;
- source path;
- solver and analysis type;
- planned output files;
- artifact references;
- review-required flag;
- `writes_files=false`;
- `result_dataset_persistence=false`;
- `solver_execution_performed=false`;
- `artifact_copy_performed=false`.

The manifest is invalid if the reviewed write plan does not provide planned
files. The standard layout must include `README_REVIEW_FIRST.txt`.

## Diagnostics payload

The diagnostics payload combines:

- schema-model diagnostics;
- carried result-import, scanner, parser, and draft-mapping diagnostics;
- write-plan diagnostics.

It preserves counts and blocker state for review. Diagnostics are carried
forward; they are not hidden or treated as proof of engineering correctness.

## Provenance payload

The provenance payload preserves:

- run metadata and export manifest fields carried by the draft mapping;
- source FEASpec id and case id where available;
- source release and source version;
- artifact source paths, filenames, suffixes, SHA-256 values, and sizes;
- `solver_execution_performed` exactly as provenance evidence, not as a new
  solver action by this model.

The schema model itself performs no solver execution.

## Review README payload

The review README payload is an in-memory `README_REVIEW_FIRST.txt` record. It
states:

- human review is required before any future persistence gate;
- no ResultDataset persistence is implemented here;
- no file writes occur in this schema model;
- no solver execution is performed by this schema model;
- issue `#8` remains open;
- external solvers are optional and not bundled;
- no industrial certification is claimed.

The README payload is required for the future standard output layout, but this
gate does not write the README to disk.

## Diagnostics

- `FDS_SCHEMA_MODEL_ONLY`
- `FDS_SCHEMA_NAME_MISSING`
- `FDS_SCHEMA_VERSION_MISSING`
- `FDS_PRODUCER_VERSION_MISSING`
- `FDS_SOURCE_VERSION_MISSING`
- `FDS_DRAFT_MAPPING_MISSING`
- `FDS_WRITE_PLAN_MISSING`
- `FDS_WRITE_PLAN_BLOCKED`
- `FDS_ARTIFACTS_MISSING`
- `FDS_PROVENANCE_MISSING`
- `FDS_DIAGNOSTICS_MISSING`
- `FDS_LIMITATIONS_MISSING`
- `FDS_PAYLOAD_INVALID`
- `FDS_MANIFEST_INVALID`
- `FDS_README_REQUIRED`
- `FDS_FILE_WRITE_FORBIDDEN`
- `FDS_PERSISTENCE_NOT_IMPLEMENTED`

## Validation policy

Validation blocks when:

- draft mapping evidence is missing;
- write plan evidence is missing or blocked;
- schema metadata is incomplete;
- artifacts are missing;
- provenance is missing;
- manifest planned files are missing;
- the review README payload is missing.

Missing carried diagnostics or missing limitations produce warning diagnostics
because a future persistence gate should review why those records are absent.

## Relationship to draft mapping

[FEASpec CalculiX ResultDataset draft mapping](feaspec_calculix_result_dataset_draft_mapping.md)
provides the source in-memory ResultDataset-shaped draft. This schema model
packages that draft into a stable payload bundle with schema, manifest,
diagnostics, provenance, and review README records. It still writes no files and
persists no `ResultDataset`.

## Relationship to write plan

[FEASpec CalculiX ResultDataset write plan](feaspec_calculix_result_dataset_write_plan.md)
provides reviewed output-directory intent, planned standard files, artifact
references, and write-plan diagnostics. This schema model consumes the write
plan to build manifest and review README payload records. A blocked write plan
blocks schema payload readiness.

## Relationship to result import model and CLI preview

The result import model and `feaspec-calculix-result-import-preview` remain
preview-only. The schema payload model is not wired as a write-capable import
CLI, adds no `--output` persistence mode, and performs no file writes.

## Safety boundary

This model preserves:

- no file writes;
- no ResultDataset persistence;
- no write-capable import CLI;
- no GUI write/import command;
- no atomic write implementation;
- no artifact copying;
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

Issue `#8` remains open. The schema payload model does not validate live `ccx`,
does not record issue `#8` pass evidence, and does not close issue `#8`.

## Non-goals

- no actual ResultDataset persistence;
- no actual file writes;
- no atomic write implementation;
- no artifact copy implementation;
- no write-capable import CLI;
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
- `OSW-EXP-043_FEASPEC_RESULT_IMPORT_WRITE_CLI_PREVIEW_ONLY`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
