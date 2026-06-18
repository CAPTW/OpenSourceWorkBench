# FEASpec CalculiX result import and run gate design

Status: design-only. There is no result import implementation, no run gate
implementation, and no solver execution in this gate.

## Release Context

`v0.1.4-rc1` is a public prerelease. This design is post-release development on
`develop`; it does not edit the public release, mutate tags, upload assets,
install solvers, close issues, or run live optional validation.

## Relationship To Existing Layers

This design follows the existing experimental FEASpec and CalculiX no-run
layers:

- FEASpec validator: checks candidate and approved FEASpec records before any
  downstream bridge.
- Project bridge: produces a draft plan and diagnostics without ProjectSchema
  mutation.
- CalculiX case plan: preserves reviewed node, element, material, section,
  boundary-condition, load, step, output, and provenance records.
- INP renderer: renders deterministic `.inp` text from writer-ready case plans
  without solver execution.
- No-run exporter: writes a local bundle with `.inp`, manifest JSON,
  diagnostics JSON, and `README_RUN_FIRST.txt` while preserving
  `solver_execution_performed=false`.
- CLI preview/write: expose no-run preview and explicit local bundle writing.
- ResultDataset / report summary concepts: provide summary-first result
  inspection, artifact references, diagnostics, and report handoff after
  result artifacts already exist.

## Safety Principle

There is no automatic unreviewed solver execution. Export, review, run, and
import are separate gates.

The no-run export boundary must not implicitly trigger `ccx`. A generated
bundle is not permission to run a solver. The user must inspect FEASpec
evidence, generated `.inp` text, diagnostics, manifest metadata, and
`README_RUN_FIRST.txt` before any future installed-only run gate is requested.

## Recommended Sequence

1. FEASpec human review.
2. No-run export preview.
3. No-run export write.
4. Optional manual inspection of `.inp`, manifest, diagnostics, and README.
5. Installed-only run gate.
6. Result import gate.
7. ResultDataset/report summary.

The sequence is intentionally staged so that a blocked or suspicious result at
any gate stops the workflow before mutation, execution, or import.

## Human Review Record Evidence

The [FEASpec human review record model](feaspec_human_review_record_model.md)
now captures reviewer identity, action, state, validator summary/hash,
accepted-warning reasons, diagnostic decisions, bridge/case/export summaries,
and solver-execution flags as experimental JSON-serializable evidence.

The [FEASpec human review CLI approval](feaspec_human_review_cli_approval.md)
workflow can now create, validate, and summarize those JSON review records. It
does not implement a GUI, run gate, result importer, SolverAdapter handoff,
runner handoff, subprocess path, or solver execution. It can support future
provenance for this sequence, but the run gate remains separate and issue `#8`
remains open until installed-only validation passes.

The
[FEASpec human review GUI dialog design](feaspec_human_review_gui_dialog_design.md)
maps the same record states and CLI evidence into a future OSW dialog contract.
It covers future entry points, diagnostic panels, warning acceptance, approval
gating, record preview, and save behavior only. It does not implement GUI
source, result import, a run gate, SolverAdapter or runner behavior,
subprocess calls, ProjectSchema mutation, VLM APIs, dependency installation, or
solver execution.

## Installed-Only Run Gate Preconditions

A future installed-only run gate may proceed only when all preconditions are
true:

- the user explicitly requests the run gate;
- `ccx` is installed and discovered on the prepared machine;
- the no-run export bundle exists;
- `README_RUN_FIRST.txt` has been reviewed;
- the export manifest exists and records `solver_execution_performed=false`
  before the run;
- the output directory is isolated from source, release, tag, and user data;
- a short timeout is configured;
- there is no release mutation;
- there is no tag push;
- there is no hidden solver install.

The run gate must be installed-only. It must not download, install, bundle, or
silently configure external solvers.

## Installed-Only Run Gate Outputs

A future run gate should write only ignored runtime artifacts under an explicit
run directory:

- run metadata JSON;
- stdout and stderr logs;
- exit code;
- generated CalculiX files if any;
- updated run manifest;
- no tracked solver outputs.

The run metadata should preserve the export manifest hash, `.inp` file hash,
`ccx` discovery details, timeout policy, command argv, working directory, exit
status, and artifact list.

## Run Gate Diagnostics

Future run gate diagnostics reserve these codes:

