# FEASpec human review CLI

This tutorial records FEASpec human-review decisions with CLI commands. It is
safe for a base Python environment: no external solver is required, no
CalculiX command is run, and no export bundle is written.

`v0.1.4-rc1` is a public prerelease. FEASpec and VFEA workflows remain
experimental and are not industrial-certified or stable production workflows.

## Commands

The review commands are:

- `python -m osw.cli feaspec-human-review-create`
- `python -m osw.cli feaspec-human-review-validate`
- `python -m osw.cli feaspec-human-review-summary`

Generated review JSON files in this tutorial should go under
`artifacts/tutorials/`, which is ignored runtime output.

## Needs Changes

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\tutorials\review-needs-changes.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action needs-changes --notes "Review explicit mesh topology before export."
```

## Reject

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\tutorials\review-rejected.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action reject --reject-diagnostic FS_LOAD_TARGET_INVALID:"Load target must be corrected."
```

## Approve No-Run Export

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\tutorials\review-approved-export.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action approve-no-run-export --validator-summary "{\"has_blockers\":false,\"has_errors\":false,\"diagnostics\":[]}" --validator-report-hash sha256:validator --bridge-summary "{\"status\":\"ready\"}" --case-plan-summary "{\"status\":\"ready\"}" --export-preview-summary "{\"status\":\"ready\"}"
```

This records approval evidence only. It does not write a CalculiX bundle and
does not run `ccx`.

## Request Installed-Only Run

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\tutorials\review-run-request.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action request-installed-only-run --validator-summary "{\"has_blockers\":false,\"has_errors\":false,\"diagnostics\":[]}" --validator-report-hash sha256:validator --bridge-summary "{\"status\":\"ready\"}" --case-plan-summary "{\"status\":\"ready\"}" --export-preview-summary "{\"status\":\"ready\"}" --export-write-summary "{\"status\":\"written\"}" --acknowledge-limitations --acknowledge-readme --acknowledge-run-gate-separate
```

An installed-only run request is not a solver run. The run gate remains a
separate future workflow, and issue `#8` live CalculiX validation remains
separate.

## Validate And Summarize

```powershell
python -m osw.cli feaspec-human-review-validate --record artifacts\tutorials\review-approved-export.json
python -m osw.cli feaspec-human-review-summary --record artifacts\tutorials\review-approved-export.json --format json
```

Validation and summary commands read review JSON only. They write no files,
call no SolverAdapter, call no runner, invoke no subprocess, mutate no
ProjectSchema, and execute no solver.

## Boundaries

- No GUI implementation.
- No result import implementation.
- No installed-only run gate implementation.
- No live optional validation.
- No bundled external solver.
- No industrial certification.
