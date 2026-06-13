# FEASpec CalculiX INP golden fixtures

Status: no-run golden text fixtures. These fixtures are not solver outputs,
not validation results, and not evidence of engineering correctness.

## Release Context

`v0.1.4-rc1` is a public prerelease. Development continues on `develop` after
that release tag. This fixture gate does not edit the release, upload assets,
move tags, close issues, install solvers, or run live optional validation.

## Fixture Directory

The FEASpec CalculiX renderer golden fixtures live under:

```text
tests/fixtures/feaspec/calculix_golden/
```

Tracked FEASpec `.inp` files for this gate are limited to that directory.

## Fixtures

- `cantilever_minimal.inp`
- `truss_minimal.inp`

The directory also contains:

- `README.md`
- `manifest.json`

The manifest records the source case, expected rendered sections, SHA-256
digest, no-run status, and limitations for each fixture.

## Purpose

The fixtures lock deterministic renderer output for small synthetic
writer-ready case plans. Tests compare normalized text so line endings are
stable across platforms while preserving meaningful CalculiX input-card
content.

This gate verifies renderer regression behavior only. It does not prove that a
deck solves, that the model is physically correct, or that CalculiX is
installed.

The follow-up [FEASpec CalculiX no-run exporter](feaspec_calculix_exporter_no_run.md)
uses renderer output to create a caller-directory bundle with manifest,
diagnostics, and README files. That bundle is still no-run evidence and does
not validate issue `#8`.

## Safety Boundary

The golden fixture tests are no-run:

- no `ccx`;
- no SolverAdapter;
- no runner;
- no subprocess;
- no live validation;
- no ProjectSchema mutation;
- no VLM provider or credential use.

The fixtures are static text under `tests/fixtures/feaspec/calculix_golden/`.
They are not generated solver output files and do not include `.frd`, `.dat`,
`.sta`, `.cvg`, `.12d`, `.out`, `.err`, or solver logs.

## Relationship To Issue #8

Issue `#8` is live CalculiX `ccx` validation and remains separate. These
golden fixtures do not validate a local `ccx` executable, do not run
CalculiX, and do not close issue `#8`.

## Limitations

- No engineering correctness claim.
- No industrial certification, compliance, production CAE, or accuracy claim.
- No bundled solver.
- No live optional validation.
- Educational/test fixture only.

## Next Implementation Slices

- `OSW-EXP-014_FEASPEC_CALCULIX_EXPORTER_NO_RUN`
- `OSW-EXP-015_FEASPEC_CALCULIX_EXPORTER_CLI_PREVIEW`
- `OSW-EXP-016_FEASPEC_CALCULIX_RUN_GATE_INSTALLED_ONLY`
