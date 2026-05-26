# GNU Octave Runner

`OSW-FUNC-007_OCTAVE_RUNNER` adds explicit GNU Octave execution for previewed
MATLAB/Octave `.m` files. Import and preview remain non-executing. A script can
run only when a caller creates an `OctaveRunRequest` or invokes the matching CLI
command.

## Purpose

The runner is a backend execution boundary for trusted `.m` smoke workflows. It
does not add MATLAB Engine, Oct2Py, figure capture, `.mat` reading, Simulink, or
App Designer support.

## Data Model

The runner model lives under `src/osw/scripts/mscript`:

- `OctaveExecutionPolicy`: timeout, safety overrides, workspace isolation,
  artifact collection, and environment override settings.
- `OctaveRunRequest`: script path, optional preview, workspace, run id, policy,
  arguments, and metadata.
- `OctaveRunResult`: status, command, return code, stdout, stderr, elapsed time,
  workspace, artifacts, safety findings, diagnostics, and metadata.
- `OctaveRunStatus`: `ready`, `blocked_by_safety`, `missing_executable`,
  `running`, `completed`, `failed`, `timed_out`, and `cancelled`.

All models are serializable and do not require PySide6, MATLAB, Octave, Oct2Py,
Matplotlib, or SciPy at import time.

## Executable Detection

`find_octave_executable()` resolves `octave-cli`, `octave`, or `octave.exe`
through `ExecutablePathRegistry`. Detection checks configured paths and `PATH`
only. It does not execute Octave or call `--version`.

If Octave is missing, diagnostics explain that GNU Octave was not found and that
the user can install Octave or configure the path in Plugin Manager.

## Execution Policy

Default policy:

- timeout: 30 seconds
- isolated workspace: enabled
- copy script to workspace: enabled
- artifact collection: enabled
- high-risk findings: blocked
- blocked/out-of-scope findings: blocked

High-risk findings can be allowed only with an explicit policy override.
Blocked findings, including Simulink, `.slx`, and `.mlapp` signals, remain
blocked by default and are out of scope for normal v0.1 execution.

## Workspace Isolation

By default, each run creates a temporary or caller-provided run directory and
copies the `.m` file into that workspace before execution. This prevents normal
runs from mutating the source fixture or project script directory.

The workspace path is included in `OctaveRunResult`.

## Runner Boundary

`OctaveRunner` builds an argument-list command and delegates process execution
to `ExternalCommandRunner`. It does not use shell strings and does not expose a
GUI subprocess path.

The command runner provides:

- stdout/stderr capture
- timeout handling
- nonzero return-code diagnostics
- summary/stdout/stderr artifacts
- generic artifact collection

## Artifact Collection

The runner collects generic files from the Octave workspace using default
patterns such as:

- `*.txt`
- `*.csv`
- `*.png`
- `*.svg`
- `*.pdf`
- `*.mat`
- `*.dat`
- `*.json`

PNG/SVG/PDF files are generic artifacts only in this step. Figure-specific
classification and `FigureDataset` integration are deferred to
`OSW-FUNC-008_FIGURE_CAPTURE_DATASET`.

## CLI

Check whether Octave is configured without executing it:

```powershell
.venv\Scripts\python.exe -m osw.cli octave-check
```

Run a script explicitly:

```powershell
.venv\Scripts\python.exe -m osw.cli mscript-run tests\fixtures\mscript\simple_plot.m
```

Useful options:

- `--timeout SECONDS`
- `--allow-high-risk`
- `--allow-blocked`
- `--workspace PATH`
- `--json`

If Octave is not installed or configured, `mscript-run` returns a friendly
missing-executable diagnostic.

## GUI Binding

`ScriptPreviewDialog` and `ScriptPreviewPanel` expose a Run with Octave action
only after preview data exists. The button is disabled for high-risk or blocked
safety findings by default. When invoked, the panel calls `OctaveRunner`; it
does not call subprocess APIs directly.

The dialog can show run status, a log preview, and diagnostics while preserving
the completed GUI visual shell and theme behavior.

## Security Rules

- Import and preview never execute `.m` code.
- Octave runs require explicit request through `OctaveRunRequest`, CLI
  `mscript-run`, or a user action in the preview dialog.
- Execution is blocked by default for high-risk shell, filesystem mutation,
  network, dynamic execution, Simulink, `.slx`, and `.mlapp` findings.
- The GUI does not launch subprocesses directly.
- Octave executable detection does not execute Octave.
- Plugin health checks may resolve Octave paths, but must not run Octave,
  plugin code, or scripts.

## Known Limitations

- This step does not capture figures as `FigureDataset` records.
- This step does not read `.mat` files.
- This step does not provide MATLAB Engine or Oct2Py integration.
- This step does not implement Simulink, `.slx`, or `.mlapp` support.
- Octave compatibility depends on the user's installed GNU Octave version.

## Next Step

Next functional step: `OSW-FUNC-008_FIGURE_CAPTURE_DATASET`.
