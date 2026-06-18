# FEASpec human review CLI approval

## Status

- Experimental CLI record workflow.
- No GUI implementation.
- No solver execution.
- No result import implementation.
- No installed-only run gate implementation.

This gate adds CLI commands that create, validate, and summarize FEASpec human
review JSON records. The commands preserve review evidence only. Approval is
not solver execution, and an installed-only run request is not a run.

## Release Context

`v0.1.4-rc1` is a public prerelease. This implementation is post-release
development on `develop`; it does not edit the public release, mutate tags,
upload assets, close issues, install dependencies, install solvers, or run live
optional validation.

The package and CLI version remain `0.1.4rc1`.

## Commands

The exact command names are:

- `feaspec-human-review-create`
- `feaspec-human-review-validate`
- `feaspec-human-review-summary`

Each command supports text output by default and `--format json` for automation
and tests.

## Create Command

Command shape:

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\review.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action needs-changes
```

Required arguments:

- `--output PATH`
- `--source-feaspec-id ID`
- `--reviewer NAME`
- `--reviewed-at ISO_TIMESTAMP`
- `--action needs-changes|reject|approve-no-run-export|request-installed-only-run`

Optional evidence arguments:

- `--notes TEXT`
- `--validator-report-hash HASH`
- `--validator-summary PATH_OR_JSON`
- `--bridge-summary PATH_OR_JSON`
- `--case-plan-summary PATH_OR_JSON`
- `--export-preview-summary PATH_OR_JSON`
- `--export-write-summary PATH_OR_JSON`
- `--accept-warning CODE:REASON`
- `--reject-diagnostic CODE:REASON`
- `--acknowledge-limitations`
- `--acknowledge-readme`
- `--acknowledge-run-gate-separate`
- `--format text|json`
- `--overwrite`

Accepted warning syntax is `CODE:REASON`. The reason is required. Diagnostic
decision syntax is also `CODE:REASON`.

The create command validates the record before writing. Invalid approval
records are refused and no review file is written. Writes use only the explicit
`--output` path, refuse overwrite unless `--overwrite` is supplied, and do not
create parent directories implicitly.

## Validate Command

Command shape:

```powershell
python -m osw.cli feaspec-human-review-validate --record artifacts\review.json
```

Required arguments:

- `--record PATH`

Optional arguments:

- `--format text|json`
- `--strict`

The validate command loads one review JSON file, validates the record, prints
diagnostics, writes no files, and runs no solver.

Exit codes:

- `0`: record is valid.
- `2`: record is readable but invalid.
- `1`: unreadable input, invalid JSON, or command error.

## Summary Command

Command shape:

```powershell
python -m osw.cli feaspec-human-review-summary --record artifacts\review.json
```

Required arguments:

- `--record PATH`

Optional arguments:

- `--format text|json`

The summary command prints state, action, source FEASpec id, reviewer,
reviewed timestamp, solver-execution flags, diagnostics, and limitations. It
writes no files and runs no solver.

## Review Boundaries

- Approval is not solver execution.
- Installed-only run request is not a run.
- No-run export preview and no-run export write remain separate commands.
- Result import remains a separate future gate.
- Issue `#8` live CalculiX validation remains separate and open until a
  prepared installed-only validation gate passes.

The CLI can record reviewer intent for a future installed-only run request, but
it cannot execute CalculiX and cannot mark solver execution as performed.

## Safety

The human-review CLI commands perform:

- no `ccx` invocation;
- no SolverAdapter call;
- no runner call;
- no subprocess or external command invocation;
- no ProjectSchema mutation;
- no GUI mutation;
- no result import;
- no VLM API or provider call;
- no credentials or API keys;
- no dependency install or upgrade.

## Examples

Needs changes:

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\review-needs-changes.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action needs-changes --notes "Mesh topology needs review."
```

Reject:

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\review-rejected.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action reject --reject-diagnostic FS_LOAD_TARGET_INVALID:"Load target is not present in reviewed topology."
```

