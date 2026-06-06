# Validation Matrix

OSW v0.1 validation evidence is educational and research oriented. The matrix
records deterministic checks, formulas, tolerances, and optional dependency
conditions for the demo path:

```text
Import -> Configure -> Run or prepare -> Result -> Report
```

This matrix is not an industrial certification plan and is not a substitute for
expert engineering judgment. External solver and optional dependency cases may be
documented, fixture-backed, or skipped locally when the dependency is not
installed.

## Case Status Legend

| Status | Meaning |
| --- | --- |
| `automated` | Covered by local tests that run without external solver binaries. |
| `optional` | Runs only when an optional dependency or external executable is installed; otherwise skipped or reported as missing. |
| `documented` | Covered by tutorial, smoke checklist, or report evidence, not a mandatory executable fixture. |
| `planned` | Identified validation target without complete v0.1 evidence. |

## v0.1 Cases

| Case ID | Demo Mapping | Domain | Solver | Input | Expected result | Tolerance / pass criterion | Source / formula | Status | Last run |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VAL-CAE-001 | Demo 04, CalculiX cantilever | CAE linear static | CalculiX adapter result fixture; no mandatory `ccx` run | Cantilever beam parameters: force `F`, length `L`, Young's modulus `E`, second moment of area `I`, and parsed `.dat` displacement summary | Maximum tip displacement agrees with Euler-Bernoulli beam estimate | Relative error `<= 5%`; corrupt or partial result produces a warning instead of silent pass | `delta = F L^3 / (3 E I)`; `tests/validation/test_calculix_cantilever.py` | automated | 2026-05-28 via OSW-FUNC-015 parser QA |
| VAL-CAE-002 | Demo 04, CalculiX deck writer | CAE linear static | CalculiX input deck generator; no `ccx` run | One-element cantilever MeshModel, Steel isotropic elastic material, fixed node set, and nodal force set | Deterministic `.inp` includes heading, nodes, C3D8 element, material, elastic data, fixed boundary, nodal force, and static step | Golden `.inp` text matches exactly after normalization | `tests/golden/calculix/cantilever_linear_static.inp`; `tests/unit/test_calculix_input_deck.py` | automated | 2026-05-28 via OSW-FUNC-013 QA |
| VAL-CFD-001 | Demo 05, OpenFOAM cavity and duct templates | CFD incompressible template | OpenFOAM template adapter; no mandatory real OpenFOAM run | Cavity and duct request fixtures with velocity inlet, pressure outlet, wall/no-slip, simple transport properties, and generated dictionary files | Deterministic case files match golden fixtures and residual parser extracts Ux/Uy/Uz/p from sample logs | Golden case text and exact final residual fixture values; real OpenFOAM execution is optional/skipped when unavailable | `tests/golden/openfoam`, `tests/unit/test_openfoam_case_generator.py`, `tests/unit/test_openfoam_residual_parser.py` | automated | 2026-05-28 via OSW-FUNC-016 QA |
| VAL-MESH-001 | Demo 02, mesh import preview | Mesh | None | Small synthetic mesh or curated mesh fixture through MeshModel/conversion path | Node count, element count, cell type distribution, bounding box, and exported artifact reference remain inspectable | Exact structural checks for counts/types; unsupported export or cell type must produce a clear error | MeshModel metadata, `tests/unit/test_mesh_quality.py`, `tests/unit/test_mesh_export.py` | automated | 2026-05-14 via `pytest tests/unit -q` |
| VAL-MSCRIPT-001 | Demo 8, MATLAB/Octave figure preview | Script and figure data | GNU Octave optional; import remains preview-first | `examples/08_mscript_figure` simple plot script and captured/fake figure image fixture | FigureDataset contains at least one FigureRecord with title/path metadata and PNG or SVG output when capture is available | Pass if preview/import does not execute automatically, dangerous commands warn, and figure capture test passes or skips with missing Octave diagnostic | FigureDataset contract, `tests/unit/test_figure_dataset.py`, `tests/integration/test_mscript_figure_capture_optional.py` | optional | 2026-05-14 via unit QA; real Octave path optional/skipped if unavailable |
| VAL-CHM-001 | Demo 7, CoolProp property | Chemistry/property | CoolProp optional | Water property point with `fluid="Water"`, `pressure_pa=101325.0`, `temperature_k=300.0`, density output, and T sweep at fixed P | Density is approximately `996.6 kg/m^3`, property/sweep tables include SI-unit metadata, ResultDataset series are generated, and missing CoolProp produces a friendly diagnostic | Numeric pass if `990.0 < D < 1000.0 kg/m^3`; sweep structure exact in fake-backend tests; optional dependency may skip numeric check when CoolProp is unavailable | CoolProp `PropsSI("D", "P", 101325 Pa, "T", 300 K, "Water")` reference point; `tests/unit/test_coolprop_adapter.py`, `tests/unit/test_coolprop_result_bridge.py`, `tests/integration/test_coolprop_optional.py` | optional | 2026-06-02 via OSW-FUNC-018 CHM QA |
| VAL-CHM-002 | Demo 6, Cantera 0D reactor | Chemistry/reactor | Cantera optional | Constant-volume `gri30.yaml` methane/air reactor with short bounded end time and tracked species | Time, temperature, pressure, and species histories convert to ResultDataset tables/series; missing Cantera or mechanism produces a friendly diagnostic | Fake-backend time history structure exact; optional real Cantera test passes if time history is non-empty | Cantera `IdealGasReactor` bounded 0D example; `tests/unit/test_cantera_adapter.py`, `tests/unit/test_cantera_result_bridge.py`, `tests/integration/test_cantera_optional.py` | optional | 2026-06-02 via OSW-FUNC-018 CHM QA |
| VAL-REPORT-001 | Report step for all demos | Report/post | None | Minimal project summary with unit system, materials, mesh/result summaries, warnings, FigureDataset, and ResultDataset placeholders | HTML report includes required sections and handles missing or broken figure paths gracefully | Exact section-name presence for required report sections; no broken image crash | HTML report generator tests, `tests/unit/test_report_generator.py`, `tests/golden/report` | automated | 2026-05-14 via `pytest tests/unit -q` |

