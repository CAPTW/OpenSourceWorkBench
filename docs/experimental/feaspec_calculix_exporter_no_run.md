# FEASpec CalculiX no-run exporter

Status: experimental no-run exporter implemented. It performs no solver execution,
no `ccx` invocation, no SolverAdapter call, no runner call, and no subprocess
use.

Related release: `v0.1.4-rc1`

## Release Context

`v0.1.4-rc1` is a public prerelease. This implementation is post-release
development on `develop`; it does not edit the public release, mutate tags,
upload assets, close issues, install solvers, or run live optional validation.

## Package Path

The implementation lives under the experimental FEASpec package:

- `src/osw/experimental/feaspec/calculix_exporter.py`
- `src/osw/experimental/feaspec/calculix_export_diagnostics.py`

The public package exports the no-run exporter API from
`osw.experimental.feaspec`.

Follow-up CLI preview evidence:
[FEASpec CalculiX exporter CLI preview](feaspec_calculix_exporter_cli_preview.md)
adds `feaspec-calculix-export-preview`, a diagnostic-only command that previews
validation, bridge, case-plan, in-memory render status, and planned bundle file
names without calling the write-capable exporter path.

Follow-up CLI write evidence:
[FEASpec CalculiX exporter CLI write no-run](feaspec_calculix_exporter_cli_write_no_run.md)
adds `feaspec-calculix-export-write`, an explicit caller-output-directory
command that writes the local no-run bundle only when exporter diagnostics
permit it. The CLI write path still performs no solver execution, no `ccx`
validation, no SolverAdapter handoff, no runner handoff, no subprocess use, and
no ProjectSchema mutation.

Follow-up result/run gate design:
[FEASpec CalculiX result import and run gate design](feaspec_calculix_result_import_or_run_gate_design.md)
keeps export, human review, installed-only run, result import, and
ResultDataset/report summary as separate future gates. It is design-only and
does not add result import code, run commands, SolverAdapter/runner/subprocess
calls, solver execution, live issue `#8` validation, or release mutation.

## Public API

The exporter exposes:

- `export_calculix_case`
- `export_calculix_case_from_feaspec`
- `export_calculix_case_from_bridge`
- `explain_calculix_export_result`

The result and manifest objects are:

- `FEASpecCalculiXExportResult`
- `FEASpecCalculiXExportStatus`
- `FEASpecCalculiXExportManifest`
- `FEASpecCalculiXExportedFile`
- `FEASpecCalculiXExportDiagnostic`

Every export result keeps `ready_for_solver_execution=false` and
`solver_execution_performed=false`.

## Export Bundle

When a case plan renders successfully, the exporter writes exactly this bundle
to the caller-provided output directory:

- `<basename>.inp`
- `<basename>.manifest.json`
- `<basename>.diagnostics.json`
- `README_RUN_FIRST.txt`

The `.inp` text comes from `render_calculix_inp`. The exporter does not modify
the rendered text and does not add tracked generated `.inp` files.

## Safety Behavior

The exporter is a reviewed file bundle boundary:

- no solver run;
- no external command;
- no SolverAdapter;
- no runner;
- no subprocess;
- safe basename checks;
- missing-directory checks;
- non-directory checks;
- nonempty-directory guard;
- overwrite guard for existing target files.

`overwrite=True` overwrites only the known target files for the requested
basename and `README_RUN_FIRST.txt`. It does not delete unrelated files.

`create_dir=True` may create the final output directory when its parent already
exists. Parent directory creation remains explicit caller responsibility.

## Manifest Fields

The manifest records:

- exporter module;
- OSW version;
- release tag context;
- target solver;
- source FEASpec id;
- case-plan id;
- `solver_execution_performed: false`;
- `ready_for_solver_execution: false`;
- generated bundle file names;
- SHA-256 digests;
- byte sizes;
- limitations.

Limitations state that no solver run was performed, no certification or
production CAE claim is made, CalculiX is not bundled, issue `#8` remains
separate, and the exporter is experimental.

## Diagnostics

The exporter uses the `FX_*` diagnostic catalog:

- `FX_RENDER_BLOCKED`
- `FX_OUTPUT_DIR_MISSING`
- `FX_OUTPUT_DIR_NOT_DIRECTORY`
- `FX_OUTPUT_DIR_NOT_EMPTY`
- `FX_UNSAFE_BASENAME`
- `FX_OUTPUT_EXISTS`
- `FX_WRITE_FAILED`
- `FX_MANIFEST_WRITE_FAILED`
- `FX_DIAGNOSTICS_WRITE_FAILED`
- `FX_README_WRITE_FAILED`
- `FX_CHECKSUM_FAILED`
- `FX_SOLVER_RUN_FORBIDDEN`

Blocked render results write no files. Filesystem blockers write no bundle
files before the target checks pass. Diagnostics JSON preserves both exporter
diagnostics and renderer diagnostics for review.

## Example Behavior

Focused tests cover a synthetic writer-ready case that exports into pytest
`tmp_path` and verifies:

- exactly four bundle files;
- parsed manifest JSON;
- parsed diagnostics JSON;
- SHA-256 and byte-size metadata;
- README no-run warnings;
- `.inp` text equality with the renderer output.

Approved FEASpec examples without explicit mesh topology still block with
renderer diagnostics. Candidate and invalid examples also remain blocked before
export.

The CLI preview command reports those same blocked states without writing an
export bundle or creating output directories.

The CLI write command reports those blocked states with exit code `2` and still
writes no bundle files. Successful CLI write coverage uses synthetic
writer-ready case-plan JSON in pytest temporary directories.

## Relationship To Issue #8

Issue `#8` is live CalculiX `ccx` validation and remains separate. This
exporter does not validate installed `ccx`, does not run live optional
validation, and does not close issue `#8`.

Live CalculiX validation remains separate from this exporter.

## Non-Goals

- No solver run.
- No `ccx` invocation.
- No SolverAdapter integration.
- No runner integration.
- No ProjectSchema mutation.
- No VLM API, provider client, credentials, or API keys.
- No release edit, release publish, tag mutation, or asset upload.
- No production certification.
- No bundled external solver.
- No Abaqus export.
- No topology optimization.

## Next Implementation Slices

- `OSW-EXP-017_FEASPEC_CALCULIX_EXPORTER_RESULT_IMPORT_OR_RUN_GATE_DESIGN`
- `OSW-EXP-018_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
- `OSW-EXP-019_FEASPEC_CALCULIX_RESULT_IMPORT_MODEL`
- `OSW-EXP-020_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