Approve no-run export:

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\review-approved-export.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action approve-no-run-export --validator-summary "{\"has_blockers\":false,\"has_errors\":false,\"diagnostics\":[]}" --validator-report-hash sha256:validator --bridge-summary "{\"status\":\"ready\"}" --case-plan-summary "{\"status\":\"ready\"}" --export-preview-summary "{\"status\":\"ready\"}"
```

Request installed-only run:

```powershell
python -m osw.cli feaspec-human-review-create --output artifacts\review-run-request.json --source-feaspec-id cantilever-approved --reviewer reviewer@example.test --reviewed-at 2026-06-18T00:00:00Z --action request-installed-only-run --validator-summary "{\"has_blockers\":false,\"has_errors\":false,\"diagnostics\":[]}" --validator-report-hash sha256:validator --bridge-summary "{\"status\":\"ready\"}" --case-plan-summary "{\"status\":\"ready\"}" --export-preview-summary "{\"status\":\"ready\"}" --export-write-summary "{\"status\":\"written\"}" --acknowledge-limitations --acknowledge-readme --acknowledge-run-gate-separate
```

Validate:

```powershell
python -m osw.cli feaspec-human-review-validate --record artifacts\review-approved-export.json
```

Summary:

```powershell
python -m osw.cli feaspec-human-review-summary --record artifacts\review-approved-export.json --format json
```

## JSON Output

JSON output includes:

- `command`
- `status`
- `valid`
- `record_path`
- `source_feaspec_id`
- `reviewer`
- `reviewed_at`
- `state`
- `action`
- `solver_execution_performed`
- `solver_execution_authorized`
- `files_written`
- `diagnostics`
- `limitations`

`solver_execution_performed` remains `false`.

## Text Output

Text output states:

- no solver execution was performed;
- run gate remains separate;
- no-run export remains separate;
- result import remains separate;
- external solvers are optional and not bundled;
- issue `#8` live validation remains separate for installed-only run requests.

## Exit Codes

Create:

- `0`: valid review record written.
- `2`: validation-blocked record, no write.
- `1`: invalid arguments, unreadable evidence input, or write failure.

Validate:

- `0`: valid record.
- `2`: invalid record.
- `1`: unreadable input, invalid JSON, or command error.

Summary:

- `0`: readable record summarized.
- `1`: unreadable input, invalid JSON, or command error.

## Non-Goals

- No GUI implementation.
- No run gate implementation.
- No result import implementation.
- No CalculiX execution.
- No live `ccx` validation.
- No SolverAdapter integration.
- No runner integration.
- No subprocess or external command invocation.
- No ProjectSchema mutation.
- No VLM API or credentials.
- No topology optimization.
- No Abaqus exporter.
- No industrial certification.
- No stable production claim.
- No bundled external solver.

## Next Implementation Slices

- `OSW-EXP-021_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_DESIGN`
- `OSW-EXP-022_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_VIEWMODEL`
- `OSW-EXP-023_FEASPEC_HUMAN_REVIEW_GUI_DIALOG_IMPLEMENTATION`
- `OSW-EXP-024_FEASPEC_HUMAN_REVIEW_GUI_SAVE_INTEGRATION`
- `OSW-EXP-025_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`

The follow-up
[FEASpec human review GUI dialog design](feaspec_human_review_gui_dialog_design.md)
maps this CLI record workflow into future OSW dialog states, panels, disabled
actions, warning acceptance, record preview, and save behavior. It remains
design-only and does not implement GUI classes, result import, a run gate,
SolverAdapter or runner paths, subprocess calls, ProjectSchema mutation, VLM
APIs, dependency installation, or solver execution.

[FEASpec human review GUI dialog view-model](feaspec_human_review_gui_dialog_viewmodel.md)
implements the pure Python state/action layer for that future GUI. It preserves
the same record actions, diagnostic decisions, accepted-warning reasons, save
path review, and no-run/run-gate separation while still avoiding PySide/Qt
imports, GUI classes, result import, a run gate, SolverAdapter or runner
behavior, subprocess calls, ProjectSchema mutation, VLM APIs, dependency
installation, and solver execution.

[FEASpec human review GUI dialog implementation](feaspec_human_review_gui_dialog_implementation.md)
adds a read-only PySide6 dialog bound to the view-model. It renders panels,
diagnostics, warning rows, disabled action reasons, safety copy, and record
preview only. It adds no record save integration, no file dialog, no result
import implementation, no installed-only run gate implementation, no
SolverAdapter or runner behavior, no subprocess calls, no ProjectSchema
mutation, no VLM APIs, and no solver execution.