## Bootstrap and Guardrail Evidence

| Area | Evidence | Pass criterion | Last run |
| --- | --- | --- | --- |
| Package import | `python -m osw.cli --version` through fast QA | CLI returns version without importing heavy optional dependencies | 2026-06-02 via `python tools/qa/run_fast_qa.py` |
| CLI doctor | `python -m osw.cli doctor` through fast QA | Reports optional dependencies and states external solver execution is disabled | 2026-06-02 via `python tools/qa/run_fast_qa.py` |
| Scope drift | `python tools/qa/check_scope_drift.py` | No forbidden v0.1 scope claims in changed files | 2026-06-02 via `python tools/qa/run_release_gate.py` |
| Architecture boundaries | `python tools/qa/check_architecture_boundaries.py` | GUI/core/plugin dependency direction remains within documented boundaries | 2026-06-02 via `python tools/qa/run_release_gate.py` |
| Solver artifacts | `python tools/qa/check_no_solver_artifacts_committed.py` | No runtime solver outputs, logs, or generated reports staged or committed | 2026-06-02 via `python tools/qa/run_release_gate.py` |
| Golden fixtures | `pytest tests/golden -q` | CalculiX decks, OpenFOAM templates, mesh export summaries, report sections, and plugin health output match curated fixtures with normalized diffs | 2026-06-02 |
| Release checklist gate | `python tools/qa/run_release_gate.py`; split unit/gui/integration/golden/validation suites; CLI smoke matrix | Release readiness checklist records PASS/SKIP/P1/P2 status, with no P0 scope or safety blocker | 2026-06-02 |
| Broad pytest command | Split suite commands including tracked GUI with duplicate-file ignore | Unit, integration, golden, validation, and tracked GUI suites pass; untracked desktop duplicate `* (1).py` files remain a local hygiene warning | 2026-06-02 |
| Packaging docs | `python tools/qa/check_docs_links.py`; `pytest tests/unit/test_cli_surface.py -q`; CLI quickstart smoke | README, install docs, optional dependency matrix, and release-candidate docs link current v0.1 source-install and diagnostic workflows | 2026-06-02 |

## v0.1.3rc2 Maintenance Validation

The `v0.1.3rc2` line is maintenance and revalidation only. It should not expand
features unless a critical public-prerelease blocker is identified and scoped in
a separate gate.

