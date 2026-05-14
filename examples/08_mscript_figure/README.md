# Tutorial 08: MATLAB/Octave Figure Preview

## Goal

Preview a `.m` script safely, surface risky commands before execution, and
capture PNG/SVG figure artifacts only after explicit user-approved execution.

## Prerequisites

- Base OSW development install for preview and safety scanning.
- Optional GNU Octave only if the user explicitly runs the reviewed Octave
  runner.
- Optional Matplotlib stack for later plot viewing/report integration.

Security warning: `.m` imports are preview-first. Importing `simple_plot.m`
must never execute code. Treat script output as untrusted until it is previewed,
reviewed, and explicitly accepted.

## Steps

1. Preview the script and safety scan:

   ```python
   from pathlib import Path

   from osw.scripts.mscript.importer import import_mscript_preview

   preview = import_mscript_preview(Path("simple_plot.m"))
   print(preview.to_dict())
   ```

2. Review the classification (`script` or `function`), plot-call detection,
   line counts, and safety findings.
3. Confirm that dangerous commands such as `system`, `unix`, `delete`, `rmdir`,
   `webread`, `urlread`, and risky file mutation are absent or explicitly
   acknowledged.
4. Only after explicit approval, run through the reviewed Octave runner and
   collect generated PNG/SVG outputs.
5. Convert accepted image paths into a `FigureDataset` for plot viewer and
   report placeholders:

   ```python
   from pathlib import Path

   from osw.scripts.mscript.figure_capture import capture_existing_figures

   figures = capture_existing_figures(
       [Path("simple_plot.png"), Path("simple_plot.svg")],
       dataset_id="simple-plot",
       source="simple_plot.m",
   )
   print(figures.to_dict())
   ```

## Expected Output

- A preview model showing script/function classification, line counts, and
  whether plot calls are present.
- Safety findings for risky shell, network, or file mutation commands.
- Optional PNG and SVG figures only when the user explicitly executes the
  script through the reviewed runner path.
- A `FigureDataset` containing figure id, title placeholder, image path, axes
  placeholder, and report-friendly metadata.

## Troubleshooting

- `.m` file missing or wrong extension: pass a real `.m` file to the preview
  importer.
- Safety scan warnings are not fatal by themselves, but they must be reviewed
  before execution.
- Missing Octave is acceptable for preview-only work; record the diagnostic
  instead of bypassing the runner.
- Do not add generated PNG/SVG runtime outputs to the repository unless they are
  deliberately curated fixtures.