- `FR_RUN_NOT_AUTHORIZED`
- `FR_CCX_MISSING`
- `FR_EXPORT_BUNDLE_INVALID`
- `FR_MANIFEST_MISSING`
- `FR_README_NOT_REVIEWED`
- `FR_TIMEOUT`
- `FR_NONZERO_EXIT`
- `FR_OUTPUT_MISSING`
- `FR_FORBIDDEN_PATH`

These diagnostics must be user-facing and serializable. Blocking diagnostics
must prevent execution.

## Result Import Boundary

Result import may import only from an explicit result directory. Result import
does not execute solver commands, does not call `ccx`, does not mutate releases
or assets, and does not overwrite user data.

The import gate consumes already-collected artifacts. It may create a
ResultDataset draft and parser diagnostics in memory or in an explicit caller
path in a later implementation gate, but it must not launch or retry solver
runs.

## Result Import Inputs

The future result import gate may inspect:

- `.dat`
- `.frd`
- `.sta`
- `.cvg`
- stdout/stderr logs
- export manifest
- run metadata

Missing files should produce diagnostics rather than raw tracebacks. Partial
artifacts should remain visible as partial evidence.

## Result Import Outputs

The future result import gate should produce:

- ResultDataset draft;
- solver run summary;
- artifact manifest;
- parser diagnostics;
- provenance links to FEASpec, export, and run metadata.

The initial result import can remain summary-first: scalar displacement/stress
summaries, status tables, artifact references, limitations, and provenance are
more important than full field visualization.

## Result Import Diagnostics

Future result import diagnostics reserve these codes:

- `FI_RESULT_DIR_MISSING`
- `FI_MANIFEST_MISSING`
- `FI_RUN_METADATA_MISSING`
- `FI_UNSUPPORTED_FILE`
- `FI_PARSE_FAILED`
- `FI_PARTIAL_IMPORT`
- `FI_NO_PRIMARY_RESULT`
- `FI_PROVENANCE_INCOMPLETE`

Parser diagnostics must distinguish missing artifacts, unsupported files,
partial import, and provenance gaps.

## ResultDataset Mapping

Result import should map reviewed CalculiX artifacts into ResultDataset concepts:

- scalar summaries for values such as maximum displacement and maximum stress;
- tables for status, increments, warnings, and parser summaries;
- artifacts for `.dat`, `.frd`, `.sta`, `.cvg`, logs, manifests, and metadata;
- field references for deferred field-capable artifacts;
- provenance links to FEASpec, export manifest, run metadata, and parser
  evidence;
- limitations that state the path is experimental and not certified.

Field-heavy outputs should remain references or summaries until a later parser
and visualization gate explicitly supports them.

## Relationship To Issue #8

Issue `#8` remains open until installed-only `ccx` validation passes on a
prepared machine. This design does not run live optional validation, does not
validate a local `ccx` executable, and does not close issue `#8`.

## CLI Future

Future CLI command names may be:

- `feaspec-human-review-create`
- `feaspec-human-review-validate`
- `feaspec-human-review-summary`
- `feaspec-calculix-run-installed-only`
- `feaspec-calculix-result-import`

The human-review commands are record-only and do not run solvers. The run and
import commands are future only. This gate does not implement either command.

The future run command must require explicit authorization, an export bundle,
reviewed README status, isolated output directory, timeout, and installed
`ccx`. The future import command must require an explicit result directory and
must not execute any solver.

## Security And Path Safety

Future gates must use explicit directories only:

- no path traversal;
- no hidden parent creation unless authorized;
- no system-wide writes;
- no release directories;
- no tag or asset directories;
- no overwriting user data without explicit review.

Runtime outputs must remain ignored unless a later gate deliberately curates a
small fixture under an approved tests path.

## Non-Goals

- No implementation.
- No solver execution.
- No result parser implementation.
- No live validation.
- No certification.
- No bundled solver.
- No release mutation.
- No tag mutation.
- No asset upload.
- No SolverAdapter handoff.
- No runner handoff.
- No subprocess or external command invocation.
- No ProjectSchema mutation.
- No VLM API, provider client, credentials, or API keys.
- No Abaqus export.
- No topology optimization.

## Future Implementation Slices

- `OSW-EXP-018_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
- `OSW-EXP-019_FEASPEC_CALCULIX_RESULT_IMPORT_MODEL`
- `OSW-EXP-020_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
- `OSW-EXP-021_FEASPEC_CALCULIX_RESULT_IMPORT_CLI`
