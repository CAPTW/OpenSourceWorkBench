# FEASpec CalculiX export preview

This tutorial previews whether a FEASpec JSON file is ready for a future
CalculiX no-run export bundle. It does not write `.inp`, manifest, diagnostics,
or README files. It does not execute CalculiX.

## Requirements

- OpenSolver Workbench source checkout or installed package.
- Python environment with OSW available.
- No CalculiX `ccx` executable is required.
- No external solver is bundled or invoked.

## Preview An Approved Example

From the repository root:

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\cantilever_beam_approved.json --basename cantilever_preview
```

Expected result:

- exit code `0`;
- validation status is reported;
- bridge and case-plan status are reported;
- export preview status is reported;
- planned file names are listed;
- `files_written` remains false;
- `solver_execution_performed` remains false.

The approved cantilever example currently blocks export readiness because it
does not include explicit mesh and element topology.

## Preview Candidate Input

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\cantilever_beam_candidate.json
```

Expected result:

- exit code `0`;
- diagnostics explain that human review and approval are required;
- no files are written.

## JSON Preview

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\invalid_load_target.json --format json
```

The JSON output includes:

- `validation_status`;
- `bridge_status`;
- `case_plan_status`;
- `export_preview_status`;
- `planned_files`;
- `diagnostics`;
- `files_written: false`;
- `solver_execution_performed: false`.

## Strict Mode

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\cantilever_beam_approved.json --strict
```

Strict mode returns exit code `2` when the preview is blocked. Without
`--strict`, a blocked preview returns exit code `0` because diagnostics were
reported successfully.

## Planned Output Directory

`--planned-output-dir` only changes displayed planned file paths:

```powershell
python -m osw.cli feaspec-calculix-export-preview --feaspec examples\feaspec\cantilever_beam_approved.json --planned-output-dir artifacts\feaspec-preview
```

The command does not create `artifacts\feaspec-preview` and does not write
runtime export bundles.

## Safety Boundary

This tutorial is preview-only:

- no solver execution;
- no file writes;
- no output directory creation;
- no SolverAdapter or runner handoff;
- no `ccx` validation;
- no ProjectSchema mutation;
- no VLM provider or API call.

Issue `#8` live CalculiX validation remains separate and should only be run on
a prepared machine where `ccx` is already installed.
