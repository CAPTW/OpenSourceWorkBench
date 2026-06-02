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
