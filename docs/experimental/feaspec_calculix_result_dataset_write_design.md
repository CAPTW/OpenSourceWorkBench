# FEASpec CalculiX ResultDataset write design

Status: design-only. No ResultDataset persistence implementation. No file
writes. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This design is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this
  gate.

## Relationship to existing layers

This design sits after the implemented FEASpec CalculiX result import layers:

- result import model;
- ResultDataset draft mapping;
- result import CLI preview;
- metadata, status, `.dat`, and `.frd` scanners.

The existing ResultDataset draft mapping remains the reviewable in-memory
source. This design defines the future write boundary for that reviewed draft
only; it does not add persistence.

The implemented
[FEASpec CalculiX ResultDataset write plan](feaspec_calculix_result_dataset_write_plan.md)
now provides the first in-memory planning slice for this design. It validates
explicit output-directory intent, path safety, draft status, schema/provenance
readiness, artifact references, limitations acknowledgement, and planned atomic
write paths while still performing no ResultDataset persistence or actual file
writes.

The implemented
[FEASpec CalculiX ResultDataset schema payload model](feaspec_calculix_result_dataset_schema.md)
adds the next in-memory slice. It assembles ResultDataset, manifest,
diagnostics, provenance, and review README payload records from the reviewed
draft mapping and write plan, but still performs no file writes, no
ResultDataset persistence, no artifact copying, and no solver execution.

## Write goals

A future write gate should:

- persist a reviewed ResultDataset draft;
- preserve provenance from run metadata, export manifests, parser summaries,
  and review state;
- preserve diagnostics and limitations instead of hiding partial evidence;
- remain reproducible through stable schema metadata and artifact hashes;
- avoid copying solver outputs unless an explicit future copy mode is designed;
- keep live solver validation and result persistence as separate concerns.

## Proposed output layout

A future writer should create one explicit output directory containing:

- `result_dataset.json`: the reviewed ResultDataset payload;
- `result_dataset_manifest.json`: schema, producer, source, artifact, and hash
  inventory;
- `diagnostics.json`: carried-forward and write-planning diagnostics;
- `provenance.json`: run/export/parser/review provenance;
- `artifacts/`: optional future copy area, disabled unless a separate copy-mode
  gate approves it;
- `README_REVIEW_FIRST.txt`: human-facing limitations, prerelease status, no
  certification claim, and no bundled solver note.

The default design references original artifacts by path, size, and SHA-256
rather than copying them.

## Schema/versioning

The future schema should include:

- `schema_name`: `osw.feaspec.calculix.resultdataset`;
- `schema_version`: a small explicit persistence schema version;
- `producer`: the OSW component and command that produced the files;
- `producer_version`: the installed OSW package version;
- `source_release`: `v0.1.4-rc1` or the later development release context;
- `source_version`: package metadata such as `0.1.4rc1`;
- `migration_policy`: old files are read only through explicit migration gates.

Schema changes must be additive where practical, reviewed, and covered by
fixtures before any implementation gate can write files.

## Write preconditions

A future writer must require:

- an explicit output path or output directory;
- a non-blocked ResultDataset draft mapping;
- provenance records for source artifacts and parser summaries;
- diagnostics reviewed or explicitly carried forward;
- no unsupported persistence blockers;
- explicit acknowledgement that live `ccx` validation is separate.

Blocked drafts, missing provenance, unreviewed diagnostics, unsafe paths, or
missing artifact references should prevent persistence.

## Output path policy

The future output path policy should require:

- explicit user-supplied paths only;
- no hidden default location;
- parent directory handling defined by options, not inference;
- create-directory behavior behind an explicit flag;
- path traversal rejection;
- Windows path normalization notes for drive roots, UNC paths, reserved names,
  and case-insensitive collisions.

The writer must never choose a hidden workspace, temporary, or project
directory on behalf of the user.

## Overwrite policy

The future default is no overwrite.

