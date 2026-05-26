# M-Script Import Preview

`OSW-FUNC-006_MSCRIPT_IMPORT_PREVIEW` adds preview-first MATLAB/Octave `.m`
import. It reads source text, extracts metadata, and scans for safety concerns.
It does not execute scripts, launch MATLAB, launch Octave, or translate code.

## Purpose

M-Script import is an inspection boundary. OSW can show what a `.m` file appears
to contain before any future execution workflow is considered. Imported preview
metadata can be attached to `ProjectSchema` as a `ScriptRef` while preserving the
completed GUI baseline.

## Data Model

The preview model lives under `src/osw/scripts/mscript`:

- `ScriptKind`: `script`, `function`, `classdef`, or `unknown`.
- `FunctionSignature`: best-effort function name, inputs, outputs, raw
  signature, and line number.
- `PlotHint`: command, line number, and source context for common plot calls.
- `SafetyFinding`: severity, code, message, hint, line number, token, and
  context.
- `ScriptPreview`: source path, language, kind, line/character counts, help
  text, signature, plot hints, safety findings, detected calls, and metadata.

Models are serializable and do not depend on PySide6, MATLAB, Octave, Oct2Py,
SciPy, or hdf5storage.

## Importer

`preview_mscript(path)` and `preview_mscript_text(text)` are text-only. They:

- verify `.m` extension support;
- read UTF-8 text with a replacement-character fallback;
- classify script, function, classdef, or unknown files;
- extract leading help/comment blocks;
- extract common function signatures;
- extract plot hints;
- run the safety scanner;
- return structured diagnostics instead of raw tracebacks for missing,
  unsupported, empty, or limited-support files.

`create_script_ref(preview)` converts the preview into a ProjectSchema
`ScriptRef` with:

- `language: matlab_octave`
- `safe_preview_required: true`
- `status: previewed`
- preview metadata including kind, line count, safety summary, function
  signature, and plot hint count.

## Safety Scan

The scanner is best-effort, conservative, and preview-only. It ignores comments
and string literals where practical and reports one-based line numbers.

High-risk findings include:

- external command tokens: `system`, `unix`, `dos`, shell escape `!`;
- destructive filesystem tokens: `delete`, `rmdir`;
- network/web tokens: `webread`, `webwrite`, `websave`, `urlread`,
  `urlwrite`, `ftp`, `tcpclient`, `udpport`, `serialport`, `web`;
- dynamic execution tokens: `eval`, `evalin`, `feval`, `run`, `source`.

Warnings include:

- file/path/environment access: `fopen`, `fprintf`, `save`, `load`, `diary`,
  `cd`, `addpath`, `rmpath`, `path`, `setenv`, `getenv`;
- Python or Java bridge usage.

Out-of-scope blocked findings include:

- Simulink/App Designer signals: `simulink`, `sim`, `open_system`, `.slx`,
  `.mlapp`.

Findings are warnings for preview/import. No script content is run.

## Plot Hints

Plot hints flag common commands such as `plot`, `scatter`, `bar`, `histogram`,
`figure`, `subplot`, `tiledlayout`, `title`, `xlabel`, `ylabel`, `legend`,
`contour`, `surf`, `mesh`, and `imagesc`.

Hints are used only to show future figure-capture potential. OSW-FUNC-006 does
not generate figures or `FigureDataset` records.

## Built-in Plugin Metadata

`builtin_mscript_preview_plugin_manifest()` declares a data-only built-in plugin
manifest:

- id: `osw.mscript_preview`
- domain: `MATH`
- type: `script_importer`
- input format: `m`
- output formats: `script_preview`, `script_ref`
- capabilities: `m_file_preview`, `function_signature_detection`,
  `safety_scan`, `plot_hint_detection`, `project_script_ref_binding`

The preview importer requires no executable names and does not load plugin code
during discovery or health display.

## CLI

The CLI commands are preview-only:

```powershell
.venv\Scripts\python.exe -m osw.cli mscript-preview tests\fixtures\mscript\simple_plot.m
.venv\Scripts\python.exe -m osw.cli mscript-scan tests\fixtures\mscript\dangerous_system.m
```

Both commands support `--json`. They do not require PySide6, MATLAB, Octave, or
Oct2Py.

## GUI Binding

The GUI adds a safe script preview surface without changing the visual shell:

- `ScriptPreviewDialog`
- `ScriptPreviewPanel`
- `MainWindow.preview_script_file(path)`
- `ProjectTreePanel` continues rendering `ScriptRef` rows under Scripts.
- `PropertiesPanel` can show selected script preview summaries.

There is no Run button and no direct GUI execution path in this step.

## Security Rules

- `.m` files are treated as untrusted source text.
- Import and preview never execute script content.
- GUI preview does not launch MATLAB, Octave, or external commands.
- Simulink, `.slx`, `.mlapp`, `.fig`, `.mat`, and figure capture are deferred
  or out of scope for this step.
- Scanner findings are conservative and may false-positive on complex MATLAB
  syntax; users must review findings before any future execution workflow.

## Known Limitations

- The parser is heuristic, not a full MATLAB grammar.
- Nested functions, package/class method signatures, line continuations, and
  unusual command syntax may be summarized imperfectly.
- Plot hints do not reconstruct figures.
- `.mat`, `.fig`, Simulink, and App Designer workflows are not implemented.

## Next Step

Next functional step: `OSW-FUNC-007_OCTAVE_RUNNER`.