| Area | Evidence target | Pass criterion | Status |
| --- | --- | --- | --- |
| Duplicate hygiene | `OSW-MAINT-002_POST_PUBLIC_RELEASE_DUPLICATE_FILE_HYGIENE` evidence and `tools/qa/check_release_gate.py` | No untracked duplicate ` (1)` warning returns. | completed |
| Release asset smoke | `tools/release/check_release_assets.py`, downloaded assets, `SHA256SUMS.txt`, manifest, wheel install, sdist install, and portable ZIP `--help` evidence | Checksums match, manifest matches, archives are safe to inspect/extract, and optional full smoke commands pass on a local machine. | automated for `v0.1.3-rc1`; reusable for `v0.1.3rc2` |
| Release asset smoke CI | `.github/workflows/release-asset-smoke.yml`, `tests/fixtures/release_assets`, and `tools/qa/check_release_asset_smoke.py` | PR and `develop` push checks use offline fixtures only; live GitHub release downloads are manual `workflow_dispatch` only with read-only permissions. | automated offline; manual live download |
| Portable ZIP UX | Current portable ZIP inspection, [Windows Portable ZIP](release/windows_portable_zip.md), and `README_RUN_FIRST.txt` template checks | Docs clearly say unsigned, no MSI, no code signing, no bundled external solvers, prerelease, and checksum verification. Tooling reports portable UX warnings for future builds. | automated warnings added for `v0.1.3rc2` maintenance |
| Maintenance baseline revalidation | [v0.1.3rc2 maintenance revalidation](maintenance/v0_1_3rc2_revalidation.md), release tag checks, GitHub Release asset checks, local smoke, unit, GUI, Ruff, and QA guardrails | Current `develop` remains scoped to maintenance, active version is `0.1.3rc2.dev0`, `v0.1.3-rc1` remains intact, and workflow/release asset checks stay non-mutating. | revalidated for maintenance |
| Post-public release checklist | [Post-Public Release Checklist](release/post_public_release_checklist.md), release checklist, release summary, and issue #3 evidence | Checklist records metadata/tag gates, draft/publish gates, asset build/upload, asset smoke, post-public audit, docs polish, branch reconciliation, maintenance follow-up, CI/manual smoke, issue triage, safety checks, never-do rules, and limitations. | completed for issue `#3` |
| Onboarding examples and tutorials | [Tutorials](tutorials/README.md), [First CLI Walkthrough](tutorials/first_cli_walkthrough.md), [Result Dataset Walkthrough](tutorials/result_dataset_walkthrough.md), [Examples](examples.md), and public docs QA | New users can run zero-dependency CLI smoke, inspect fixtures, understand GUI prerequisites, and see optional backend diagnostics without external solver execution. | completed for issue `#13` |
| Code signing and installer strategy | [Code Signing And Installer Strategy](release/code_signing_installer_strategy.md), Windows portable ZIP docs, release asset smoke docs, and release trust docs tests | Docs distinguish checksums/manifest, artifact attestation, Authenticode signing, MSI/MSIX/Store packaging, and preserve current no signing/no MSI/no bundled solver claims. | completed for issue `#16` |
| v0.1.4 feature selection planning | [v0.1.4 feature selection planning](roadmap/v0_1_4_feature_selection.md), roadmap docs, and issue #12 evidence | Feature-line planning selects Plugin Manager UX/install receipts as the first implementation candidate, ResultViewer / FieldViewer workflow as the second candidate, VFEA as planning-only, and live validation as environment-blocked. | completed for issue `#12` |
| v0.1.4 scope lock | [v0.1.4 scope lock](roadmap/v0_1_4_scope_lock.md), roadmap docs, and issues `#12`/`#15` evidence | Scope is locked to Plugin Manager UX/install receipts, with remote plugin store, dependency auto-install, plugin signing, marketplace behavior, plugin code execution during install, and GUI solver execution out of scope. | scope locked for issue `#15` |
| Plugin Manager UX receipts | [Plugin Install Hardening](33_plugin_install_hardening.md), [First GUI Walkthrough](tutorials/first_gui_walkthrough.md), Plugin Manager GUI tests, and plugin install receipt/quarantine unit tests | Managed install receipts, quarantine/rejection records, diagnostics, and managed-root uninstall eligibility are visible in the GUI and remain consistent with CLI records. No remote store, dependency auto-install, plugin signing, marketplace behavior, or plugin code execution during install is added. | implemented for issue `#15` |
| v0.1.4 planning issue closure | [v0.1.4 planning issue closure evidence](maintenance/v0_1_4_planning_issue_closure.md), roadmap docs, and issues `#12`/`#15` evidence | Closure evidence confirms feature selection, scope lock, first implementation slice, and first implementation closure are present before Issue `#12` is closed. | closure gate for issue `#12` |
| Result/Field viewer workflow | ResultViewer and FieldViewer GUI tests, result/field view-model tests, CLI result/field inspect help, [Result Dataset Walkthrough](tutorials/result_dataset_walkthrough.md), and [closure evidence](maintenance/v0_1_4_result_field_viewer_closure.md) | Catalog summary, dataset details, plot/table/field/report handoff labels, field artifact summaries, diagnostics, PyVista optional/fallback state, and summary-first limitations render without executing solvers or scripts. | completed for issue `#14` |
| v0.1.4 remaining scope review | [v0.1.4 remaining scope review](roadmap/v0_1_4_remaining_scope_review.md), issue `#17`, and open live validation issues `#6`-`#11` | Remaining scope selects VFEA scope definition as planning-only and keeps live optional validation environment-dependent. It does not implement VFEA, run live solver validation, or claim `v0.1.4` is released. | completed planning review |
| VFEA experimental scope | [VFEA experimental scope definition](roadmap/vfea_experimental_scope.md), issue `#17`, and `tests/unit/test_vfea_scope_docs.py` | VFEA is documented as planning-only and experimental, with FEASpec candidate/validator/human-review/benchmark requirements, CalculiX-first planning, no automatic unreviewed solver execution, no mandatory Abaqus, no topology optimization implementation, and no certification claim. | scope defined for issue `#17` |
| Public release wording | GitHub Release notes body audit | Notes say public prerelease, assets attached, unsigned portable ZIP, no MSI, no code signing, and no bundled solvers. | completed for `v0.1.3-rc1` |
| Roadmap triage | GitHub issues and milestones | Maintenance tasks are assigned or deferred before feature work starts. | planned |

