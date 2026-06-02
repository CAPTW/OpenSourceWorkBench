# v0.1 Freeze Handoff

This document freezes OpenSolver Workbench v0.1 as an internal release
candidate. It is a local handoff package, not a public release announcement,
not a tag push, not a binary installer, and not a package publication.

## Freeze Status

| Item | Status |
| --- | --- |
| Release state | v0.1 internal release candidate |
| Freeze result | passed-with-warnings |
| Public tag | not created in this handoff step |
| Push | not pushed |
| Binary/package publication | not produced |
| Current package metadata | `0.1.2` |

The remaining warnings are local-environment and release-line items: optional
live solver/dependency stacks may be missing, `.codex/reports/*` and
`artifacts/*` are untracked by policy, historical tags through `v0.1.2` must not
be moved, and current `develop` is ahead of local `v0.1.2` tag evidence.
Duplicate desktop `* (1)` files were quarantined during post-freeze hygiene.

## Latest Commits

| Commit | Purpose |
| --- | --- |
| `c26bf0e` | Added optional field rendering viewer metadata path. |
| `893a375` | Recorded v0.1 validation gate outputs. |
| `d646857` | Added v0.1 packaging and install guide. |
| `c2bbee7` | Hardened local plugin install flow. |
| Handoff commit | The commit containing this document; final run output records the exact hash. |

## Completed Feature Matrix

| Area | v0.1 readiness |
| --- | --- |
| GUI visual baseline | Frozen PySide6 shell with dark/light/system themes and visual QA capture. |
| ProjectSchema | Core schema, units, materials, project IO, GUI binding, and validation. |
| Plugin contract/discovery/health | Manifest-first discovery and health diagnostics without plugin code execution. |
| Plugin install hardening | Local folder/ZIP install, safe archive checks, receipts, rejection records, managed uninstall, GUI/CLI integration. |
| Runner/diagnostics | Backend runner boundary with timeout/log/artifact diagnostics; GUI does not call subprocess directly. |
| Mesh import bridge | Standard/exported mesh metadata and optional meshio conversion paths. |
| Gmsh adapter | Bounded primitive `.geo` generation and optional explicit backend runner path. |
| M-Script preview | Preview-first `.m` parsing, safety scan, plot hints, and ProjectSchema script refs. |
| Octave runner | Explicit, safety-gated backend runner path with missing executable diagnostics. |
| FigureDataset | PNG/SVG/PDF/CSV/workspace artifact normalization for existing artifacts. |
| MAT reader | Optional SciPy/HDF5-backed MAT preview and CSV export diagnostics. |
| BoundaryCurve | CSV/MAT/workspace curve import, export, validation, and GUI preview. |
| Report generator | Deterministic HTML report summary/export from existing data. |
| CalculiX | Input deck generation, explicit runner binding, result parser, and validation metric. |
| OpenFOAM | Cavity/duct template generation, explicit runner binding, residual parser. |
| CHM CoolProp/Cantera | Optional property/reactor adapters with ResultDataset handoff and missing dependency diagnostics. |
| ResultViewer / PlotViewer / TableViewer | Unified scalar, series, table, figure, artifact, and diagnostic surfaces. |
| FieldViewer | Field metadata panel and optional guarded PyVista scalar rendering path. |

## Demo Readiness

| Demo path | Readiness |
| --- | --- |
| ProjectSchema demo | `project-demo-json`, `project-validate`, GUI project tree/properties/report bindings. |
| Plugin manager/health | Manifest table, health diagnostics, enable/disable state, install receipt/quarantine views. |
| Mesh bridge | Mesh format listing and metadata bridge; optional meshio reports dependency diagnostics. |
| Gmsh `.geo` generation | Deterministic box/primitive `.geo` generation; missing Gmsh check is friendly. |
| M-Script preview/safety scan | Safe preview of `.m` fixtures and dangerous-token diagnostics without auto-running code. |
| Octave missing diagnostic / fake paths | `octave-check` and explicit runner paths report availability; execution is opt-in. |
| FigureDataset artifact normalization | Existing figure artifacts can be inspected and normalized into FigureDataset metadata. |
| MAT reader optional diagnostics | MAT summary works when optional readers support the fixture; otherwise diagnostics are explicit. |
| BoundaryCurve CSV import/export | CSV curves convert to JSON and can be inspected without solver generation. |
| Report export | Project-backed HTML report export and report summary are deterministic. |
| CalculiX deck/parser validation | Cantilever deck generation, parser fixtures, result summaries, and validation tests. |
| OpenFOAM case/residual parsing | Template case generation and residual log parser fixtures. |
| CHM missing dependency diagnostics | CoolProp/Cantera checks and dialogs report missing optional packages clearly. |
| ResultViewer/FieldViewer | ResultDataset, ResultCatalog, and field metadata fixture inspection. |

