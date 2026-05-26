# OpenSolver Workbench Visual QA

## Purpose

This document defines the repeatable visual QA workflow for comparing the
OpenSolver Workbench PySide6 visual shell against the reference Run screen. The
goal of UI-009 is screenshot capture and advisory comparison, not pixel-perfect
polish.

## Reference Image

Reference screenshot:

```text
docs/ui/reference/osw_run_screen.png
```

Use the reference only for QA. Do not embed it in the running application or use
it as a background image.

## Capture Dark Theme

```bash
python tools/ui/capture_main_window.py --theme dark --out artifacts/ui/osw_dark.png --offscreen
```

Dark is the default and should visually resemble the reference most closely.

## Capture Light Theme

```bash
python tools/ui/capture_main_window.py --theme light --out artifacts/ui/osw_light.png --offscreen
```

Light should preserve the same layout, density, and content with readable
contrast.

## Capture System Theme

```bash
python tools/ui/capture_main_window.py --theme system --out artifacts/ui/osw_system.png --offscreen
```

System stores `system` as the selected mode and resolves to the active platform
theme, falling back safely when detection is unavailable.

## Capture All Themes

```bash
python tools/ui/capture_main_window.py --all --out-dir artifacts/ui --offscreen
```

Expected outputs:

```text
artifacts/ui/osw_dark.png
artifacts/ui/osw_light.png
artifacts/ui/osw_system.png
```

## Compare Against Reference

```bash
python tools/ui/compare_reference.py --reference docs/ui/reference/osw_run_screen.png --candidate artifacts/ui/osw_dark.png --out-json artifacts/ui/osw_dark_compare.json --out-diff artifacts/ui/osw_dark_diff.png --resize-candidate
```

The comparison score is advisory. A large mismatch does not fail this step;
UI-010 uses the artifacts for final visual polish.

## Expected Artifact Paths

```text
artifacts/ui/osw_dark.png
artifacts/ui/osw_light.png
artifacts/ui/osw_system.png
artifacts/ui/osw_dark_compare.json
artifacts/ui/osw_dark_diff.png
artifacts/ui/visual_qa_report.json
```

## What Not To Commit

Do not commit generated files under:

```text
artifacts/
```

The repository `.gitignore` excludes that directory. The approved committed
reference image remains:

```text
docs/ui/reference/osw_run_screen.png
```

Do not commit a root-level `GUI.png`.

## Manual QA Checklist

### Layout

- Window size close to 2048 x 1152 reference.
- Top header/toolbar/stepper height close to reference.
- Left project tree width close to reference.
- Right inspector width close to reference.
- Bottom run monitor height close to reference.
- Status bar compact.

### Top Region

- OpenSolver Workbench title visible.
- Subtitle visible.
- Toolbar actions visible.
- Step 4 Run active.
- Steps 1-3 completed.
- Steps 5-6 inactive.

### Left Panel

- PROJECTS header visible.
- HeatSink_Flow tree expanded.
- Geometry/Mesh/Physics/Solvers/Scripts/Results/Reports visible.
- FILTERS search field visible.
- Active Project footer visible.

### Viewport

- View selector shows von Mises Stress.
- Heat sink mock visible.
- Mesh overlay visible.
- Contour overlay visible.
- Legend visible.
- Orientation cube visible.
- Axis triad visible.
- Scale bar visible.

### Run Monitor

- LOG panel visible.
- RESIDUALS chart visible.
- WARNINGS section visible.
- PROGRESS 100% visible.
- OCTAVE / MATLAB FIGURE visible.

### Right Panel

- Properties/Materials/BCS/Advanced tabs visible.
- Material section visible.
- Boundary Conditions table visible.
- Solver Settings visible.
- Plugins section visible.
- Report Preview visible.

### Status Bar

- Solver: chtSolver visible.
- Memory: 6.2 GB / 15.9 GB visible.
- Cores: 12 / 16 visible.
- Ready indicator visible.

### Themes

- Dark resembles reference most closely.
- Light preserves layout and contrast.
- System resolves without crash.
- Runtime theme switching still works from Preferences.

## Known Limitations

- Capture requires the optional PySide6 GUI dependency.
- Image comparison requires Pillow.
- The comparison utility reports basic image metrics only and does not understand
  semantic layout regions.
- Pixel mismatch is expected before UI-010.

## Next Step

UI-010_FINAL_POLISH_PASS
