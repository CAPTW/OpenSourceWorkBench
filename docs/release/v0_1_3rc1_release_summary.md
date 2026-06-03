# v0.1.3rc1 Release Summary Handoff

This page records the final local handoff for the OpenSolver Workbench
`0.1.3rc1` internal release candidate. The annotated `v0.1.3-rc1` tag was
pushed to `origin` as a tag-only push. No GitHub Release, binary installer,
package publication, branch push, all-tags push, force push, or release asset
upload was created by the release gates.

## Release Status

| Item | Status |
| --- | --- |
| Package metadata | `0.1.3rc1` |
| Tag name | `v0.1.3-rc1` |
| Tag pushed | yes |
| GitHub Release created | no |
| Binary installer created | no |
| Release assets uploaded | no |

## Tag Details

| Item | Value |
| --- | --- |
| Annotated tag | yes |
| Local tag target | `a6e8d3a8211e02359841d10e1947e16ab847b132` |
| Remote peeled target | `a6e8d3a8211e02359841d10e1947e16ab847b132` |
| Remote tag object | `0502ae26b2013fcb8ce708d21a03d55f9dd7ed04` |

Important commit distinction:

- Tagged release commit: `a6e8d3a8211e02359841d10e1947e16ab847b132`.
- Latest local post-push docs/status commit at handoff:
  `0491fab783202ebbad4e827f8df383f4cbae693f`.
- The post-push docs/status commit is not included in `v0.1.3-rc1`.
- Do not move, delete, retarget, or recreate `v0.1.3-rc1`.

## Push Audit

| Item | Result |
| --- | --- |
| Tag-only push | yes |
| Branch push | no |
| All-tags push | no |
| Force push | no |
| GitHub Release creation | no |

## Feature Readiness Summary

- GUI baseline: PySide6 shell, project tree, properties, viewer panels, report
  preview, and status surfaces are present for v0.1 preview workflows.
- ProjectSchema: project, unit, material, script, result, figure, curve, and
  report contracts are available as inspectable typed data.
- Plugin contract/health/install hardening: manifest-first discovery, local
  folder/ZIP install validation, receipts, rejection/quarantine metadata, and
  CLI/GUI health diagnostics are included.
- Runner/diagnostics: external execution remains a backend/service concern with
  explicit diagnostics and preview-first boundaries.
- Mesh/Gmsh: standard mesh metadata, optional meshio bridge, Gmsh primitive
  `.geo` generation, and explicit optional mesh generation paths are present.
- M-Script/Octave/FigureDataset/MAT: MATLAB/Octave `.m` preview and scanning,
  optional Octave execution, FigureDataset normalization, and MAT inspection
  workflows are present.
- BoundaryCurve: CSV/MAT import, inspection, and export workflows are present.
- Report: deterministic HTML report generation and report-summary workflows are
  present without requiring solver execution.
- CalculiX: input deck preview/write, validation, optional runner binding, and
  fixture-backed parser/validation summaries are present.
- OpenFOAM: bounded cavity/duct templates and residual-log summaries are
  present without claiming full OpenFOAM coverage.
- CHM: CoolProp and Cantera optional adapters and result inspection workflows
  are present.
- ResultViewer: result dataset, catalog, table, figure, and summary inspection
  surfaces are present.
- FieldViewer: field-capable dataset metadata and optional field rendering
  surfaces are present.

## Optional Dependency Diagnostics

- PySide6 was available locally for GUI-focused release checks.
- PyVista, meshio, Gmsh, Octave, SciPy/hdf5storage/h5py, CoolProp, Cantera,
  CalculiX `ccx`, OpenFOAM, and PyYAML remain optional or
  environment-dependent. Missing optional stacks should produce diagnostics and
  must not block base import, CLI smoke, or lightweight unit tests.
- No live solver/science backend evidence is claimed for machines where those
  optional stacks are missing.

## Known Limitations

- OSW v0.1 is an educational and research prototype, not an industrial-certified
  CAE product.
- No native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import
  is claimed.
- No Simulink, `.slx`, or `.mlapp` compatibility is claimed.
- No full OpenFOAM GUI/editor or full OpenFOAM solver coverage is claimed.
- Full CalculiX FRD field parsing is deferred.
- Full OpenFOAM field parsing is deferred.
- Process flowsheet/DWSIM workflows are out of v0.1 scope.
- Plugin signing, a remote plugin store, and dependency auto-install are not
  present.
- No binary installer or GitHub Release assets exist for this handoff.

## SSH Caveat

Default Git-for-Windows SSH may still fail authentication in this checkout. The
successful remote verification and tag-only push used the process-local Windows
OpenSSH override:

```powershell
$env:GIT_SSH = "C:\Windows\System32\OpenSSH\ssh.exe"
```

Use a separate explicit gate before changing Git configuration, changing the
remote URL, or pushing branches.

## Recommended Next Actions

1. Decide whether to push the local post-push docs/status commit
   `0491fab783202ebbad4e827f8df383f4cbae693f` to `develop` in a separate
   branch-push policy gate.
2. Optionally create a GitHub Release draft in a separate explicit release
   creation gate.
3. Optionally configure Git to use Windows OpenSSH permanently in a separate
   configuration gate.
4. Optionally run live dependency and solver validation on a machine with the
   optional stacks installed.