## Live Optional Validation Placeholder

Live optional validation is environment-specific and should be recorded under
[Live optional validation](roadmap/live_optional_validation.md). Current local
evidence is summarized in
[Live Optional Solver Environment Validation](validation/live_optional_solver_validation.md).
It may include Gmsh, GNU Octave, CalculiX `ccx`, OpenFOAM, CoolProp, Cantera,
SciPy MAT support, PyVista, and meshio when those tools are already installed
locally. Generated evidence belongs under `artifacts/validation/` and must not
be committed as runtime output.

This evidence is useful for confidence and diagnostics, but it is not an
industrial certification claim and does not make optional dependencies mandatory
for base import, CLI smoke, or unit tests.

## Limitations

- The matrix records validation evidence for v0.1 demos; it does not certify
  OSW for production CAE, CFD, chemistry, or safety-critical decisions.
- External solver cases are bounded. CalculiX validation is fixture/formula
  backed unless a local optional `ccx` path is available and explicitly used
  outside default unit tests.
- OpenFOAM coverage remains template and tutorial oriented in v0.1. It is not a
  full OpenFOAM solver UI or broad CFD validation campaign.
- CoolProp, Cantera, Gmsh, PyVista, meshio, Octave, and solver executables are
  optional. Missing dependencies must produce clear diagnostics or skips, not
  hidden success.
- MATLAB/Octave `.m` workflows are preview-first. Import must not auto-run
  arbitrary scripts; execution remains explicit and user-triggered.
- CAD validation is limited to standard/exported formats such as STEP, STL, OBJ,
  and mesh formats. Native commercial CAD direct import is not supported.

## Future Expansion

Post-v0.1 validation can add more reference cases only when they remain
reproducible without commercial software and avoid certification claims. Useful
future rows include OpenFOAM cavity/duct residual trend fixtures, Cantera reactor
reference trajectories, richer mesh-quality fixtures, and report diff snapshots.
