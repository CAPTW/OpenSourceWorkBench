# GUI aggregate timeout hardening

## Status

`completed`

This maintenance note records the post-`v0.1.5-rc1` policy for handling a
recurring GUI aggregate pytest timeout in the local release environment. It is
documentation and QA-tooling hardening only.

## v0.1.5-rc1 maintenance context

- `v0.1.5-rc1` is a public prerelease.
- The post-public asset download audit passed.
- The public release body note was corrected after the audit.
- Live optional validation issues `#6` through `#11` remain open.
- Issue `#8` remains `skipped-missing` because `ccx` was absent in the local
  installed-only audit.

## Aggregate timeout behavior

The aggregate command:

```powershell
.venv\Scripts\python.exe -m pytest tests/gui -q
```

can time out in this environment even when the GUI files pass when executed one
file at a time. A timeout is not the same as a failed test assertion or an
import/collection failure.

## Policy

- An aggregate GUI pass is sufficient.
- An aggregate GUI failure is blocking.
- An aggregate GUI timeout is warning-only only if a full deterministic
  per-file fallback passes.
- The fallback must cover every `tests/gui/test_*.py` file, not a selected
  subset.
- Every fallback file must pass or report an expected skip.
- A partial fallback, missing GUI file, failed GUI file, or collection failure
  is blocking.
- The fallback path executes pytest only. It does not run solvers, solver
  adapters, external solver commands, or release operations.

## Fallback command

Use the tracked helper after an aggregate timeout:

```powershell
.venv\Scripts\python.exe tools/qa/run_gui_per_file_fallback.py
```

List the deterministic file set without running pytest:

```powershell
.venv\Scripts\python.exe tools/qa/run_gui_per_file_fallback.py --list-only
```

Optionally write a caller-selected JSON summary:

```powershell
.venv\Scripts\python.exe tools/qa/run_gui_per_file_fallback.py --json-summary artifacts/qa/gui_per_file_fallback_summary.json
```

The helper does not write a summary unless `--json-summary` is supplied.

## Non-actions

- No solver execution.
- No release edit, create, publish, asset upload, asset delete, or asset
  replacement.
- No issue creation, comment, or closure.
- No dependency installation or upgrade.
- No runtime source, GUI behavior, or CLI behavior mutation.