## Optional Dependency Status

| Dependency/tool | v0.1 policy |
| --- | --- |
| PySide6 | Optional GUI extra; available locally when GUI tests/screenshots pass, otherwise skipped with diagnostics. |
| PyVista | Optional field rendering dependency; missing dependency returns diagnostics. |
| meshio | Optional mesh conversion dependency; base mesh contracts remain import-safe. |
| Gmsh | Optional executable/Python stack; `.geo` generation does not require it. |
| GNU Octave | Optional executable for explicit reviewed `.m` runs only. |
| SciPy/hdf5storage/h5py | Optional MAT reader helpers; JSON/preview paths remain guarded. |
| CoolProp | Optional property package; missing package is a diagnostic, not a base failure. |
| Cantera | Optional reactor package; missing package is a diagnostic, not a base failure. |
| CalculiX `ccx` | Optional executable for explicit backend runs; deck/parser tests do not require it. |
| OpenFOAM | Optional executables for explicit backend runs; template/parser tests do not require it. |
| PyYAML | Optional YAML manifest support; JSON plugin manifests work without it. |

## Known Warnings

- Duplicate `* (1)` files were quarantined under ignored `artifacts/hygiene`
  during post-freeze hygiene and must not be staged.
- `.codex/reports/*` reports are runtime evidence and remain untracked by
  policy.
- `artifacts/*` outputs are runtime evidence and remain git-ignored by policy.
- Optional live solvers/dependencies may be unavailable locally.
- A stale duplicate editable `.pth` in the local venv was repaired during
  release-line reconciliation; validation should import OSW from this checkout.
- Local `v0.1.2` exists as historical tag evidence and points to
  `c39f21372ef837f096aa0d430cced82adc6f3485`, while current `develop` is ahead
  at `f42131845bee49a89ef40a8d21c0c146846ada25`.

## Known Limitations

- Educational/research prototype only; not industrial certification.
- No native commercial CAD direct import.
- No Simulink, `.slx`, or `.mlapp` compatibility.
- No full OpenFOAM GUI/editor or broad solver coverage.
- No full CalculiX FRD parser.
- No full OpenFOAM field parser.
- No process flowsheet simulator or DWSIM bridge.
- No vector glyphs, streamlines, or time animation in v0.1 field rendering.
- No PDF report export.
- No plugin signing, remote plugin store/catalog, or dependency auto-install.

## Handoff Instructions

Install base source checkout:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m osw.cli doctor
```

Install GUI/development extras when needed:

```powershell
python -m pip install -e ".[gui,dev]"
python -m osw.cli gui
```

Run concise CLI smoke:

```powershell
python -m osw.cli --help
python -m osw.cli project-demo-json --out artifacts\release\freeze_demo_project.json
python -m osw.cli project-validate artifacts\release\freeze_demo_project.json
python -m osw.cli plugins-health
python -m osw.cli report-export artifacts\release\freeze_demo_project.json --out artifacts\release\freeze_report.html
```

Primary docs:

- [Release notes](v0_1_release_notes.md)
- [Handoff manifest](v0_1_handoff_manifest.md)
- [Release candidate](v0_1_release_candidate.md)
- [Known limitations](known_limitations_v0_1.md)
- [Release checklist](../10_release_checklist.md)
- [Validation matrix](../04_validation_matrix.md)
- [Packaging and release docs](../32_packaging_release_docs.md)
- [Plugin install hardening](../33_plugin_install_hardening.md)

Do not stage generated `artifacts/*`, `.codex/reports/*`, root `GUI.png`, or
duplicate `* (1)` files. Manual cleanup of duplicate files should happen in a
separate hygiene step after the release freeze is recorded.

## Recommended Next Actions

1. Manual hygiene cleanup of duplicate `* (1)` files in a separate task.
2. Optional public release tag prep after maintainer approval.
3. Optional plugin signing/trust policy design.
4. Optional binary packaging experiment.
5. Optional post-release cleanup and dependency-specific smoke on machines with
   Gmsh, `ccx`, OpenFOAM, Octave, CoolProp, Cantera, meshio, PyVista, and MAT
   reader stacks installed.
