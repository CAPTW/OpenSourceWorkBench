# FEASpec CalculiX ResultDataset draft mapping

Status: experimental in-memory draft mapping implemented; draft mapping only.
No ResultDataset persistence. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- This implementation is post-release development on `develop`.
- Public release artifacts, tags, assets, and issues are not edited by this
  gate.

## Package path

- `src/osw/experimental/feaspec/calculix_result_dataset_draft_mapping.py`

## Public API

- `build_calculix_result_dataset_draft_mapping`
- `summarize_calculix_result_dataset_draft_mapping`
- `explain_calculix_result_dataset_draft_mapping`

The API consumes an existing FEASpec CalculiX result import plan or compatible
object and returns pure Python data records. It writes no files and performs no
additional parsing.

## Mapped inputs

The draft mapping consumes already-built result import records:

- artifact metadata from directory inspection;
- `.sta` and `.cvg` status summaries;
- `.dat` scalar candidates from the bounded minimal parser;
- `.dat` table candidates from the bounded minimal parser;
- `.frd` reference candidates from the block metadata scanner;
- provenance from run metadata and export manifests;
- diagnostics and limitations from the result import plan and scanner payloads.

## Draft outputs

The mapping produces:

- draft artifacts with source path, name, suffix, kind, role, SHA-256, size, and
  parser summary references;
- draft scalars with label, raw value, already-parsed preview value, unit, and
  line provenance;
- draft tables with heading, raw headers, raw cells, already-parsed preview
  cells, unit context, row and column counts, and line spans;
- draft field references for `.frd` blocks, without field arrays;
- provenance records;
- limitations;
- diagnostics.

The mapping also exposes a compact summary with artifact, status-summary,
scalar, table, field-reference, limitation, and diagnostic counts.

## Safety boundary

- no file writes;
- no ResultDataset persistence;
- no solver execution;
- no subprocess;
- no SolverAdapter;
- no runner;
- no unit inference;
- no engineering correctness claims;
- no numerical `.frd` parser;
- no `.frd` node or element value arrays;
- no mesh reconstruction;
- no field reconstruction;
- no visualization arrays;
- no VLM API;
- no provider credentials.

Units are preserved only when already present in the existing parser outputs.
The mapping does not infer units from headings, labels, values, or file names.

## Relationship to result import model

`build_calculix_result_dataset_draft` now includes the richer draft mapping in
its in-memory `draft_mapping` payload while preserving the older draft fields.
This keeps existing preview consumers working and provides a stable structure
for a future reviewed ResultDataset write gate.

The CLI preview may display compact draft mapping counts and may include the
full `dataset_draft_mapping` JSON payload. It remains preview-only and writes
no files.

## Relationship to write design

[FEASpec CalculiX ResultDataset write design](feaspec_calculix_result_dataset_write_design.md)
defines the future reviewed persistence boundary for this in-memory draft. It
records the proposed output layout, schema/versioning, path and overwrite
policy, atomic-write strategy, artifact reference policy, validation rules, and
`FDW_*` diagnostics. That design is documentation-only: no ResultDataset
persistence implementation, file write, write-capable CLI, GUI write flow, or
solver execution exists in this gate.

## Relationship to #8

The draft mapping does not validate live `ccx`.
Issue `#8` remains open until a prepared-machine live CalculiX validation gate
passes.

## Non-goals

- no persistence;
- no ResultDataset write;
- no write-capable import command;
- no `.frd` numerical parser;
- no mesh reconstruction;
- no solver execution;
- no certification;
- no industrial certification;
- no bundled solver.

## Next implementation slices

- `OSW-EXP-040_FEASPEC_RESULT_IMPORT_DATASET_WRITE_PLAN_MODEL`
- `OSW-EXP-041_FEASPEC_RESULT_IMPORT_DATASET_WRITE_IMPLEMENTATION`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
