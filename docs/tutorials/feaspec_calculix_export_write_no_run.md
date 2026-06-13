# FEASpec CalculiX export write no-run

This tutorial writes a local FEASpec CalculiX no-run export bundle when the
input is writer-ready. It does not execute CalculiX and does not validate a
local `ccx` installation.

## Requirements

- OpenSolver Workbench source checkout or installed package.
- Python environment with OSW available.
- No CalculiX `ccx` executable is required.
- No external solver is bundled or invoked.

Generated files should stay under an ignored runtime directory such as
`artifacts\tutorials\feaspec-export\`.

## Blocked FEASpec Example

Create a reviewed output directory first:

```powershell
New-Item -ItemType Directory -Force artifacts\tutorials\feaspec-export
```

Run the approved cantilever example:

```powershell
python -m osw.cli feaspec-calculix-export-write --feaspec examples\feaspec\cantilever_beam_approved.json --output-dir artifacts\tutorials\feaspec-export --basename cantilever_case
```

Expected result:

- exit code `2`;
- export status is `blocked`;
- diagnostics include the missing explicit mesh/topology requirement;
- `files_written` remains false;
- `solver_execution_performed` remains false;
- no `.inp`, manifest, diagnostics JSON, or README bundle is written.

The approved example is intentionally blocked until explicit reviewed mesh and
element topology exist.

## Candidate Example

```powershell
python -m osw.cli feaspec-calculix-export-write --feaspec examples\feaspec\cantilever_beam_candidate.json --output-dir artifacts\tutorials\feaspec-export
```

Expected result:

- exit code `2`;
- diagnostics explain that human review and approval are required;
- no bundle files are written.

## JSON Output

```powershell
python -m osw.cli feaspec-calculix-export-write --feaspec examples\feaspec\invalid_load_target.json --output-dir artifacts\tutorials\feaspec-export --format json
```

The JSON output includes:

- `export_status`;
- `files_written`;
- `solver_execution_performed: false`;
- `written_files`;
- `diagnostics`;
- `limitations`.

## Successful Ready Case Plan

The `--case-plan` path is experimental and intended for reviewed
`FEASpecCalculiXCasePlan` JSON records that already contain explicit node,
element, material, section, boundary-condition, load, step, and output-request
data.

```powershell
python -m osw.cli feaspec-calculix-export-write --case-plan path\to\ready_case_plan.json --output-dir artifacts\tutorials\feaspec-export --basename ready_case
```

When successful, the output directory contains exactly:

- `ready_case.inp`
- `ready_case.manifest.json`
- `ready_case.diagnostics.json`
- `README_RUN_FIRST.txt`

The README and manifest both record that no solver execution was performed.

## Output Directory Controls

Missing output directories block by default:

```powershell
python -m osw.cli feaspec-calculix-export-write --case-plan path\to\ready_case_plan.json --output-dir artifacts\tutorials\new-export
```

Use `--create-dir` to create the final directory explicitly:

```powershell
python -m osw.cli feaspec-calculix-export-write --case-plan path\to\ready_case_plan.json --output-dir artifacts\tutorials\new-export --create-dir
```

Existing target files block by default. Use `--overwrite` only after reviewing
the target directory. It overwrites expected bundle files only and does not
delete unrelated files.

## Safety Boundary

This tutorial covers local no-run export only:

- no solver execution;
- no `ccx`;
- no SolverAdapter or runner handoff;
- no subprocess;
- no external command;
- no ProjectSchema mutation;
- no VLM provider or API call.

Issue `#8` live CalculiX validation remains separate and should only be run on
a prepared machine where `ccx` is already installed.