- `overwrite=false` blocks if the target exists.
- `overwrite=true` must be explicit.
- Unrelated directories are never overwritten.
- Existing non-ResultDataset files are blockers.
- Partial prior writer outputs require manifest review before replacement.

## Atomic write design

A future implementation should:

- render all JSON payloads in memory first;
- write to a temporary path inside the target parent;
- flush and fsync where practical for local filesystems;
- atomically rename or replace only after all payloads validate;
- record partial write diagnostics on failure;
- clean up temporary paths when safe;
- preserve enough evidence when cleanup fails.

This gate does not implement atomic writes.

## Artifact reference policy

The default policy references original artifacts:

- path;
- suffix and role;
- size;
- SHA-256;
- scanner/parser summary references;
- source run/export provenance.

Optional future copy mode would place copied artifacts under `artifacts/` only
after a separate gate defines size limits, hash verification, overwrite
behavior, and privacy warnings. Missing artifacts or hash mismatches block
write planning unless a reviewed degraded mode is explicitly introduced.

## Validation before write

Future validation should cover:

- draft status and blocker diagnostics;
- required ResultDataset schema fields;
- schema/version metadata;
- provenance completeness;
- artifact references and hashes;
- diagnostics and limitations retention;
- no hidden solver execution evidence;
- no unsupported `.frd` numerical field arrays or reconstructed mesh data.

Validation failure should prevent file writes.

## Planned diagnostics

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
- `FDW_ATOMIC_WRITE_FAILED`
- `FDW_PARTIAL_WRITE_CLEANUP_FAILED`
- `FDW_RESULTDATASET_PERSISTENCE_FORBIDDEN`

## CLI future design

A future preview-to-write command should require:

- explicit `--output`;
- explicit `--overwrite` for replacement;
- explicit `--acknowledge-limitations`;
- structured text and JSON diagnostics;
- no solver execution;
- no SolverAdapter or runner path;
- no release, tag, asset, or issue mutation.

The current result import CLI remains preview-only and has no write command.

## GUI future design

A future GUI flow should be review-first:

- show draft mapping, diagnostics, limitations, and artifact references;
- require an explicit user-selected path;
- require overwrite confirmation;
- make missing artifact/hash blockers visible;
- save only through the future reviewed writer;
- never execute solvers.

No GUI write/import command is implemented by this design gate.

## Security and safety boundary

This design preserves:

- no solver execution;
- no subprocess;
- no SolverAdapter;
- no runner;
- no ProjectSchema mutation;
- no VLM API;
- no provider credentials;
- no release mutation;
- no issue mutation.

The design also does not add `.frd` numerical field parsing, node or element
value arrays, mesh reconstruction, field reconstruction, visualization arrays,
unit inference, bundled solvers, or industrial certification.

## Test strategy

Future implementation tests should include:

- dry planning tests;
- path safety tests;
- overwrite policy tests;
- artifact hash verification tests;
- schema/version validation tests;
- diagnostic retention tests;
- atomic-write simulation tests in a future implementation gate;
- no file writes in this design gate.

Design tests lock the wording and non-goals. Implementation tests must use
`tmp_path` and must not add tracked solver output fixtures.

## Relationship to #8

This write design does not validate live `ccx`.
Issue `#8` remains open until a prepared-machine live CalculiX validation gate
passes.

## Non-goals

- no persistence implementation;
- no actual file writes;
- no write-capable import CLI;
- no GUI write/import command;
- no `.frd` numerical parser;
- no mesh reconstruction;
- no field reconstruction;
- no solver execution;
- no certification;
- no industrial certification;
- no bundled solver.

## Future implementation slices

- `OSW-EXP-042_FEASPEC_RESULT_IMPORT_DATASET_WRITE_IMPLEMENTATION`
- `OSW-EXP-043_FEASPEC_RESULT_IMPORT_WRITE_CLI_PREVIEW_ONLY`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
