# FEASpec CalculiX exporter CLI preview

Status: experimental preview command. It reports no files written by default
and performs no solver execution.

Related release context: `v0.1.4-rc1` is a public prerelease. This CLI preview
is post-release development on `develop`; it does not edit the public release,
mutate tags, upload assets, close issues, install solvers, or run live optional
validation.

## Command

Command name:

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\cantilever_beam_approved.json
```

Options:

- `--feaspec PATH`: required FEASpec JSON input.
- `--target-solver calculix`: target solver planning path; currently bounded to
  CalculiX.
- `--format text|json`: default `text`; JSON is intended for automation and
  tests.
- `--strict`: returns exit code `2` when export preview is blocked.
- `--basename NAME`: planned bundle basename used only for displayed file names.
- `--planned-output-dir PATH`: planned output directory used only for displayed
  file names.

The command does not create the planned output directory.

## Text Output

Text output is reviewer-facing and reports:

- validation status;
- bridge status;
- case-plan status;
- in-memory render status if render is safe to attempt;
- export preview status;
- planned files;
- diagnostics;
- `files_written: false`;
- `solver_execution_performed: false`;
- limitations.

It clearly states that no solver execution occurred, no files were written,
external solvers are optional and not bundled, and issue `#8` live CalculiX
validation remains separate.

## JSON Output

JSON output is parseable and includes:

- `version`;
- `input_path`;
- `target_solver`;
- `validation_status`;
- `bridge_status`;
- `case_plan_status`;
- `export_preview_status`;
- `planned_files`;
- `diagnostics`;
- `solver_execution_performed: false`;
- `files_written: false`;
- `limitations`.

The JSON shape is diagnostic-first. A blocked preview is still a successful
preview command unless `--strict` is supplied.

## Example Commands

Approved cantilever example:

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\cantilever_beam_approved.json --basename cantilever_preview
```

This example is approved but still blocks export readiness until reviewed mesh
and element topology exist.

Candidate example:

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\cantilever_beam_candidate.json
```

Candidate input remains blocked until human review and approval are recorded.

JSON preview:

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\invalid_load_target.json --format json
```

Strict mode:

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\cantilever_beam_approved.json --strict
```

Strict mode exits `2` when preview diagnostics block export readiness.

## Output Meaning

`validation_status` comes from the FEASpec validator. `bridge_status` comes from
the FEASpec-to-ProjectSchema draft-plan layer. `case_plan_status` comes from the
CalculiX case-plan model. `export_preview_status` is `blocked`,
`ready-with-warnings`, or `ready` based on those no-run planning layers and any
in-memory renderer diagnostics.

`planned_files` lists the bundle names that a future explicit write command
would target:

- `<basename>.inp`
- `<basename>.manifest.json`
- `<basename>.diagnostics.json`
- `README_RUN_FIRST.txt`

The preview does not create those files.

## Safety Boundary

The CLI preview performs:

- no file writes;
- no `.inp`;
- no manifest;
- no diagnostics JSON file;
- no README;
- no ccx;
- no SolverAdapter;
- no runner;
- no subprocess;
- no ProjectSchema mutation;
- no VLM provider or API call;
- no credential handling.

The preview may read a FEASpec JSON file and create in-memory validator, bridge,
case-plan, and renderer diagnostics. It may render text in memory only when the
case plan is already writer-ready.

## Relationship To Issue #8

Issue `#8` remains live CalculiX `ccx` validation. This preview does not
validate installed `ccx`, does not run live optional validation, and does not
close issue `#8`.

Live CalculiX validation remains separate from the CLI preview.

## Non-Goals

- No solver execution.
- No bundled solver.
- No industrial certification.
- No production-readiness claim.
- No release edit, release publish, tag mutation, or asset upload.
- No Abaqus export.
- No topology optimization.

## Next Implementation Slices

- `OSW-EXP-016_FEASPEC_CALCULIX_EXPORTER_CLI_WRITE_NO_RUN`
- `OSW-EXP-017_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
- `OSW-EXP-018_FEASPEC_HUMAN_REVIEW_UI_DESIGN`
