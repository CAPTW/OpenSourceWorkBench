# Report Generator Binding

`OSW-FUNC-011_REPORT_GENERATOR_BINDING` binds existing OSW project and preview
data into deterministic, dependency-light reports. It does not execute solvers,
scripts, MATLAB, Octave, or external commands.

## Data Model

Report models live in `osw.post.report_model`:

- `ReportAsset`
- `ReportSection`
- `ReportTable`
- `ReportFigure`
- `ReportSummary`
- `ReportBuildRequest`
- `ReportBuildResult`

All paths serialize as strings, and summaries are JSON-serializable.

## Section Builders

`osw.post.report_sections.build_report_summary()` creates stable report
sections for:

- project metadata and unit system;
- materials, geometry references, mesh summaries, physics, and boundary
  conditions;
- solver settings, plugin health, and execution-environment diagnostics;
- M-Script preview metadata and safety summaries;
- run logs and diagnostics passed as structured result objects;
- MAT and workspace variable summaries;
- FigureDataset figure records and missing-artifact warnings;
- BoundaryCurve summaries and validation notes;
- result references;
- warnings and known limitations.

Missing data produces empty-state rows or warnings instead of crashes.

## Export

`osw.post.report_generator.build_report()` writes HTML, Markdown, or JSON
summary output. HTML is standalone, UTF-8, deterministic, escaped, and has no
external CDN dependency. PDF export remains optional/deferred; no mandatory PDF
dependency is added.

CLI:

```powershell
.venv\Scripts\python.exe -m osw.cli report-export project.json --out artifacts\report\report.html
.venv\Scripts\python.exe -m osw.cli report-summary project.json
.venv\Scripts\python.exe -m osw.cli report-export-demo --out artifacts\report\demo_report.html
```

## GUI Binding

`ReportPreviewPanel` can consume a `ReportSummary` and display the report title,
run label, section list, figure count, and warning count. `MainWindow` routes
Generate Report and Export Report actions through the report generator service.
The GUI does not call subprocess APIs and does not run solvers or scripts.

## Security Rules

- Escape HTML for user-provided strings.
- Do not execute scripts, solvers, MATLAB, Octave, or external commands.
- Do not load remote assets.
- Warn on missing figure/image assets.
- Keep report outputs under `artifacts/report` or test temp directories unless
  explicitly exported elsewhere by the user.

## Known Limitations

- Heavy PDF export is deferred.
- Reports summarize imported/previewed data; they do not prove physical
  validity.
- Missing optional dependencies are surfaced as diagnostics where available.
- Solver adapter sections remain descriptive until bounded solver adapters are
  implemented.

## Next Step

Next functional step: `OSW-FUNC-012_GMSH_ADAPTER`.
