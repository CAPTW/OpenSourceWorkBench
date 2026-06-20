# FEASpec CalculiX result import write CLI design

Status: historical design implemented by
`docs/experimental/feaspec_calculix_result_import_write_cli.md`. No GUI write
command. No solver execution.

## Release context

- `v0.1.4-rc1` is a public prerelease.
- The design and implementation are post-release development on `develop`.
- The public release, release tag, release assets, and GitHub issues are not
  edited by this work.

## Relationship to existing layers

The write CLI is a review surface over existing layers:

- `feaspec-calculix-result-import-preview` inspects an explicit result
  directory and returns a preview-only result import plan.
- The ResultDataset draft mapping turns preview evidence into an in-memory
  ResultDataset-shaped draft.
- The write plan model records output-directory intent, planned standard files,
  path policy, overwrite intent, artifact references, diagnostics, provenance,
  and limitations acknowledgement.
- The schema payload model builds deterministic in-memory ResultDataset,
  manifest, diagnostics, provenance, and review README payloads.
- The library writer writes the five standard ResultDataset review files only
  after the plan and schema payload are valid.

The implementation registers a CLI command, does not change the library
writer, and does not add any GUI write path.

## Command

```text
osw feaspec-calculix-result-import-write
```

The command is registered as of
`OSW-EXP-044_FEASPEC_RESULT_IMPORT_WRITE_CLI_IMPLEMENTATION`.

## Command modes

- `--plan-only`: inspect inputs, build the import plan, draft mapping, write
  plan, and schema payload readiness, then print text or JSON output without
  writing files.
- `--write`: perform the same planning flow and call the library writer only
  when all write preconditions and acknowledgements are satisfied.
- text output: human-readable review-first summary.
- JSON output: machine-readable plan and write readiness payload.

Default mode is plan-only.

## Required input options

- `--result-dir PATH`: existing explicit CalculiX result directory to inspect.
- `--output-dir PATH`: explicit target directory for the standard
  ResultDataset layout.

Both paths must be caller-provided. The command must not invent hidden output
paths or derive a write target from unreviewed artifact names.

## Safety and acknowledgement options

- `--acknowledge-limitations`: required before write mode can call the writer
  when limitations are present.
- `--acknowledge-review-required`: required before write mode can call the
  writer, confirming the `README_REVIEW_FIRST.txt` workflow.
- `--overwrite`: opt in to overwriting existing standard files after review.
- `--create-dir`: opt in to creating the explicit output directory when the
  parent policy allows it.
- `--format text|json`: choose text or JSON output; default is `text`.

## Default behavior

- Plan-only by default.
- No files written unless `--write` mode is explicit.
- No solver execution.
- No artifact copying.
- No release, tag, asset, or issue mutation.

The default command is useful for review automation and tutorials without
modifying the filesystem.

## Write behavior

When `--write` is present, the command composes the existing layers in this
order:

1. Call the result import planner for `--result-dir`.
2. Build the ResultDataset draft mapping.
3. Build a write plan for `--output-dir`, `--overwrite`, `--create-dir`, and
   acknowledgements.
4. Build the schema payload from the draft mapping and write plan.
5. Validate the write plan and schema payload.
6. Call `write_calculix_result_dataset` only if `--write` is explicit and all
   acknowledgements are present.
7. Print text or JSON output that records files written, diagnostics, and
   safety flags.

The write path must not copy original `.dat`, `.frd`, `.sta`, `.cvg`, log, or
export artifacts. Artifact references remain references.

## Exit codes

- `0`: successful plan-only review or successful write.
- `2`: blocked plan or write preconditions, including missing
  acknowledgements, invalid output path, existing output without overwrite,
  blocked import plan, blocked write plan, or blocked schema payload.
- `1`: CLI usage errors, read errors, invalid JSON serialization, writer
  failure, or unexpected internal errors.

## Text output

Text output includes:

- command mode;
- result directory and output directory;
- plan status and write status;
- planned files;
- diagnostics and blocker count;
- limitations and required acknowledgements;
- written standard files and hashes when write mode succeeds;
- safety notes stating no solver execution, no artifact copying, no issue
  mutation, and no release mutation.

## JSON output

JSON output includes:

- `command`;
- `mode`;
- `result_dir`;
- `output_dir`;
- `plan_status`;
- `schema_status`;
- `write_status`;
- `planned_files`;
- `written_files`;
- `diagnostics`;
- `files_written`;
- `solver_execution_performed`;
- `artifact_copy_performed`;
- `release_mutation_performed`;
- `issue_mutation_performed`;
- `limitations`;
- `acknowledgements`.

In plan-only mode, `files_written` is `false`, `written_files` is empty, and
`solver_execution_performed` is `false`.

## Path and overwrite policy

- Require an explicit output directory.
- Reject single-file output paths.
- Reject path traversal such as `..` segments.
- Reject unsafe targets under `.git`, `.codex`, release artifact directories,
  or other internal runtime locations.
- Do not create parent directories implicitly.
- Allow `--create-dir` only for reviewed explicit output directories.
- Do not overwrite existing standard files unless `--overwrite` is explicit.
- Block unplanned files in the target directory.

The CLI mirrors the write-plan and library-writer policies rather than
duplicating weaker path checks.

## Safety boundary

The command preserves:

- no solver execution;
- no CalculiX `ccx` invocation;
- no artifact copying by default or by hidden behavior;
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
- no dependency install or upgrade;
- no `.frd` numerical field parsing;
- no `.frd` value array parsing;
- no mesh reconstruction;
- no field reconstruction;
- no free-form `.dat` parser;
- no unit inference;
- no engineering correctness claims.

## Relationship to issue #8

The write CLI does not validate live `ccx`. Issue `#8` remains open until a
separate prepared-machine live CalculiX validation gate records passing
evidence. Persisting review files is not live solver validation and must not
close issue `#8`.

## Non-goals

- no GUI write command;
- no solver execution;
- no live `ccx` validation;
- no SolverAdapter or runner integration;
- no subprocess use;
- no ProjectSchema mutation;
- no certification;
- no industrial certification;
- no bundled solver.

## Implementation tests

The future implementation tests defined by this design are now implemented as
focused CLI and guardrail tests.

Implementation tests cover:

- command help;
- default plan-only behavior;
- blocked output directory;
- required limitations acknowledgement;
- required review acknowledgement;
- overwrite acknowledgement;
- create-dir behavior;
- text output;
- JSON output;
- writer invocation mocked or observed;
- writer invocation only after `--write`;
- no writer invocation in plan-only mode;
- no solver execution;
- no artifact copying;
- no issue, release, asset, tag, or ProjectSchema mutation.

## Next implementation slices

- `OSW-EXP-045_FEASPEC_RESULT_IMPORT_WRITE_GUI_DESIGN`
- `OSW-EXP-046_FEASPEC_RESULT_IMPORT_WRITE_GUI_IMPLEMENTATION`
- `OSW-VALID-004_LIVE_CALCULIX_RUN_GATE_VALIDATION_IF_INSTALLED`
