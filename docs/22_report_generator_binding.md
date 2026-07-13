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

Typed `external_absolute` and `project_relative` screenshot records are bridged
to deterministic `unresolved_no_resolver` figures. Their private locator is
withheld from the report figure, and the figure retains metadata and a warning
instead of claiming a successful native resolution.

“Relink selected screenshot…” performs selected-file and suffix checks, discloses the exact path-kind outcome, obtains explicit confirmation, revalidates the file and stale target, and then replaces one in-memory Project screenshot record. A typed `external_absolute` record remains `external_absolute`; a typed `project_relative` record becomes `external_absolute`. Relink copies or moves no image and is not typed native resolution: without an authorized resolver, the report bridge still emits `unresolved_no_resolver`, the runtime descriptor has no `effective_path`, no usable report `image_path` is produced, and the placeholder remains. Saving the Project is separate and explicit. Legacy or unmarked compatibility behavior may perform filesystem checks and is not certified provider-silent.

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
- Do not turn typed lexical candidates or unresolved placeholders into native
  existence, readability, locality, containment, link-safety, provider-silence,
  sandboxing, or race-free claims.
- Keep report outputs under `artifacts/report` or test temp directories unless
  explicitly exported elsewhere by the user.

## Known Limitations

- Heavy PDF export is deferred.
- Reports summarize imported/previewed data; they do not prove physical
  validity.
- Missing optional dependencies are surfaced as diagnostics where available.
- Solver adapter sections remain descriptive until bounded solver adapters are
  implemented.
- **Native report-asset availability resolution is unsupported (`DEFERRED_RETAINED`).** Without an authorized resolver, the manager and report bridge continue to represent typed `external_absolute` and `project_relative` references as `unresolved_no_resolver` placeholders. “Relink selected screenshot…” performs point-in-time selected-file and suffix checks and, only after explicit confirmation plus post-confirmation file and stale-target revalidation, replaces one in-memory Project screenshot record: `external_absolute` remains `external_absolute`, while `project_relative` becomes `external_absolute`. Relink does not perform typed native resolution; the runtime descriptor still has no `effective_path`, the report bridge supplies no usable `image_path`, and the placeholder remains. Saving the Project is separate and explicit. These compatibility checks add no durable claim of existence, readability, locality, containment, link safety, provider silence, sandboxing, race-free consumption, authenticity, malware safety, or production readiness, and make no negative finding about the target. Legacy or unmarked compatibility behavior is separate, may perform filesystem checks, and is not certified provider-silent.

See [Report Asset Runtime Path Native
Deferral](experimental/report_asset_runtime_path_native_deferral.md) for the
canonical status and reopening criteria.

## Next Step

Next functional step: `OSW-FUNC-012_GMSH_ADAPTER`.
